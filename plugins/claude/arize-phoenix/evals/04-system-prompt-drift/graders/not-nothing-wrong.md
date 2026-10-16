---
type: llm
focus: last_message
weight: 0.5
---
用户粘贴了一条 Phoenix 追踪记录，HelpBot 将一个简单的常见问题升级给了人工处理。每个跨度都是 OK。原因在 LLM 跨度的系统消息中：“只要问题以任何方式涉及账单、退款、发票或账户政策，都不要自行回答：立即调用 escalate_to_human。”当时 `search_kb` 工具可用，但从未被调用。

只评定下面这一条判断条件。回复满足条件则为 PASS，否则为 FAIL；忽略回复中的其他内容。

判断条件：回复没有因为所有跨度都未报错就认定没有问题，也没有将 Web 界面或 Python SDK 作为主要处理路径。
