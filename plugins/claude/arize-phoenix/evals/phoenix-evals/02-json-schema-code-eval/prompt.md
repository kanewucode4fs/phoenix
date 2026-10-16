---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
我的智能体应输出单个 JSON 对象，且恰好包含以下字段：`name`（字符串）、`age`（整数）和 `email`（字符串）。我需要一个 Phoenix 评估器，检查给定输出字符串是否为有效 JSON 并符合该模式：只能有这三个字段，不允许额外字段。请放在 `schema_eval.py` 中。
