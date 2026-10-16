---
type: llm
focus: {source: file, path: tool-audit.sh}
weight: 0.5
---
你正在检查一个 bash 脚本，它应将 Phoenix 追踪记录中的每个 TOOL 跨度输出为 JSON，包括状态为 OK 的跨度。

只评定下面这一条判断条件。回复满足条件则为 PASS，否则为 FAIL；忽略回复中的其他内容。

判断条件：脚本为每个工具跨度输出跨度 `name`、`status_code`，以及从 `.attributes["input.value"]` 和 `.attributes["output.value"]`（或等价路径）读取的工具输入与输出。如果读取追踪 JSON 中不存在的字段，如跨度顶层的 `.tool.parameters`，或不带 `.value` 的 `.input`，则不满足此条件。
