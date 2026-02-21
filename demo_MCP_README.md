# Demo API

## Tools

### calc-add

Add two numbers


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| a | integer | Yes |  |
| b | integer | Yes |  |


---

### call-object-method

Call a method on a stored object. Use this after getting an object_id from another tool.


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| object_id | string | Yes | The ID of the stored object |
| method | string | Yes | The name of the method to call |
| args | array | No | Positional arguments for the method |
| kwargs | object | No | Keyword arguments for the method |


---
