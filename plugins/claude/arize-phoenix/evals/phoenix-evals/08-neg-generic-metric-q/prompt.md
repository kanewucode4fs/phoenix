---
max_turns: 6
timeout_seconds: 180
allowed_tools: [Skill, Read]
runs: 3
tags: [phoenix-evals]
---
我有一个 CSV 文件，包含 500 条机器翻译输出及其参考译文。我希望对整批数据计算一个语料库级 BLEU 分数，与其他指标一起报告。应该使用哪个库，具体如何调用？
