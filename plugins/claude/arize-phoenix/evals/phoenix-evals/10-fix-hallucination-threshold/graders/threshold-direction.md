---
type: llm
focus: {source: file, path: hallucination_check.py}
weight: 0.5
---
用户粘贴了一段检查代码，在含 `input`、`output` 和 `context` 列的 RAG 数据帧上运行 `HallucinationEvaluator`（从顶层 `phoenix.evals` 导入），然后对 `hallucination_score` 列调用 `.mean()`，均值低于 0.8 时判失败。用户希望超过 20% 的答案没有检索文档支持时，使整个批次失败。已知：内置评估器位于 `phoenix.evals.metrics`；`evaluate_dataframe` 返回的 `{name}_score` 列包含类似 `{"score": ..., "label": ..., "explanation": ...}` 的字典；`HallucinationEvaluator` 仅接收 `input`/`output`（不接收 `context`），标签 `hallucinated`=1.0 / `grounded`=0.0，分数越低越好；`FaithfulnessEvaluator` 接收 `input`/`output`/`context`，标签 `faithful`=1.0 / `unfaithful`=0.0，分数越高越好。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：通过或失败逻辑与评估器分数方向一致，使批次恰好在超过 20% 的答案没有文档支持时失败：使用 `HallucinationEvaluator`（hallucinated = 1.0）时，幻觉率超过 0.2 则失败；使用 `FaithfulnessEvaluator`（faithful = 1.0）时，忠实率低于 0.8 则失败。若将幻觉分数的 1.0 视为“好”，则失败。
