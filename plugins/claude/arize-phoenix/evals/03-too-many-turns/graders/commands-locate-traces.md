---
type: llm
focus: last_message
weight: 0.5
---
用户的智能体回答简单问题需要 30 多次 LLM 调用，期间没有错误；用户询问应运行哪些 `px` CLI 命令以及应检查什么。这是执行轨迹问题：答案在跨度的顺序和内容中，而非状态码中。

只评定下面这一条判断条件。回复满足条件则为 PASS，否则为 FAIL；忽略回复中的其他内容。

判断条件：回复给出真实可运行的 `px` 命令来定位有问题的追踪记录，例如 `px trace list ... --format raw --no-progress | jq 'sort_by(-.duration)'`，或按 `latency_ms` 筛选，然后通过 `px trace get <id> --format raw`（或 `px span list --trace-id <id>`）打开其中一条。
