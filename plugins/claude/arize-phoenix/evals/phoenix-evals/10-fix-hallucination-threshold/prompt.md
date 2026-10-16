---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
RAG 机器人的幻觉检查代码在 `.mean()` 这一行抛出 TypeError，我也不确定阈值逻辑是否正确。`df` 是导出的数据帧，包含 `input`（用户问题）、`output`（机器人答案）和 `context`（检索文档）列。当超过 20% 的答案没有检索文档支持时，整个批次应判失败。

```python
from phoenix.evals import HallucinationEvaluator, LLM, evaluate_dataframe

llm = LLM(provider="openai", model="gpt-4o")
hallucination = HallucinationEvaluator(llm=llm)

results_df = evaluate_dataframe(dataframe=df, evaluators=[hallucination])
score = results_df["hallucination_score"].mean()
if score < 0.8:
    raise SystemExit(f"too many hallucinations: {score:.2f}")
```

请修复并保存为 `hallucination_check.py`。
