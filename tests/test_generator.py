from pathlib import Path

from allbemcp.generator import generate_mcp_server, generate_requirements


def test_generate_mcp_server_writes_all_artifacts_to_output_dir(tmp_path: Path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Demo API", "version": "1.0.0"},
        "paths": {
            "/calc/add": {
                "post": {
                    "operationId": "calc__add",
                    "description": "Add two numbers",
                    "parameters": [
                        {"name": "a", "in": "query", "required": True, "schema": {"type": "integer"}},
                        {"name": "b", "in": "query", "required": True, "schema": {"type": "integer"}},
                    ],
                    "x-function": {
                        "module": "demo",
                        "name": "add",
                        "is_async": False,
                        "returns_object": False,
                    },
                }
            }
        },
    }

    output_file = tmp_path / "demo_server.py"
    generate_mcp_server(spec, output=str(output_file), library_name="demo")

    assert output_file.exists()
    readme_file = tmp_path / "demo_MCP_README.md"
    assert readme_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "call-object-method" in content
    assert "calc-add" in content


def test_generate_requirements_supports_output_dir(tmp_path: Path):
    generate_requirements("json", output_dir=str(tmp_path))
    stdlib_req = (tmp_path / "json_mcp_requirements.txt").read_text(encoding="utf-8")
    assert "# json is a standard library module" in stdlib_req

    generate_requirements("requests", output_dir=str(tmp_path))
    third_party_req = (tmp_path / "requests_mcp_requirements.txt").read_text(encoding="utf-8")
    assert "requests" in third_party_req
