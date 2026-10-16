---
type: llm
focus: {source: file, path: run_eval_experiment.py}
weight: 0.5
---
用户询问如何在含 50 个示例的问答数据集上，将自己的任务和评估器作为 Phoenix 实验运行。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：脚本将本地 50 个示例创建或上传为数据集（如 `client.datasets.create_dataset(...)`），定义任务函数，并调用 `run_experiment`，传入数据集、任务及一个或多个评估器。代码必须具体到用户可以运行，不能只是伪代码或文字描述。
