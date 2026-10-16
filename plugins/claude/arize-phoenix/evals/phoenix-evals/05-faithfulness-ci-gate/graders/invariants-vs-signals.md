---
type: llm
focus: {source: file, path: test_faithfulness.py}
weight: 0.5
---
该文件是一个 pytest 测试套件，应根据 RAG 机器人的忠实性实施 CI 门禁，同时强制满足两个硬性不变量（回复非空、JSON 有效）。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：测试套件遵循“不变量与信号分开处理”的原则，区别处理这两类关注点。对硬性不变量（回复非空、JSON 有效）使用断言，任何违反都立即使 CI 失败。忠实性信号（LLM 裁判）通过 `log_evaluation`/`evaluate`（或等价的已记录信号）逐例记录，不对每个单独用例作断言；忠实性门禁交给独立的汇总或趋势机制（夜间阈值、`run_experiment`，或对收集分数进行显式汇总检查），而非逐例断言。如果测试套件对每个用例都断言 `faithful == True`，则失败。
