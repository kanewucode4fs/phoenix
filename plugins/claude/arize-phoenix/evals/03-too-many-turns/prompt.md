---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read]
runs: 3
tags: [phoenix-cli]
---
我们的客服智能体（Phoenix 项目 `helpdesk`）有时需要 30 次或更多 LLM 调用，才能回答“退款期限是多久”这样的一句话问题，客户需要等待 40 秒。没有任何报错，所以追踪记录看起来全是绿色。我已经安装 `px` CLI 并设置 `PHOENIX_ENDPOINT`，但你无法从这里访问。请逐步说明应具体运行哪些命令来查找这些追踪记录，以及应检查其中哪些内容，才能弄清智能体为何需要这么多轮调用。
