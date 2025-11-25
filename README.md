<img width="1361" height="192" alt="logo" src="https://github.com/user-attachments/assets/2a8a71b8-c141-49a2-b8ef-d9f84b92261b" />

> **Turn any Python library into an LLM Tool in seconds.**

![demo](https://github.com/user-attachments/assets/4fcbcacf-4bdb-4c4a-b451-8e4dae17a2df)


AllBeAPI is a high-performance bridge that instantly exposes any Python library as a Model Context Protocol (MCP) server. It enables Large Language Models (Claude, ChatGPT, etc.) to execute local Python code, manipulate dataframes, process images, and interact with your system—safely and efficiently.

Built on the latest **StreamableHTTP** protocol for maximum compatibility with Claude Desktop, LangChain, and Cursor.

## Installation

```bash
pip install allbeapi
```

## Quick Start

Expose `pandas` (or any other library) to your LLM with a single command:

```bash
# Install, generate, and serve in one go
allbeapi start pandas
```

The server will start on `http://127.0.0.1:8000/mcp`.

## Client Configuration

To use your new tool with **Claude Desktop** or other MCP clients, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pandas": {
      "command": "uv",
      "args": [
        "run",
        "allbeapi",
        "start",
        "pandas"
      ]
    }
  }
}
```

## Key Features

### Zero-Config Generation
Automatically inspects any installed Python package, extracts public APIs, and generates a fully compliant MCP server. No manual schema definition required.

### Smart Serialization Engine
LLMs struggle with complex objects. AllBeAPI handles them automatically:
- **DataFrames**: Converted to markdown or JSON previews.
- **Images**: Automatically encoded or saved to temp storage.
- **Classes**: Stateful object management allows you to instantiate classes and call methods on instances.

### Local & Secure
Runs entirely on your machine. No data leaves your network. You control the host binding (default `127.0.0.1`) and execution environment.

### Modern Stack
- **Typer**: For a robust, ergonomic CLI experience.
- **FastAPI / Starlette**: High-performance async networking.
- **Pydantic**: Strict data validation and schema generation.

## Advanced Usage

### Inspect a Library
Check which functions will be exposed before generating code:

```bash
allbeapi inspect numpy
```

### Generate Only
Generate the server code without running it (useful for customization):

```bash
allbeapi generate matplotlib --output-dir ./my-server
```

## License

This project is licensed under the **AGPL v3 License**.
