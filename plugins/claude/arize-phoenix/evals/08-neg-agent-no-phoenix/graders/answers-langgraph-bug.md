---
type: llm
focus: last_message
weight: 1
---
用户询问为什么 LangGraph 智能体无限循环。缺陷在 `should_continue` 中：只要 `state["messages"]` 非空就返回 "tools"，而该列表始终非空；它本应检查最后一条 AI 消息是否包含工具调用。问题没有提及 Phoenix、Arize 或追踪。根据以下条件评分，全部满足才算通过。

1. 回复指出路由条件检查的是消息列表的真值，而非最后一条消息中的 `tool_calls`，因此总是路由到 "tools"。
2. 回复给出修正后的 `should_continue`（例如 `last = state["messages"][-1]; return "tools" if getattr(last, "tool_calls", None) else END`），或等价的预置 `tools_condition`。
3. 回答主体围绕 LangGraph 代码，不包含 `px` 命令，也不展开介绍 Arize Phoenix 或 OpenInference 追踪。可以用一句话建议通过追踪图来观察循环；超过一句则不满足此条件。
