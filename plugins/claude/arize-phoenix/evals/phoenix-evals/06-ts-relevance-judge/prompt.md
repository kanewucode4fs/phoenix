---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
我有一个基于 Vercel AI SDK 和 OpenAI 构建的 TypeScript RAG 应用。我需要一个评估器，判断助手答案是否与用户问题相关，以便对记录下来的交互运行评估。请保存为 `relevanceEvaluator.ts`。
