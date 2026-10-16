---
type: llm
focus: {source: file, path: schema_eval.py}
weight: 0.5
---
用户需要一个评估器，要求输出必须是 JSON 对象，且恰好包含三个字段：`name`（字符串）、`age`（整数）、`email`（字符串），不能有额外字段。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：评估器拒绝布尔类型的 `age`（如 `{"age": true}`）。Python 中 `isinstance(True, int)` 为 `True`，所以单独使用 `isinstance(value, int)` 会接受布尔值；评估器必须显式排除 `bool`（如 `isinstance(v, int) and not isinstance(v, bool)`、`type(v) is int`，或使用 `integer` 类型会拒绝布尔值的 JSON Schema 验证器）。如果仅检查 `isinstance(age, int)` 而不排除 bool，则失败。
