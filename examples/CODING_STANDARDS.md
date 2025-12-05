# AllBeAPI Custom Code Standards

本指南旨在帮助开发者编写能够被 AllBeAPI 完美解析、评分最高且对 LLM 最友好的自定义 Python 代码。

## 🎯 核心原则 (Core Principles)

AllBeAPI 的分析引擎 (`analyzer.py`) 会根据以下维度对你的代码进行评分。遵循这些原则可以确保生成的 MCP Tool 精确且易用。

1.  **强类型注解 (Strict Typing)**: 决定了 Tool Schema 的生成质量。
2.  **详细文档 (Rich Docstrings)**: 决定了 LLM 对工具用途的理解。
3.  **显式导出 (Explicit Export)**: 控制上下文窗口，避免无关函数干扰 LLM。

---

## ✅ 最佳实践 (Best Practices)

### 1. 类型注解 (Type Hinting)

**规则**: 所有参数和返回值必须包含类型注解。
**原因**: `TypeParser` 依赖注解生成 JSON Schema。如果没有注解，参数将被视为 `Any`，导致 LLM 无法准确传递参数。

*   **❌ 错误示例**:
    ```python
    def add(a, b):
        return a + b
    ```

*   **✅ 正确示例**:
    ```python
    def add(a: int, b: int) -> int:
        return a + b
    ```

### 2. 文档字符串 (Docstrings)

**规则**: 文档长度应大于 30 个字符，并描述参数用途。
**评分机制**:
*   `> 200` 字符: 🌟🌟🌟 (1.0分)
*   `> 100` 字符: 🌟🌟 (0.7分)
*   `> 30` 字符: 🌟 (0.4分)
*   无文档: ❌ (0.1分)

*   **✅ 正确示例**:
    ```python
    def calculate_bmi(weight: float, height: float) -> float:
        """
        根据体重和身高计算 BMI 指数。
        
        Args:
            weight: 体重，单位为千克 (kg)
            height: 身高，单位为米 (m)
            
        Returns:
            计算出的 BMI 数值，保留两位小数。
        """
        return round(weight / (height ** 2), 2)
    ```

### 3. API 暴露控制 (__all__)

**规则**: 使用 `__all__` 列表明确指定要暴露给 LLM 的函数或类。
**原因**: 如果不定义 `__all__`，AllBeAPI 可能会暴露导入的第三方库函数（如 `numpy.array`），污染 LLM 的工具列表。

*   **✅ 正确示例**:
    ```python
    __all__ = ['create_user', 'get_user_status']

    import json # 这是一个内部依赖，不会被暴露

    def create_user(name: str): ...
    def get_user_status(uid: str): ...
    def _internal_helper(): ... # 下划线开头的函数自动被忽略
    ```

---

## 🧩 模式规范 (Design Patterns)

### 场景 A: 无状态工具 (Stateless Tools)
适用于计算、查询、转换等一次性任务。

*   **设计**: 使用纯函数。
*   **输入**: 基本类型 (`int`, `str`, `bool`) 或 `List`/`Dict`。
*   **输出**: 可 JSON 序列化的数据。

### 场景 B: 有状态对象 (Stateful Objects)
适用于游戏角色、数据库连接、窗口管理等需要保持状态的场景。

*   **原理**: AllBeAPI 会自动缓存返回的对象实例，并向 LLM 返回 `object_id`。
*   **设计**:
    1.  定义一个类 (`Class`) 处理业务逻辑。
    2.  提供一个**工厂函数** (`Factory Function`) 用于创建实例。
*   **示例**:
    ```python
    class BankAccount:
        def __init__(self, owner: str):
            self.balance = 0
        def deposit(self, amount: int):
            self.balance += amount

    # LLM 调用此函数，获得 object_id
    def open_account(owner: str) -> BankAccount:
        """为用户开设一个新的银行账户"""
        return BankAccount(owner)
    ```

### 场景 C: 数据处理 (Data Containers)
适用于处理 Pandas DataFrame、Numpy Array 或 PIL Image。

*   **设计**: 直接返回复杂对象即可。
*   **机制**: `SmartSerializer` 会自动判断数据大小：
    *   **小数据**: 直接转为 JSON 返回。
    *   **大数据**: 自动存储并返回 Markdown 预览 + `object_id`。

---

## 🚫 避免事项 (Don'ts)

1.  **不要**在函数名中使用无意义的名称 (如 `func1`, `do_it`)，这会降低评分。
2.  **不要**让参数列表过长 (超过 5 个参数会降低评分)。
3.  **不要**在参数中使用无法序列化的自定义类，除非该类已在代码中定义且支持状态管理。
4.  **不要**将核心逻辑放在 `if __name__ == "__main__":` 块中，否则无法被导入分析。

---

## 🏆 完美评分检查表 (Quality Checklist)

在提交代码前，请检查：

- [ ] 函数/类名是否采用清晰的 `snake_case` 或 `CamelCase`？
- [ ] 是否定义了 `__all__`？
- [ ] 所有参数都有类型注解吗？
- [ ] 文档字符串是否超过 30 个字符？
- [ ] 函数参数数量是否在 1-5 个之间？
- [ ] 是否避免了以 `_` 开头的私有函数？

---