"""
MCP Server Runtime
Contains core runtime logic for MCP Server, called by generated server scripts.
"""

import asyncio
import json
import importlib
import uuid
import sys
import logging
import contextlib
import argparse
from typing import Any, Dict, Optional, AsyncIterator, List
from pathlib import Path
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import StreamableHTTP support
try:
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.middleware.cors import CORSMiddleware
    from starlette.types import Receive, Scope, Send
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    # Fallback for type hints if dependencies are missing
    class StreamableHTTPSessionManager: pass
    class Starlette: pass
    class Receive: pass
    class Scope: pass
    class Send: pass

# Import intelligent serialization engine
try:
    from allbemcp.serialization.engine import SmartSerializer, SerializationConfig
    SERIALIZATION_ENGINE_AVAILABLE = True
except ImportError:
    SERIALIZATION_ENGINE_AVAILABLE = False
    class SmartSerializer: pass
    class SerializationConfig: pass


class MCPServer:
    """Generic MCP Server Base Class"""
    
    def __init__(self, title: str, tools: List[Dict], function_map: Dict, library_name: str):
        self.title = title
        self.tools = tools
        self.function_map = function_map
        self.library_name = library_name
        
        self.server = Server(title.lower().replace(" ", "-"))
        
        # Cache
        self._func_cache = {}
        self._object_store = {}
        self._object_methods = {}
        
        # Initialize intelligent serializer
        if SERIALIZATION_ENGINE_AVAILABLE:
            # Try to load configuration file
            config_file = Path(f"{library_name}_serialization_config.json")
            if config_file.exists():
                config = SerializationConfig.from_file(str(config_file))
                logger.info(f"[INFO] Loaded serialization config from {config_file}")
            else:
                config = SerializationConfig()
            
            self.serializer = SmartSerializer(config)
            logger.info(f"[INFO] Serialization engine initialized")
        else:
            self.serializer = None
            logger.warning("[WARN] Serialization engine not available, using fallback")
        
        self._preload_functions()
        self._setup_handlers()
    
    def _preload_functions(self):
        """Preload all functions into cache"""
        for tool_name in self.function_map.keys():
            if tool_name == "call-object-method":
                continue
            try:
                self._get_function(tool_name)
            except Exception as e:
                logger.warning(f"Failed to preload {tool_name}: {e}")
  
    def _setup_handlers(self):
        """Setup MCP handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"]
                )
                for tool in self.tools
            ]
        
        @self.server.list_resources()
        async def list_resources() -> list[types.Resource]:
            if not self.serializer:
                return []
            
            resources = []
            for resource_id, resource_data in self.serializer.resource_store.items():
                uri = f"mcp://resources/{resource_id}"
                content_type = resource_data.get('content_type', 'application/octet-stream')
                resources.append(types.Resource(uri=uri, name=resource_id, mimeType=content_type))
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            if not self.serializer:
                raise ValueError("Serializer not available")
            
            if not uri.startswith("mcp://resources/"):
                raise ValueError(f"Invalid resource URI: {uri}")
            
            resource_id = uri.replace("mcp://resources/", "")
            resource_data = self.serializer.get_resource(resource_id)
            
            if not resource_data:
                raise ValueError(f"Resource not found: {resource_id}")
            
            content = resource_data.get('content', b'')
            if isinstance(content, bytes):
                import base64
                return base64.b64encode(content).decode('ascii')
            return str(content)
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            try:
                result = await self._execute_tool(name, arguments)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, ensure_ascii=False)
                )]
    
    async def _execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute tool call"""
        if tool_name == "call-object-method":
            return await self._call_stored_method(arguments)

        if tool_name not in self.function_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        meta = self.function_map[tool_name]
        func = self._get_function(tool_name)
        
        # Filter out empty string arguments - convert to None or remove
        # This is necessary because some libraries (e.g., requests) don't accept empty strings
        # for optional parameters like files, headers, cookies, etc.
        filtered_arguments = {}
        for key, value in arguments.items():
            if value == "" or value is None:
                # Skip empty strings and None values for optional parameters
                continue
            filtered_arguments[key] = value
        
        # Call function
        if meta["is_async"]:
            result = await func(**filtered_arguments)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: func(**filtered_arguments))
        
        # Handle return value
        if meta["returns_object"]:
            if not self._is_json_serializable(result):
                obj_info = self._store_object(result)
                return {
                    "success": True,
                    "object_id": obj_info["object_id"],
                    "object_type": obj_info["object_type"],
                    "available_methods": obj_info["available_methods"],
                    "note": "Object stored. Use call-object-method tool to invoke methods."
                }
        
        serialized = self._serialize_result(result)
        return {"success": True, "data": serialized}

    async def _call_stored_method(self, arguments: dict) -> dict:
        """Call method on stored object"""
        object_id = arguments.get("object_id")
        method_name = arguments.get("method")
        args = arguments.get("args", [])
        kwargs = arguments.get("kwargs", {})
        
        if object_id not in self._object_store:
            raise ValueError(f"Object {object_id} not found")
        
        if not isinstance(method_name, str) or not method_name:
            raise ValueError("Method name must be a non-empty string")
        if method_name.startswith('_'):
            raise ValueError("Access to private/dunder methods is not allowed")
        
        
        obj = self._object_store[object_id]
        if not hasattr(obj, method_name):
            raise ValueError(f"Method '{method_name}' not found on object")
        
        # Get attribute or method
        attr = getattr(obj, method_name)
        
        # Check if callable (method or property?)
        if callable(attr):
            allowed = self._object_methods.get(object_id)
            if allowed is not None and method_name not in allowed:
                raise ValueError(f"Method '{method_name}' is not allowed on object")
            # If method, execute call
            loop = asyncio.get_running_loop()
            if asyncio.iscoroutinefunction(attr):
                result = await attr(*args, **kwargs)
            else:
                result = await loop.run_in_executor(None, lambda: attr(*args, **kwargs))
        else:
            # If property (e.g. .columns, .shape, .index), return its value directly
            result = attr
        
        try:
            serialized = self._serialize_result(result)
            if serialized is None or isinstance(serialized, (int, float, str, bool, list, dict)):
                return {"success": True, "data": serialized}
        except Exception:
            pass
        
        obj_info = self._store_object(result)
        return {
            "success": True,
            "object_id": obj_info["object_id"],
            "object_type": obj_info["object_type"],
            "available_methods": obj_info["available_methods"],
            "note": "Complex object stored. Use call-object-method to invoke more methods."
        }
    
    def _serialize_result(self, result: Any) -> Any:
        """Intelligent result serialization"""
        if self.serializer and SERIALIZATION_ENGINE_AVAILABLE:
            serialization_result = self.serializer.serialize(result)
            
            if serialization_result.type == 'object_ref':
                obj_id = serialization_result.data['object_id']
                obj = self.serializer.get_object(obj_id)
                self._object_store[obj_id] = obj
                available = serialization_result.data.get('available_methods', [])
                self._object_methods[obj_id] = {m.get("name") for m in available if isinstance(m, dict) and m.get("name")}
                return serialization_result.data
            else:
                return serialization_result.data
        else:
            return self._fallback_serialize(result)
    
    def _fallback_serialize(self, result: Any) -> Any:
        if result is None or isinstance(result, (int, float, str, bool)):
            return result
        if isinstance(result, (list, tuple)):
            return [self._fallback_serialize(item) for item in result]
        if isinstance(result, dict):
            return {k: self._fallback_serialize(v) for k, v in result.items()}
        try:
            return str(result)
        except:
            return f"<{type(result).__name__} object>"
    
    def _get_function(self, tool_name: str):
        if tool_name in self._func_cache:
            return self._func_cache[tool_name]
        
        meta = self.function_map[tool_name]
        module = importlib.import_module(meta["module"])
        
        if meta["class"]:
            cls = getattr(module, meta["class"])
            method_name = meta["function"]
            def wrapper(**kwargs):
                instance = cls()
                method = getattr(instance, method_name)
                return method(**kwargs)
            self._func_cache[tool_name] = wrapper
            return wrapper
        
        func = getattr(module, meta["function"])
        self._func_cache[tool_name] = func
        return func
    
    def _store_object(self, obj: Any) -> dict:
        object_id = f"obj_{uuid.uuid4().hex[:12]}"
        self._object_store[object_id] = obj
        
        obj_type = type(obj)
        type_name = f"{obj_type.__module__}.{obj_type.__name__}"
        
        available_methods = []
        for name in dir(obj):
            if not name.startswith('_'):
                attr = getattr(obj, name, None)
                if callable(attr):
                    try:
                        import inspect
                        sig = inspect.signature(attr)
                        params = [
                            {"name": pname, "required": param.default == inspect.Parameter.empty}
                            for pname, param in sig.parameters.items()
                            if pname not in ('self', 'cls')
                        ]
                        available_methods.append({"name": name, "params": params})
                    except:
                        available_methods.append({"name": name, "params": []})
        
        self._object_methods[object_id] = {m.get("name") for m in available_methods if m.get("name")}
        return {
            "object_id": object_id,
            "object_type": type_name,
            "available_methods": available_methods
        }
    
    def _is_json_serializable(self, obj: Any) -> bool:
        try:
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False
    
    async def run_stdio(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
    
    async def _auto_cleanup_objects(self):
        """Background task: Automatically cleanup idle objects"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                if self.serializer:
                    before = set(self.serializer.object_store.keys())
                    removed = self.serializer.cleanup_objects(max_age_seconds=1800)  # Cleanup objects unused for 30 minutes
                    if removed > 0:
                        after = set(self.serializer.object_store.keys())
                        removed_ids = before - after
                        for object_id in removed_ids:
                            self._object_store.pop(object_id, None)
                            self._object_methods.pop(object_id, None)
                        logger.info(f"Automatically cleaned up {removed} idle objects")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Object cleanup task error: {e}")

    def create_streamable_http_app(self, host: str = "127.0.0.1", port: int = 8000, stateless: bool = False):
        if not HTTP_AVAILABLE:
            raise RuntimeError("StreamableHTTP transport not available.")
        
        session_manager = StreamableHTTPSessionManager(
            app=self.server,
            event_store=None,
            json_response=False,
            stateless=stateless
        )
        
        async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
            await session_manager.handle_request(scope, receive, send)
        
        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            # Start background cleanup task
            cleanup_task = asyncio.create_task(self._auto_cleanup_objects())
            
            async with session_manager.run():
                logger.info("StreamableHTTP session manager started!")
                try:
                    yield
                finally:
                    logger.info("StreamableHTTP session manager shutting down...")
                    cleanup_task.cancel()
                    try:
                        await cleanup_task
                    except asyncio.CancelledError:
                        pass

        starlette_app = Starlette(
            debug=True,
            routes=[Mount("/mcp", app=handle_streamable_http)],
            lifespan=lifespan
        )
        
        starlette_app = CORSMiddleware(
            starlette_app,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE"],
            expose_headers=["Mcp-Session-Id"],
        )
        
        return starlette_app, host, port
        

def serve(title: str, tools: List[Dict], function_map: Dict, library_name: str):
    """Entry point for running the server"""
    parser = argparse.ArgumentParser(description=f'{title} MCP Server')
    parser.add_argument('--http', action='store_true', help='Use StreamableHTTP transport')
    parser.add_argument('--host', default='127.0.0.1', help='HTTP server host')
    parser.add_argument('--port', type=int, default=8000, help='HTTP server port')
    parser.add_argument('--stateless', action='store_true', help='Use stateless mode')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = MCPServer(title, tools, function_map, library_name)
    
    if args.http:
        if not HTTP_AVAILABLE:
            logger.error("StreamableHTTP transport not available.")
            sys.exit(1)
        
        logger.info(f"Starting StreamableHTTP server on {args.host}:{args.port}")
        app, host, port = server.create_streamable_http_app(args.host, args.port, args.stateless)
        
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    else:
        logger.info("Starting stdio server")
        asyncio.run(server.run_stdio())
