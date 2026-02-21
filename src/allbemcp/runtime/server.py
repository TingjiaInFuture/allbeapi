"""
MCP Server Runtime (FastMCP 3.x)
Contains core runtime logic for generated MCP servers.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import json
import logging
import threading
import time
import types as py_types
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, get_args, get_origin, get_type_hints

import mcp.types as types
from fastmcp import Context, FastMCP
from fastmcp.server.dependencies import transform_context_annotations
from fastmcp.tools.function_tool import FunctionTool

try:
    from allbemcp.serialization.engine import SerializationConfig, SmartSerializer

    SERIALIZATION_ENGINE_AVAILABLE = True
except ImportError:
    SERIALIZATION_ENGINE_AVAILABLE = False

    class SmartSerializer:  # type: ignore[no-redef]
        pass

    class SerializationConfig:  # type: ignore[no-redef]
        pass


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Generic MCP Server Runtime powered by FastMCP 3.x."""

    def __init__(self, title: str, tools: List[Dict], function_map: Dict, library_name: str):
        self.title = title
        self.tools = tools
        self.function_map = function_map
        self.library_name = library_name

        self.mcp = FastMCP(
            name=title.lower().replace(" ", "-"),
            instructions=(
                "High-quality Python library tools. "
                "Use object_id with call-object-method for stateful objects."
            ),
        )

        self._func_cache: Dict[str, Callable[..., Any]] = {}
        self._object_store: Dict[str, Any] = {}
        self._object_methods: Dict[str, set[str]] = {}
        self._class_instance_cache: Dict[str, Any] = {}
        self._class_instance_lock = threading.Lock()
        self._call_stats = defaultdict(lambda: {"count": 0, "total_time": 0.0, "errors": 0})
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp-tool-")

        if SERIALIZATION_ENGINE_AVAILABLE:
            config_file = Path(f"{library_name}_serialization_config.json")
            if config_file.exists():
                config = SerializationConfig.from_file(str(config_file))
                logger.info("Loaded serialization config from %s", config_file)
            else:
                config = SerializationConfig()
            self.serializer = SmartSerializer(config)
            logger.info("Serialization engine initialized")
        else:
            self.serializer = None
            logger.warning("Serialization engine not available, using fallback")

        self._preload_functions()
        self._register_tools()
        self._register_special_tools()

    def _preload_functions(self) -> None:
        for tool_name in self.function_map.keys():
            if tool_name == "call-object-method":
                continue
            try:
                self._get_function(tool_name)
            except Exception as exc:
                logger.warning("Failed to preload %s: %s", tool_name, exc)

    def _register_tools(self) -> None:
        for tool in self.tools:
            tool_name = tool.get("name")
            if not tool_name or tool_name == "call-object-method":
                continue
            if tool_name not in self.function_map:
                continue

            description = tool.get("description") or ""
            input_schema = tool.get("inputSchema") or {"type": "object", "properties": {}}

            async def wrapper(ctx: Context, _tool_name: str = tool_name, **kwargs: Any):
                try:
                    result = await self._execute_tool(_tool_name, kwargs)
                    return self._to_mcp_content(result)
                except Exception as exc:
                    logger.error("Tool execution error (%s): %s", _tool_name, exc, exc_info=True)
                    await ctx.error(str(exc))
                    return [
                        types.TextContent(
                            type="text",
                            text=json.dumps({"error": str(exc)}, ensure_ascii=False),
                        )
                    ]

            # transform_context_annotations must be called so FastMCP's DI
            # system recognises ctx: Context and injects it automatically.
            # Bypassing FunctionTool.from_function() skips this step, so
            # we call it explicitly here.
            transformed_wrapper = transform_context_annotations(wrapper)

            self.mcp.add_tool(
                FunctionTool(
                    fn=transformed_wrapper,
                    name=tool_name,
                    description=description,
                    parameters=input_schema,
                )
            )

    def _register_special_tools(self) -> None:
        @self.mcp.tool(
            name="call-object-method",
            description=(
                "Call a method on a stored object. "
                "Use this after getting an object_id from another tool."
            ),
        )
        async def call_object_method(
            ctx: Context,
            object_id: str,
            method_name: str | None = None,
            method: str | None = None,
            args: list[Any] | None = None,
            kwargs: dict[str, Any] | None = None,
        ):
            selected_method = method_name or method
            if not selected_method:
                raise ValueError("Either method_name or method must be provided")
            result = await self._call_stored_method(
                {
                    "object_id": object_id,
                    "method": selected_method,
                    "args": args or [],
                    "kwargs": kwargs or {},
                }
            )
            await ctx.info(f"Called {selected_method} on {object_id}")
            return self._to_mcp_content(result)

        @self.mcp.tool(name="list-objects", description="List currently stored stateful objects.")
        async def list_objects(_: Context):
            payload = []
            if self.serializer and SERIALIZATION_ENGINE_AVAILABLE:
                for object_id, metadata in self.serializer.metadata_store.items():
                    payload.append(
                        {
                            "object_id": object_id,
                            "object_type": metadata.object_type,
                            "created_at": metadata.created_at,
                            "preview": metadata.preview,
                            "available_methods": metadata.available_methods,
                        }
                    )
            else:
                for object_id, obj in self._object_store.items():
                    payload.append(
                        {
                            "object_id": object_id,
                            "object_type": f"{type(obj).__module__}.{type(obj).__name__}",
                            "preview": str(obj)[:200],
                        }
                    )
            return payload

        @self.mcp.tool(name="get-call-stats", description="Get per-tool runtime call statistics.")
        async def get_call_stats(_: Context):
            return self.get_call_stats()

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        start = time.perf_counter()
        stats = self._call_stats[tool_name]
        try:
            result = await self._do_execute(tool_name, arguments)
            elapsed = time.perf_counter() - start
            stats["count"] += 1
            stats["total_time"] += elapsed
            return result
        except Exception:
            stats["errors"] += 1
            raise

    async def _do_execute_tool_call(self, func: Callable[..., Any], coerced_arguments: Dict[str, Any], is_async: bool) -> Any:
        if is_async:
            return await func(**coerced_arguments)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, lambda: func(**coerced_arguments))

    async def _do_execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "call-object-method":
            return await self._call_stored_method(arguments)

        if tool_name not in self.function_map:
            raise ValueError(f"Unknown tool: {tool_name}")

        meta = self.function_map[tool_name]
        func = self._get_function(tool_name)

        filtered_arguments = {k: v for k, v in arguments.items() if v not in ("", None)}
        coerced_arguments = self._coerce_types(func, filtered_arguments)

        result = await self._do_execute_tool_call(func, coerced_arguments, bool(meta.get("is_async")))

        if meta.get("returns_object") and not self._is_json_serializable(result):
            obj_info = self._store_object(result)
            return {
                "success": True,
                "object_id": obj_info["object_id"],
                "object_type": obj_info["object_type"],
                "available_methods": obj_info["available_methods"],
                "note": "Object stored. Use call-object-method tool to invoke methods.",
            }

        serialized = self._serialize_result(result)
        return {"success": True, "data": serialized}

    def get_call_stats(self) -> Dict[str, Dict[str, float]]:
        snapshot: Dict[str, Dict[str, float]] = {}
        for tool_name, stats in self._call_stats.items():
            count = max(0, int(stats.get("count", 0)))
            total_time = float(stats.get("total_time", 0.0))
            errors = int(stats.get("errors", 0))
            snapshot[tool_name] = {
                "count": count,
                "errors": errors,
                "total_time": total_time,
                "avg_time": (total_time / count) if count > 0 else 0.0,
            }
        return snapshot

    def _coerce_types(self, func: Callable[..., Any], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce incoming kwargs based on callable type hints."""
        if not kwargs:
            return kwargs

        try:
            signature = inspect.signature(func)
        except (TypeError, ValueError):
            return kwargs

        try:
            resolved_hints = get_type_hints(func)
        except Exception:
            resolved_hints = {}

        coerced = dict(kwargs)
        for name, value in kwargs.items():
            param = signature.parameters.get(name)
            if param is None:
                continue

            annotation = resolved_hints.get(name, param.annotation)
            coerced[name] = self._coerce_value(annotation, value)

        return coerced

    def _coerce_value(self, annotation: Any, value: Any) -> Any:
        if (
            isinstance(value, str)
            and annotation not in (inspect.Parameter.empty, str)
            and self._has_stored_object(value)
        ):
            resolved_obj = self._get_stored_object(value)
            if resolved_obj is not None:
                return resolved_obj

        if annotation is inspect.Parameter.empty:
            return value

        origin = get_origin(annotation)
        if origin is None:
            if isinstance(annotation, type) and issubclass(annotation, Path) and isinstance(value, str):
                return annotation(value)
            return value

        if origin in (list, List):
            args = get_args(annotation)
            if isinstance(value, list) and args:
                return [self._coerce_value(args[0], item) for item in value]
            return value

        if origin in (dict, Dict):
            args = get_args(annotation)
            if isinstance(value, dict) and len(args) == 2:
                key_type, value_type = args
                return {
                    self._coerce_value(key_type, key): self._coerce_value(value_type, item)
                    for key, item in value.items()
                }
            return value

        if origin in (py_types.UnionType, Union):
            for candidate in get_args(annotation):
                if candidate is type(None):
                    continue
                converted = self._coerce_value(candidate, value)
                if converted is not value:
                    return converted
            return value

        return value

    async def _call_stored_method(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        object_id = arguments.get("object_id")
        method_name = arguments.get("method")
        args = arguments.get("args", [])
        kwargs = arguments.get("kwargs", {})

        if not self._has_stored_object(object_id):
            raise ValueError(f"Object {object_id} not found")

        if not isinstance(method_name, str) or not method_name:
            raise ValueError("Method name must be a non-empty string")
        if method_name.startswith("_"):
            raise ValueError("Access to private/dunder methods is not allowed")

        obj = self._get_stored_object(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")
        if not hasattr(obj, method_name):
            raise ValueError(f"Method '{method_name}' not found on object")

        attr = getattr(obj, method_name)

        if callable(attr):
            allowed = self._object_methods.get(object_id)
            if allowed is not None and method_name not in allowed:
                raise ValueError(f"Method '{method_name}' is not allowed on object")

            loop = asyncio.get_running_loop()
            if inspect.iscoroutinefunction(attr):
                result = await attr(*args, **kwargs)
            else:
                result = await loop.run_in_executor(self._executor, lambda: attr(*args, **kwargs))
        else:
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
            "note": "Complex object stored. Use call-object-method to invoke more methods.",
        }

    def _serialize_result(self, result: Any) -> Any:
        if self.serializer and SERIALIZATION_ENGINE_AVAILABLE:
            serialization_result = self.serializer.serialize(result)
            if serialization_result.type == "object_ref":
                obj_id = serialization_result.data["object_id"]
                available = serialization_result.data.get("available_methods", [])
                self._object_methods[obj_id] = {
                    m.get("name") for m in available if isinstance(m, dict) and m.get("name")
                }
            return serialization_result.data
        return self._fallback_serialize(result)

    def _fallback_serialize(self, result: Any) -> Any:
        if result is None or isinstance(result, (int, float, str, bool)):
            return result
        if isinstance(result, (list, tuple)):
            return [self._fallback_serialize(item) for item in result]
        if isinstance(result, dict):
            return {k: self._fallback_serialize(v) for k, v in result.items()}
        return str(result)

    def _to_mcp_content(self, payload: Any) -> List[types.ContentBlock]:
        if isinstance(payload, list) and payload and isinstance(
            payload[0], (types.TextContent, types.ImageContent)
        ):
            return payload

        if isinstance(payload, dict):
            content_type = payload.get("content_type")
            if "content_base64" in payload and content_type and content_type.startswith("image/"):
                return [
                    types.ImageContent(
                        type="image",
                        data=payload["content_base64"],
                        mimeType=content_type,
                    )
                ]

        text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        return [types.TextContent(type="text", text=text)]

    def _get_function(self, tool_name: str) -> Callable[..., Any]:
        if tool_name in self._func_cache:
            return self._func_cache[tool_name]

        meta = self.function_map[tool_name]
        module = importlib.import_module(meta["module"])

        if meta.get("class"):
            cls = getattr(module, meta["class"])

            if meta.get("is_constructor"):
                init_signature = inspect.signature(cls.__init__)

                def constructor_wrapper(**kwargs: Any):
                    return cls(**kwargs)

                parameters = [
                    parameter
                    for parameter_name, parameter in init_signature.parameters.items()
                    if parameter_name not in ("self", "cls")
                ]
                constructor_wrapper.__signature__ = init_signature.replace(parameters=parameters)
                constructor_wrapper.__annotations__ = dict(getattr(cls.__init__, "__annotations__", {}))
                self._func_cache[tool_name] = constructor_wrapper
                return constructor_wrapper

            method_name = meta["function"]
            method = getattr(cls, method_name)
            method_signature = inspect.signature(method)

            def wrapper(**kwargs: Any):
                instance = self._class_instance_cache.get(tool_name)
                if instance is None:
                    with self._class_instance_lock:
                        instance = self._class_instance_cache.get(tool_name)
                        if instance is None:
                            try:
                                instance = cls()
                            except Exception as exc:
                                raise RuntimeError(
                                    f"Cannot create instance of {cls.__name__}: {exc}. "
                                    "This class may require constructor arguments; use constructor tool first."
                                ) from exc
                            self._class_instance_cache[tool_name] = instance
                method = getattr(instance, method_name)
                return method(**kwargs)

            parameters = [
                parameter
                for parameter_name, parameter in method_signature.parameters.items()
                if parameter_name != "self"
            ]
            wrapper.__signature__ = method_signature.replace(parameters=parameters)
            wrapper.__annotations__ = dict(getattr(method, "__annotations__", {}))

            self._func_cache[tool_name] = wrapper
            return wrapper

        func = getattr(module, meta["function"])
        self._func_cache[tool_name] = func
        return func

    def _store_object(self, obj: Any) -> Dict[str, Any]:
        if self.serializer and SERIALIZATION_ENGINE_AVAILABLE:
            serialized = self.serializer.serialize(obj)
            if serialized.type == "object_ref":
                object_id = serialized.data["object_id"]
                available = serialized.data.get("available_methods", [])
                self._object_methods[object_id] = {
                    m.get("name") for m in available if isinstance(m, dict) and m.get("name")
                }
                return serialized.data

        object_id = f"obj_{id(obj)}"
        methods = []
        for name in dir(obj):
            if name.startswith("_"):
                continue
            attr = getattr(obj, name, None)
            if callable(attr):
                methods.append({"name": name, "params": []})

        self._object_store[object_id] = obj
        self._object_methods[object_id] = {m["name"] for m in methods}
        return {
            "object_id": object_id,
            "object_type": f"{type(obj).__module__}.{type(obj).__name__}",
            "available_methods": methods,
        }

    def _is_json_serializable(self, obj: Any) -> bool:
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return True

        if isinstance(obj, (list, tuple)):
            return all(self._is_json_serializable(item) for item in obj[:10])

        if isinstance(obj, dict):
            sample_items = list(obj.items())[:10]
            return all(isinstance(key, str) and self._is_json_serializable(value) for key, value in sample_items)

        return False

    def _get_stored_object(self, object_id: Any) -> Any:
        if not isinstance(object_id, str):
            return None
        if self.serializer and SERIALIZATION_ENGINE_AVAILABLE:
            try:
                serializer_obj = self.serializer.get_object(object_id)
                if serializer_obj is not None:
                    return serializer_obj
            except Exception:
                pass
        return self._object_store.get(object_id)

    def _has_stored_object(self, object_id: Any) -> bool:
        return self._get_stored_object(object_id) is not None

    def run(self, transport: str = "stdio", **run_kwargs: Any) -> None:
        self.mcp.run(transport=transport, **run_kwargs)


def serve(title: str, tools: List[Dict], function_map: Dict, library_name: str):
    """Entry point for generated servers."""

    parser = argparse.ArgumentParser(description=f"{title} MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="MCP transport (stdio or streamable-http)",
    )
    parser.add_argument("--http", action="store_true", help="Backward-compat alias for --transport streamable-http")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP server host")
    parser.add_argument("--port", type=int, default=8000, help="HTTP server port")
    parser.add_argument("--path", default="/mcp", help="HTTP mount path")
    parser.add_argument("--stateless", action="store_true", help="Use stateless HTTP mode")
    parser.add_argument("--log-level", default="INFO", help="Log level")

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    transport = "streamable-http" if args.http else args.transport
    server = MCPServer(title, tools, function_map, library_name)

    run_kwargs: Dict[str, Any] = {}
    if transport == "streamable-http":
        run_kwargs.update(
            {
                "host": args.host,
                "port": args.port,
                "path": args.path,
                "stateless_http": args.stateless,
            }
        )

    logger.info("Starting MCP server with transport=%s", transport)
    server.run(transport=transport, **run_kwargs)
