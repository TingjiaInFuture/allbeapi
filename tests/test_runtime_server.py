import pytest

from allbemcp.runtime.server import MCPServer


class _SampleObject:
    def public(self):
        return "ok"

    def _private(self):
        return "secret"


@pytest.mark.asyncio
async def test_execute_tool_stats_count_success_and_error(monkeypatch):
    server = MCPServer(title="Test", tools=[], function_map={}, library_name="testlib")

    server.function_map["ok-tool"] = {
        "module": "dummy",
        "function": "ok",
        "is_async": False,
        "returns_object": False,
    }
    server.function_map["bad-tool"] = {
        "module": "dummy",
        "function": "bad",
        "is_async": False,
        "returns_object": False,
    }

    def ok(value: int):
        return value + 1

    def bad():
        raise RuntimeError("boom")

    monkeypatch.setattr(
        server,
        "_get_function",
        lambda tool_name: ok if tool_name == "ok-tool" else bad,
    )

    result = await server._execute_tool("ok-tool", {"value": 1})
    assert result["success"] is True
    assert result["data"] == 2

    with pytest.raises(RuntimeError, match="boom"):
        await server._execute_tool("bad-tool", {})

    stats = server.get_call_stats()
    assert stats["ok-tool"]["count"] == 1
    assert stats["ok-tool"]["errors"] == 0
    assert stats["bad-tool"]["count"] == 1
    assert stats["bad-tool"]["errors"] == 1


@pytest.mark.asyncio
async def test_call_stored_method_blocks_private_methods():
    server = MCPServer(title="Test", tools=[], function_map={}, library_name="testlib")
    server._object_store["obj_1"] = _SampleObject()

    with pytest.raises(ValueError, match="private/dunder"):
        await server._call_stored_method(
            {
                "object_id": "obj_1",
                "method": "_private",
                "args": [],
                "kwargs": {},
            }
        )


def test_coerce_types_resolves_object_reference_from_annotations():
    server = MCPServer(title="Test", tools=[], function_map={}, library_name="testlib")
    obj = _SampleObject()
    server._object_store["obj_ref"] = obj

    def consume(item: _SampleObject):
        return item

    coerced = server._coerce_types(consume, {"item": "obj_ref"})
    assert coerced["item"] is obj


class _DummySerializerConfig:
    resource_base_url = "mcp://resources"


class _DummySerializer:
    def __init__(self):
        self.config = _DummySerializerConfig()
        self.resource_store = {
            "res_1": {
                "content": "hello",
                "content_type": "text/plain",
            }
        }

    def get_resource(self, resource_id: str):
        return self.resource_store.get(resource_id)


def test_list_resources_returns_resource_entries_from_serializer():
    server = MCPServer(title="Test", tools=[], function_map={}, library_name="testlib")
    server.serializer = _DummySerializer()

    resources = server._list_resources()
    assert len(resources) == 1
    assert resources[0]["resource_id"] == "res_1"
    assert resources[0]["uri"] == "mcp://resources/res_1"
    assert resources[0]["content_type"] == "text/plain"


def test_read_resource_supports_uri_and_returns_text_content():
    server = MCPServer(title="Test", tools=[], function_map={}, library_name="testlib")
    server.serializer = _DummySerializer()

    result = server._read_resource("mcp://resources/res_1")
    assert result["success"] is True
    assert result["resource_id"] == "res_1"
    assert result["content_type"] == "text/plain"
    assert result["content"] == "hello"


@pytest.mark.asyncio
async def test_native_resources_and_prompts_registered_and_working():
    server = MCPServer(
        title="Test",
        tools=[{"name": "demo-tool", "inputSchema": {"type": "object", "properties": {}}}],
        function_map={},
        library_name="testlib",
    )
    server.serializer = _DummySerializer()

    resources = await server.mcp.list_resources()
    resource_uris = {str(resource.uri) for resource in resources}
    assert "allbemcp://objects" in resource_uris
    assert "allbemcp://resources" in resource_uris
    assert "allbemcp://call-stats" in resource_uris

    templates = await server.mcp.list_resource_templates()
    template_uris = {str(template.uri_template) for template in templates}
    assert "mcp://resources/{resource_id}" in template_uris

    direct_resource = await server.mcp.read_resource("allbemcp://resources")
    assert any("res_1" in str(content.content) for content in direct_resource.contents)

    template_resource = await server.mcp.read_resource("mcp://resources/res_1")
    assert any("hello" in str(content.content) for content in template_resource.contents)

    prompts = await server.mcp.list_prompts()
    prompt_names = {prompt.name for prompt in prompts}
    assert "allbemcp-tool-usage" in prompt_names
    assert "allbemcp-object-workflow" in prompt_names

    prompt_result = await server.mcp.render_prompt(
        "allbemcp-tool-usage",
        {"user_goal": "analyze dataset"},
    )
    assert any("analyze dataset" in str(message.content) for message in prompt_result.messages)
