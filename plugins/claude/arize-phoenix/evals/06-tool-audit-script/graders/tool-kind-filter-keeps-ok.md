---
type: llm
focus: {source: file, path: tool-audit.sh}
weight: 0.5
---
你正在检查一个 bash 脚本，它应将 Phoenix 追踪记录中的每个 TOOL 跨度输出为 JSON，包括状态为 OK 的跨度。

只评定下面这一条判断条件。回复满足条件则为 PASS，否则为 FAIL；忽略回复中的其他内容。

判断条件：脚本只保留 TOOL 跨度，可以在 `px span list` 上使用 `--span-kind TOOL`，也可以在 jq 中对跨度数组按 `span_kind == "TOOL"` 筛选（`px trace get` 输出使用 `.spans[]`，`px span list` 输出使用顶层数组）。不得额外按 `status_code` 筛选，必须包含状态为 OK 的工具跨度。
