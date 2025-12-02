#!/usr/bin/env python3
"""
MCP Server Generator - Convert OpenAPI spec to MCP Server
Supports direct use by Claude Desktop and other MCP clients

v3.0 - StreamableHTTP Transport
- Uses StreamableHTTPSessionManager instead of SSE
- Based on best practices from examples
- Supports stateful and stateless modes
- Intelligent serialization engine
"""

import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path


def generate_mcp_server(openapi_spec: Dict[str, Any], output: str = "mcp_server.py", library_name: str = "library"):
    """Generate MCP Server from OpenAPI spec"""
    
    # Extract tool definitions
    tools = []
    function_map = {}
    
    for path, methods in openapi_spec.get("paths", {}).items():
        for method, operation in methods.items():
            op_id = operation["operationId"]
            func_meta = operation.get("x-function", {})
            
            # Skip management endpoints
            if path.startswith("/objects") or path == "/call_method":
                continue
            
            # Note: No longer skipping instance methods (those with class field)
            # For instance methods, we will automatically create class instances in the MCP server
            # So methods like requests.Session.get() can be directly exposed as tools
            
            # Build MCP tool definition
            tool_name = op_id.replace("_", "-")
            
            # Extract parameters
            input_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param in operation.get("parameters", []):
                param_name = param["name"]
                param_schema = param.get("schema", {"type": "string"})
                input_schema["properties"][param_name] = param_schema
                
                if param.get("required", False):
                    input_schema["required"].append(param_name)
            
            # Handle request body
            if "requestBody" in operation:
                body_schema = operation["requestBody"].get("content", {}).get("application/json", {}).get("schema", {})
                if "properties" in body_schema:
                    input_schema["properties"].update(body_schema["properties"])
                    if "required" in body_schema:
                        input_schema["required"].extend(body_schema["required"])
            
            # Deduplicate required array
            input_schema["required"] = list(dict.fromkeys(input_schema["required"]))
            
            # Build tool
            tool = {
                "name": tool_name,
                "description": operation.get("description") or operation.get("summary", ""),
                "inputSchema": input_schema
            }
            
            tools.append(tool)
            
            # Save function mapping
            function_map[tool_name] = {
                "module": func_meta.get("module", ""),
                "class": func_meta.get("class"),
                "function": func_meta.get("name", ""),
                "is_async": func_meta.get("is_async", False),
                "returns_object": func_meta.get("returns_object", False),
                "http_method": method,
                "http_path": path
            }
    
    # Add object method call tool to tools list
    tools.append({
        "name": "call-object-method",
        "description": "Call a method on a stored object. Use this after getting an object_id from another tool.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "object_id": {
                    "type": "string",
                    "description": "The ID of the stored object"
                },
                "method": {
                    "type": "string",
                    "description": "The name of the method to call"
                },
                "args": {
                    "type": "array",
                    "description": "Positional arguments for the method",
                    "items": {
                        "type": "object"
                    },
                    "default": []
                },
                "kwargs": {
                    "type": "object",
                    "description": "Keyword arguments for the method",
                    "additionalProperties": True,
                    "default": {}
                }
            },
            "required": ["object_id", "method"]
        }
    })
    
    function_map["call-object-method"] = {
        "module": "__builtin__",
        "class": None,
        "function": "_call_method",
        "is_async": False,
        "returns_object": False
    }
    
    # Generate MCP Server code
    server_code = f'''#!/usr/bin/env python3
"""
Auto-generated MCP Server
Based on: {openapi_spec["info"]["title"]}
"""

import sys
import os

try:
    from allbeapi.runtime.server import serve
except ImportError:
    # Fallback: try to import from local directory if allbeapi is not installed
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from server_runtime import serve
    except ImportError:
        print("Error: allbeapi package not found. Please install it with `pip install allbeapi`.")
        sys.exit(1)

# Tool definitions
TOOLS = {repr(tools)}

# Function mapping
FUNCTION_MAP = {repr(function_map)}

if __name__ == "__main__":
    serve(
        title="{openapi_spec["info"]["title"]}",
        tools=TOOLS,
        function_map=FUNCTION_MAP,
        library_name="{library_name}"
    )
'''
    
    # Write to file
    with open(output, 'w', encoding='utf-8') as f:
        f.write(server_code)
    
    # Generate documentation
    generate_readme(tools, library_name, openapi_spec)
    



def generate_requirements(library_name: str = "library"):
    """Generate requirements.txt"""
    
    # Check if library is a standard library module
    if sys.version_info >= (3, 10):
        is_stdlib = library_name in sys.stdlib_module_names
    else:
        # Fallback for older Python versions
        import distutils.sysconfig
        std_lib = distutils.sysconfig.get_python_lib(standard_lib=True)
        is_stdlib = False
        try:
            lib_path = importlib.util.find_spec(library_name).origin
            if lib_path and lib_path.startswith(std_lib):
                is_stdlib = True
        except:
            pass

    if is_stdlib:
        requirements = f"""# MCP Server Requirements for {library_name}
mcp>=1.0.0
starlette>=0.27.0
uvicorn>=0.23.0
# {library_name} is a standard library module
"""
    else:
        requirements = f"""# MCP Server Requirements for {library_name}
mcp>=1.0.0
starlette>=0.27.0
uvicorn>=0.23.0
{library_name}
"""
    
    requirements_file = f"{library_name}_mcp_requirements.txt"
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write(requirements)


def generate_readme(tools: List[Dict[str, Any]], library_name: str, openapi_spec: Dict[str, Any]):
    """Generate README.md for the MCP server"""
    
    title = openapi_spec.get("info", {}).get("title", f"{library_name} MCP Server")
    description = openapi_spec.get("info", {}).get("description", "")
    
    md = [f"# {title}\n"]
    if description:
        md.append(f"{description}\n")
        
    md.append("## Tools\n")
    
    for tool in tools:
        name = tool["name"]
        desc = tool.get("description", "")
        input_schema = tool.get("inputSchema", {})
        
        md.append(f"### {name}\n")
        if desc:
            md.append(f"{desc}\n")
            
        properties = input_schema.get("properties", {})
        required_props = input_schema.get("required", [])
        
        if properties:
            md.append("\n**Parameters:**\n")
            md.append("| Name | Type | Required | Description |")
            md.append("|------|------|----------|-------------|")
            
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get("type", "any")
                is_required = "Yes" if prop_name in required_props else "No"
                prop_desc = prop_schema.get("description", "").replace("\n", " ")
                
                md.append(f"| {prop_name} | {prop_type} | {is_required} | {prop_desc} |")
            md.append("\n")
        else:
            md.append("\n*No parameters required.*\n")
            
        md.append("---\n")
        
    readme_file = f"{library_name}_MCP_README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate MCP Server')
    parser.add_argument('-i', '--input', default=None, help='OpenAPI specification file (default: inferred from library name)')
    parser.add_argument('-o', '--output', default=None, help='Output file (default: <library_name>_mcp_server.py)')
    parser.add_argument('-l', '--library', default=None, help='Library name (used for file prefix)')
    
    args = parser.parse_args()
    
    # If input file is specified
    if args.input:
        input_file = args.input
        # Try to infer library name from input filename
        if args.library is None:
            # e.g.: pdfkit_openapi.json -> pdfkit
            import re
            match = re.match(r'(.+?)_openapi\.json$', Path(input_file).name)
            if match:
                library_name = match.group(1)
            else:
                library_name = "library"
        else:
            library_name = args.library
    else:
        # If input file is not specified, library name is required
        if args.library is None:
            sys.exit(1)
        library_name = args.library
        input_file = f"{library_name}_openapi.json"
    
    # Set default output filename
    if args.output is None:
        args.output = f"{library_name}_mcp_server.py"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            openapi_spec = json.load(f)
    except FileNotFoundError:
        sys.exit(1)
    
    generate_mcp_server(openapi_spec, args.output, library_name)
    generate_requirements(library_name)


if __name__ == "__main__":
    main()
