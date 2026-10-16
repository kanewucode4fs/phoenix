---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
我构建了一个判断答案正确性的 LLM 裁判。有 80 个示例，由我们的两位分析人员人工标为 pass 或 fail；我也在同一批 80 个示例上运行了裁判，获得了它的预测。在生产环境中信任它之前，我希望衡量它与人工标签的一致性，并判断其是否足够好。请逐步说明需要计算什么，并将代码写入 `validate_judge.py`。
