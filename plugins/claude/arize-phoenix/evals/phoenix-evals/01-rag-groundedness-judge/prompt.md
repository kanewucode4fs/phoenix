---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
我有一个基于 Python 的 RAG 客服机器人（OpenAI 加向量存储）。它有时会给出检索上下文中不存在的说法。我需要一个评估器，接收检索上下文和机器人的答案，判断答案是否以上下文为依据。我会将它用于导出的追踪数据帧，请写成可复用形式，并放在 `groundedness_eval.py` 中。
