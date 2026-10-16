---
type: llm
focus: last_message
weight: 1
---
用户询问的是 Elixir 的 Phoenix Web 框架（Phoenix LiveView），而非 LLM 可观测性工具 Arize Phoenix。根据以下条件评分，全部满足才算通过。

1. 回复将问题视为 Elixir Phoenix LiveView 问题，并指出 LiveView 专属原因，例如 `handle_event` 未携带更新后的 socket 返回 `{:noreply, socket}`、修改变量而未调用 `assign/3`、模板未引用对应 assign，或状态在 LiveView 之外的进程中被修改。
2. 回复不提及 Arize Phoenix、LLM 追踪、跨度、追踪记录、OpenInference 或 `px` CLI。
3. 回复不要求用户澄清所指的是哪个 Phoenix；上下文（Elixir、LiveView、handle_event）已经明确。
