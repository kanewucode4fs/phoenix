---
type: llm
focus: {source: file, path: run_eval_experiment.py}
weight: 0.5
---
该脚本在含 50 个示例的问答数据集上运行任务和评估器，每个示例均包含 `question`（输入）和 `expected` 答案（输出）。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：任务从示例输入中读取问题（如 `example.input["question"]`），评估器通过标准实验参数名（`output` 和 `expected`）接收任务输出和预期答案，且与数据集输入、输出键的构造方式一致，使其能够运行，而不会因缺失键或参数而报错。
