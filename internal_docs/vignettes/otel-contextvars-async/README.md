<a id="otel-contextvars--async-generators"></a>

# OTel contextvars 与异步生成器

说明为何在 Phoenix playground（聊天、评估器、流式输出）中避免**在异步生成器清理时使用 contextvars**，以及如何验证并据此设计。

- **[分析](otel-contextvars-async.md)** — 问题、CPython/asyncio 根因、修复和设计决策。
- **配套演示** — `contextvars_async_gen_demo.py`：实测 contextvars 与异步生成器，不使用 OTel。从仓库根目录运行：

  ```bash
  uv run python internal_docs/vignettes/otel-contextvars-async/contextvars_async_gen_demo.py
  ```
