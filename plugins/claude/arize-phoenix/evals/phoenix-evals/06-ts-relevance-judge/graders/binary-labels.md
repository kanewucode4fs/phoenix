---
type: llm
focus: {source: file, path: relevanceEvaluator.ts}
weight: 0.5
---
该文件是一个 Phoenix TypeScript 评估器，应判断助手的答案是否与用户问题相关。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：评估器在离散选项（如 relevant/irrelevant）中作出选择，并通过 `choices` 对象映射到分数。它不会要求模型给出 1 到 5、1 到 10 或其他数值、李克特量表评分。
