#!/usr/bin/env python3
"""
MCP Server Generator - 将 OpenAPI 规范转换为 MCP Server
支持 Claude Desktop 和其他 MCP 客户端直接使用

v3.0 - StreamableHTTP 传输
- 使用 StreamableHTTPSessionManager 替代 SSE
- 基于 examples 中的最佳实践
- 支持状态化和无状态模式
- 智能序列化引擎
"""

import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path


def generate_mcp_server(openapi_spec: Dict[str, Any], output: str = "mcp_server.py", library_name: str = "library"):
    """从 OpenAPI 规范生成 MCP Server"""
    
    # 提取工具定义
    tools = []
    function_map = {}
    
    for path, methods in openapi_spec.get("paths", {}).items():
        for method, operation in methods.items():
            op_id = operation["operationId"]
            func_meta = operation.get("x-function", {})
            
            # 跳过管理端点
            if path.startswith("/objects") or path == "/call_method":
                continue
            
            # 注意：不再跳过实例方法（有 class 字段的）
            # 对于实例方法，我们会在 MCP server 中自动创建类实例
            # 这样像 requests.Session.get() 这样的方法可以直接作为工具暴露
            
            # 构建 MCP 工具定义
            tool_name = op_id.replace("_", "-")
            
            # 提取参数
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
            
            # 处理 request body
            if "requestBody" in operation:
                body_schema = operation["requestBody"].get("content", {}).get("application/json", {}).get("schema", {})
                if "properties" in body_schema:
                    input_schema["properties"].update(body_schema["properties"])
                    if "required" in body_schema:
                        input_schema["required"].extend(body_schema["required"])
            
            # 去重 required 数组
            input_schema["required"] = list(dict.fromkeys(input_schema["required"]))
            
            # 构建工具
            tool = {
                "name": tool_name,
                "description": operation.get("description") or operation.get("summary", ""),
                "inputSchema": input_schema
            }
            
            tools.append(tool)
            
            # 保存函数映射
            function_map[tool_name] = {
                "module": func_meta.get("module", ""),
                "class": func_meta.get("class"),
                "function": func_meta.get("name", ""),
                "is_async": func_meta.get("is_async", False),
                "returns_object": func_meta.get("returns_object", False),
                "http_method": method,
                "http_path": path
            }
    
    # 添加对象方法调用工具到 tools 列表
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
    
    # 生成 MCP Server 代码
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
    
    # 写入文件
    with open(output, 'w', encoding='utf-8') as f:
        f.write(server_code)
    
    # 生成文档
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
    
    # 如果指定了输入文件
    if args.input:
        input_file = args.input
        # 尝试从输入文件名推断库名
        if args.library is None:
            # 例如：pdfkit_openapi.json -> pdfkit
            import re
            match = re.match(r'(.+?)_openapi\.json$', Path(input_file).name)
            if match:
                library_name = match.group(1)
            else:
                library_name = "library"
        else:
            library_name = args.library
    else:
        # 如果没有指定输入文件，需要库名
        if args.library is None:
            sys.exit(1)
        library_name = args.library
        input_file = f"{library_name}_openapi.json"
    
    # 设置默认输出文件名
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
