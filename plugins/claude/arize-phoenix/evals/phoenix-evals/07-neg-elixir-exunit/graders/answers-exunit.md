---
type: llm
focus: last_message
weight: 0.5
---
用户询问的是 Elixir 的 Phoenix Web 框架（编写验证状态码和 JSON 响应体的 ExUnit 控制器测试），而非 LLM 可观测性与评估工具 Arize Phoenix。

只评定下面这一条判断条件。回复满足条件则为 PASS，否则为 FAIL；忽略回复中的其他内容。

判断条件：回复将问题视为 Elixir Phoenix / ExUnit 控制器测试问题，并提供 ExUnit 专属指导，例如 `ConnCase`、在 `conn` 上调用 `get/post`、使用 `json_response/2`，或对状态码作断言。
