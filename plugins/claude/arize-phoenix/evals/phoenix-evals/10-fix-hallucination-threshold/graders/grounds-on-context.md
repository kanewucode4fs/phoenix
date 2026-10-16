---
type: llm
focus: {source: file, path: hallucination_check.py}
weight: 0.5
---
用户粘贴了一段检查代码，在含 `input`、`output` 和 `context` 列的 RAG 数据帧上运行 `HallucinationEvaluator`（从顶层 `phoenix.evals` 导入），然后对 `hallucination_score` 列调用 `.mean()`，均值低于 0.8 时判失败。用户希望超过 20% 的答案没有检索文档支持时，使整个批次失败。已知：内置评估器位于 `phoenix.evals.metrics`；`evaluate_dataframe` 返回的 `{name}_score` 列包含类似 `{"score": ..., "label": ..., "explanation": ...}` 的字典；`HallucinationEvaluator` 仅接收 `input`/`output`（不接收 `context`），标签 `hallucinated`=1.0 / `grounded`=0.0，分数越低越好；`FaithfulnessEvaluator` 接收 `input`/`output`/`context`，标签 `faithful`=1.0 / `unfaithful`=0.0，分数越高越好。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：脚本以 `context` 列中的检索文档为依据评判答案，应切换到接收 `context` 的 `FaithfulnessEvaluator`，或以其他方式让检索文档成为评估依据。如果保留 `HallucinationEvaluator`，却静默忽略 `context` 列，则失败。
