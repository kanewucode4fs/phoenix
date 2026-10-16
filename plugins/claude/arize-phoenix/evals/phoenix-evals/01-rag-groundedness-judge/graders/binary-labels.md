---
type: llm
focus: {source: file, path: groundedness_eval.py}
weight: 0.5
---
该文件是一个 Phoenix 评估器，应判断 RAG 答案是否有检索上下文的依据。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：评估器输出离散标签，而非数值或李克特量表评分。满足以下任一情况即可：（a）定义自己的离散标签（如 grounded/ungrounded 或 factual/hallucinated），并通过 `choices` 映射将其对应到分数；（b）使用 Phoenix 内置的基于标签的评估器，如 `FaithfulnessEvaluator`。只有当评估器要求模型给出 1 到 5、1 到 10 或其他数值、李克特量表评分时，才判定此条件失败。
