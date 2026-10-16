---
type: llm
focus: {source: file, path: tool-audit.sh}
weight: 0.5
---
你正在检查一个 bash 脚本，它应将 Phoenix 追踪记录中的每个 TOOL 跨度输出为 JSON，包括状态为 OK 的跨度。

只评定下面这一条判断条件。回复满足条件则为 PASS，否则为 FAIL；忽略回复中的其他内容。

判断条件：脚本按 `start_time` 对跨度排序（或保留数组顺序并加以说明），且输出为 JSON，而非表格或自由文本。
