
<img width="1361" height="192" alt="logo" src="https://github.com/user-attachments/assets/e672b767-c37a-449d-88a6-4fc249c14db8" />

> **Turn any Python library or your local script into an LLM Tool in seconds.**

![demo](https://github.com/user-attachments/assets/2ff57087-97c8-4429-898a-6ac918a47cd3)


allbemcp is a high-performance bridge that instantly exposes any Python environment—whether standard PyPI libraries or your own custom code—as a Model Context Protocol (MCP) server. It enables Large Language Models (Claude, ChatGPT, etc.) to execute local functions, manipulate dataframes, manage stateful objects, and interact with your system safely and efficiently.

Built on the latest **FastMCP + StreamableHTTP** runtime for maximum compatibility with Claude Desktop, LangChain, and Cursor.

## Installation

```bash
pip install allbemcp
```

## Usage Scenarios

allbemcp supports two primary use cases: exposing public libraries and exposing your own custom business logic.

### 1. Exposing Public Libraries
Expose `pandas`, `numpy`, or any other installed library to your LLM with a single command. allbemcp handles dependency installation and API generation automatically.

```bash
# Install, generate, and serve in one go
allbemcp start pandas

# Explicit transport selection
allbemcp start pandas --transport streamable-http
allbemcp start pandas --transport stdio
```

### 2. Exposing Custom Code
allbemcp treats your local Python scripts as first-class citizens. It parses type hints, docstrings, and class structures to generate high-quality tool definitions.

**Step 1: Create your script (e.g., `my_tools.py`)**

```python
# my_tools.py
from typing import List

def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """
    Calculate Body Mass Index (BMI).
    
    Args:
        weight_kg: Weight in kilograms.
        height_m: Height in meters.
    """
    return round(weight_kg / (height_m ** 2), 2)

class BankAccount:
    """A stateful class example."""
    def __init__(self, owner: str):
        self.owner = owner
        self.balance = 0

    def deposit(self, amount: float) -> str:
        self.balance += amount
        return f"Deposited ${amount}. New balance: ${self.balance}"

# Factory function to create instances
def open_account(owner: str) -> BankAccount:
    return BankAccount(owner)
```

**Step 2: Start the server**

```bash
# allbemcp detects the file in your current directory
allbemcp start my_tools

# FastMCP 3.x is enabled by default in generated requirements
allbemcp generate my_tools --use-fastmcp
```

The LLM can now call `calculate_bmi` directly. Furthermore, if the LLM calls `open_account`, allbemcp automatically manages the returned `BankAccount` instance, allowing the LLM to make subsequent calls to `deposit` on that specific object.

## Client Configuration

To use your tools with **Claude Desktop** or other MCP clients, add the corresponding configuration to your `claude_desktop_config.json`.

**For a Library (e.g., pandas):**
```json
{
  "mcpServers": {
    "pandas": {
      "command": "uv",
      "args": ["run", "allbemcp", "start", "pandas"]
    }
  }
}
```

**For Custom Code (e.g., my_tools):**
```json
{
  "mcpServers": {
    "my_tools": {
      "command": "uv",
      "args": ["run", "allbemcp", "start", "my_tools"],
      "cwd": "/absolute/path/to/your/script/directory"
    }
  }
}
```

## Key Features

### Zero-Config Introspection
Automatically inspects Python packages or local modules, extracts public APIs, and generates a fully compliant MCP server. No manual schema definition (YAML/JSON) is required.

### Stateful Object Management
Unlike standard stateless tools, allbemcp supports object-oriented workflows:
- **Instance Persistence**: When a function returns a class instance, it is stored in memory.
- **Method Chaining**: LLMs can invoke methods on specific stored instances via a generated `object_id`.
- **Ideal For**: Database connections, game states, simulation environments, and session-based workflows.

### Smart Serialization Engine
LLMs struggle with complex objects. allbemcp handles them automatically:
- **DataFrames**: Converted to markdown or JSON previews based on size.
- **Images**: Automatically encoded or saved to temporary storage with resource links.
- **Iterators**: Automatically consumed and summarized.

### Local & Secure
Runs entirely on your machine. No data leaves your network. You control the host binding (default `127.0.0.1`) and execution environment.

## Advanced Usage

### Inspect a Library
Check which functions will be exposed and view their quality scores before generating code:

```bash
allbemcp inspect numpy
```

### Generate Only
Generate the server code without running it (useful for auditing or customization):

```bash
allbemcp generate matplotlib --output-dir ./my-server
```

## License

This project is licensed under the **AGPL v3 License**.
