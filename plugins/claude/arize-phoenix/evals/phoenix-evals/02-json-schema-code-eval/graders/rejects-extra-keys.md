---
type: llm
focus: {source: file, path: schema_eval.py}
weight: 0.5
---
用户需要一个评估器，要求输出必须是 JSON 对象，且恰好包含三个字段：`name`（字符串）、`age`（整数）、`email`（字符串），不能有额外字段。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：评估器将模式视为封闭模式，输出中出现 `name`、`age`、`email` 之外的任何字段都应判为无效（例如检查键集合是否恰好等于这三项，或使用带 `additionalProperties: false` 的模式）。如果只检查三个必需字段存在、忽略额外键，则失败。
