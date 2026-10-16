---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
我希望 CI 能发现 RAG 机器人的回归问题。机器人的回复必须始终非空且为有效 JSON，我也希望知道忠实性何时下降。我们已对其他功能使用 pytest，并希望将结果记录到 Phoenix，以便持续跟踪。请将测试添加到 `test_faithfulness.py`。
