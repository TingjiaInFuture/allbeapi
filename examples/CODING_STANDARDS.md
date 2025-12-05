# Coding Standards for Custom Tools

This document outlines the best practices for writing custom Python code intended for use with AllBeAPI.

AllBeAPI utilizes static analysis and runtime introspection to generate Model Context Protocol (MCP) server definitions. Adhering to these standards ensures that the generated tools provide accurate schemas, high-quality descriptions, and reliable execution contexts for Large Language Models (LLMs).

## Core Principles

The AllBeAPI analysis engine (`analyzer.py`) evaluates code based on three primary metrics:

1.  **Type Precision**: Determines the accuracy of the generated JSON Schema.
2.  **Documentation Density**: Determines the context provided to the LLM for tool selection.
3.  **Namespace Clarity**: Ensures only relevant functions are exposed to the context window.

---

## 1. Namespace Control

### Explicit Export via `__all__`
By default, AllBeAPI may inspect all functions found in a module, including those imported from third-party libraries. To prevent polluting the LLM context window with utility functions or imports, you must explicitly define the `__all__` list.

**Requirement:**
Define `__all__` at the module level containing the strings of the functions or classes you wish to expose.

**Example:**

```python
__all__ = ['calculate_metric', 'UserSession']

import json  # This will be ignored by the analyzer
import numpy as np  # This will be ignored

def _internal_helper():
    # Functions starting with underscore are automatically ignored
    pass

def calculate_metric(data: list) -> float:
    return np.mean(data)

class UserSession:
    pass
```

---

## 2. Type Hinting

AllBeAPI uses the Python `typing` module to generate the `inputSchema` for MCP tools. Missing type hints result in arguments being treated as `Any`, which significantly degrades the LLM's ability to call tools correctly.

**Requirement:**
All exposed functions and methods must have type annotations for arguments and return values.

**Supported Types:**
- Primitives: `int`, `float`, `str`, `bool`
- Containers: `List[...]`, `Dict[..., ...]`, `Optional[...]`
- Complex: Custom Classes (for stateful workflows)

**Correct:**
```python
def resize_image(width: int, height: int, keep_aspect: bool = True) -> str:
    ...
```

**Incorrect:**
```python
def resize_image(width, height, keep_aspect=True):
    ...
```

---

## 3. Documentation

The docstring of a function is transformed directly into the tool description field in the MCP protocol. This is the primary signal the LLM uses to decide which tool to call. The `QualityMetrics` engine scores APIs based on docstring length and detail.

**Scoring Thresholds:**
- **High Quality**: > 200 characters.
- **Medium Quality**: > 100 characters.
- **Low Quality**: < 30 characters (May be filtered out in strict mode).

**Requirement:**
Provide a descriptive docstring that explains the purpose of the function and the meaning of its arguments.

**Example:**
```python
def calculate_compound_interest(principal: float, rate: float, years: int) -> float:
    """
    Calculates the future value of an investment based on compound interest.

    This function uses the standard compound interest formula. It is useful for
    financial projections and savings estimation.

    Args:
        principal: The initial amount of money deposited or invested.
        rate: The annual interest rate (as a decimal, e.g., 0.05 for 5%).
        years: The number of years the money is invested for.

    Returns:
        The future value of the investment rounded to two decimal places.
    """
    return round(principal * (1 + rate) ** years, 2)
```

---

## 4. Design Patterns

### Pattern A: Stateless Tools
Use this pattern for utility functions, data transformations, or database queries that return immediate results.

*   **Structure**: Pure functions.
*   **Input**: Primitives or Data Structures.
*   **Output**: JSON-serializable data, Strings, or DataFrames.

### Pattern B: Stateful Agents (The Factory Pattern)
Use this pattern when you need to maintain context (e.g., database connections, game states, file system cursors) across multiple LLM turns.

*   **Mechanism**: When a function returns a class instance, AllBeAPI caches the instance and returns a reference ID. The LLM can then call methods on that specific instance.
*   **Structure**: A class definition and a factory function to instantiate it.

**Example:**

```python
class DatabaseConnection:
    """Represents an active connection to a specific database."""
    
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.is_connected = True

    def query(self, sql: str) -> list:
        """Executes a SQL query on the active connection."""
        return ["mock_result"]

    def close(self) -> bool:
        """Closes the connection."""
        self.is_connected = False
        return True

# The Factory Function (The Entry Point for the LLM)
def connect_to_db(db_name: str) -> DatabaseConnection:
    """
    Establishes a connection to the database.
    Returns a connection object that can be used for subsequent queries.
    """
    return DatabaseConnection(db_name)
```

### Pattern C: Data Containers
AllBeAPI's `SmartSerializer` automatically handles complex data types like Pandas DataFrames, NumPy Arrays, or PIL Images.

*   **Requirement**: Simply return the object. Do not manually convert it to a string or dictionary unless specific formatting is required.
*   **Behavior**: Small objects are serialized to JSON; large objects are stored, and a preview is returned to the LLM.

---

## 5. Naming Conventions

The analyzer applies heuristics to function names to determine their purpose and quality.

*   **Style**: Use `snake_case` for functions and `CamelCase` for classes.
*   **Clarity**: Avoid generic names like `run`, `do_it`, or `func1`.
*   **Prefixes**: The analyzer recognizes intent prefixes such as `get_`, `create_`, `update_`, `delete_`, and `calculate_`.

---

## Quality Checklist

Before exposing your custom code to an LLM, verify the following:

- [ ] **Export**: Is `__all__` defined?
- [ ] **Typing**: Are all arguments and return values typed?
- [ ] **Docs**: Does the docstring exceed 30 characters?
- [ ] **Complexity**: Is the argument count between 1 and 5 (ideal range)?
- [ ] **Naming**: Are names descriptive and compliant with PEP 8?
