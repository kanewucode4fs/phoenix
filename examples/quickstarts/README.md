<a id="quickstart-examples"></a>

# 快速入门示例

以下是 Phoenix 文档中各篇快速入门指南对应的可运行代码：

| 指南 | Python | TypeScript |
| --- | --- | --- |
| [观测](https://arize.com/docs/phoenix/get-started/get-started-tracing) | `python/observe.py` | `typescript/instrumentation.ts`, `typescript/app.ts` |
| [评估](https://arize.com/docs/phoenix/get-started/get-started-evaluations) | `python/evaluate.py` | `typescript/evaluate.ts` |
| [在代码中评估提示词改动](https://arize.com/docs/phoenix/datasets-and-experiments/how-to-experiments/evaluate-a-prompt-change) | `python/experiment.py` | `typescript/experiment.ts` |

`make sync-docs-snippets` 会将这些文件中的代码复制到指南的代码块中。
当两者不一致时，`make check-docs-snippets` 会使持续集成（CI）检查失败。
请先在此处修改并运行代码，再执行同步。标记的用法见 `python3 scripts/sync_docs_snippets.py --help`。

<a id="run"></a>

## 运行

先通过 `uvx arize-phoenix serve` 启动 Phoenix，使其运行在 `http://localhost:6006`，
并设置 `OPENAI_API_KEY` 环境变量。其中的实验示例不需要模型密钥。

```bash
cd python && pip install -r requirements.txt
python observe.py && python evaluate.py && python experiment.py
```

```bash
cd typescript && npm install
npm run observe && npm run evaluate && npm run experiment
```
