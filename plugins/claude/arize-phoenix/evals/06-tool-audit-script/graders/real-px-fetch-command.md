---
type: llm
focus: {source: file, path: tool-audit.sh}
weight: 0.5
---
你正在检查一个 bash 脚本，它应将 Phoenix 追踪记录中的每个 TOOL 跨度输出为 JSON，包括状态为 OK 的跨度。

只评定下面这一条判断条件。回复满足条件则为 PASS，否则为 FAIL；忽略回复中的其他内容。

判断条件：脚本使用真实的 `px` 命令获取追踪记录中的跨度：`px trace get "$1"` 或 `px span list --trace-id "$1"`，并传入 `--format raw` 或 `--format json`（可以同时使用 `--no-progress` 或 `--limit`）。如果使用虚构命令或选项，如 `px spans get`、`px span get` 或 `--output json`，则不满足此条件。脚本不能硬编码追踪 ID 或端点 URL，而应依赖环境变量 `PHOENIX_ENDPOINT`。
