---
type: llm
focus: {source: file, path: relevance_eval.py}
weight: 0.5
---
用户粘贴了一个旧版 phoenix-evals 1.0 脚本（导入 `OpenAIModel` 和 `llm_classify`，使用 `RAG_RELEVANCY_PROMPT_TEMPLATE` 及 `rails=` 参数），要求迁移到当前 2.x API，使其重新可运行，并保存为 `relevance_eval.py`。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：可执行代码仅使用 2.0 API，不调用或导入旧版 1.0 API：不得使用 `OpenAIModel`、`llm_classify`、`run_evals`、`rails=` 参数，也不得从 `phoenix.evals.legacy` 或 `phoenix.evals.default_templates` 导入。在说明迁移的注释或文档字符串中提及、引用或映射旧 API 不算违规；只有实际的可执行用法才算。
