---
type: llm
focus: {source: file, path: relevance_eval.py}
weight: 0.5
---
原脚本打印 `results["label"].value_counts()`。在 2.0 API 中，`evaluate_dataframe` / `async_evaluate_dataframe` 返回的数据帧包含 `{evaluator_name}_score` 列，其单元格是类似 `{"score": 1.0, "label": "relevant", "explanation": "..."}` 的字典，不再有独立的 `label` 列。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：为复现各标签计数，脚本应从 `{name}_score` 字典列中读取标签，例如 `results_df["<name>_score"].apply(lambda x: x.get("label") if isinstance(x, dict) else None).value_counts()`；不能索引已经不存在的独立 `results["label"]` 列，也不能直接对字典列作数值聚合。
