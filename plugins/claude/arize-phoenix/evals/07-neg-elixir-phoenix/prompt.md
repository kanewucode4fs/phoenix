---
max_turns: 6
timeout_seconds: 180
allowed_tools: [Skill, Read]
runs: 3
tags: [phoenix-cli]
---
我在 Elixir 中使用 Phoenix Web 框架。在 handle_event 中更新状态后，LiveView 没有重新渲染。事件已经触发（日志中可见），但模板没有变化。我哪里做错了？
