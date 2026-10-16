---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
我已有一个评估器函数和 50 个问答示例，每个示例包含 `question` 和 `expected` 答案。我的任务调用 gpt-4o 回答问题。我希望将任务和评估器作为 Phoenix 实验，在全部 50 个示例上运行，从而在 Phoenix 界面查看汇总分数并比较不同运行。请将脚本写入 `run_eval_experiment.py`。
