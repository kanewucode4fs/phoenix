<a id="phoenix-scripts"></a>

# Phoenix 脚本

用于支持 Phoenix 开发的工具、测试、数据生成和 CI 脚本。大部分 Python 脚本可通过 `uv run scripts/<path>` 运行；部分脚本声明了 PEP 723 内联依赖，其他脚本则假定已经激活项目虚拟环境。

<a id="top-level-scripts"></a>

## 顶层脚本

| 脚本 | 用途 |
| --- | --- |
| `generate_sitemap.py` | 根据 `docs.json`，为仓库根目录和 `docs/phoenix/` 生成 `sitemap.xml`。 |
| `generate_spans_with_event_attributes.py` | 向本地 `:6006` 的 Phoenix 发送带自定义事件属性的合成 OTel 跨度。 |
| `seed_vendor_tool_spans.py` | 通过 `PHOENIX_SQL_DATABASE_URL` 将供应商工具示例跨度（OpenAI Responses、Google、Bedrock、Anthropic）直接插入 Phoenix 数据库。 |
| `test_axis_label_clipping.py` | 复现问题 #11312：发送具有较长模型名称的追踪记录，测试 Metrics 图表坐标轴渲染。 |
| `update_helm.py <version>` | 更新 `helm/values.yaml` 和 `helm/Chart.yaml` 中的 Phoenix 版本。 |
| `update_kustomize.py <version>` | 更新 `kustomize/base/phoenix.yaml` 中的 Phoenix Docker 镜像版本。 |

<a id="subdirectories"></a>

## 子目录

<a id="analytics"></a>

### `analytics/`

GitHub 和 PyPI 使用情况分析，见 `analytics/README.md`。需要 `GITHUB_TOKEN`。

<a id="benchmarks"></a>

### `benchmarks/`

- `hallucination_eval_benchmark.ipynb`：对幻觉评估器进行基准测试的 Notebook。

<a id="ci"></a>

### `ci/`

由 CI 工作流运行的脚本。

- `compile_openapi_schema.py`：将 Phoenix 的 OpenAPI 模式输出到文件。
- `ensure_graphql_mutations_have_permission_classes.py`：强制 Strawberry 变更操作和订阅使用 `IsNotReadOnly` / `IsNotViewer`。
- `test_helm.py`：通过异步并发全面验证 Helm chart。
- `json-canonicalization-schema/`：规范化测试的测试数据与模式。

<a id="data"></a>

### `data/`

数据整理和语料库构建（LangChain / LlamaIndex / HaluEval / MS MARCO / WikiQA / Wiki Toxic）。

- `build_langchain_vector_store.py`、`build_llama_index_*.py`：基于 Arize 文档构建向量存储。
- `convert_arize_docs_query_csv_to_jsonl.py`、`fetch_arize_documentation.py`：语料准备。
- `generate_traces.py`：发送合成 LLM 追踪记录。
- `wrangle_*.ipynb`：数据集准备 Notebook。

<a id="ddl"></a>

### `ddl/`

- `generate_ddl_postgresql.py`：从 PostgreSQL Phoenix 数据库提取 DDL，写入 `src/phoenix/db/ddl/postgresql_schema.sql`，并通过 `pglast` 验证。属于 PEP 723 脚本。
- `generate_ddl_sqlite.py`：从 SQLite Phoenix 数据库提取 DDL，写入 `src/phoenix/db/ddl/sqlite_schema.sql`，通过在新的内存数据库中重放并重新渲染进行验证。属于 PEP 723 脚本。
- 已提交的规范模式资源位于 `src/phoenix/db/ddl/`。
- `compare_schemas.py`：断言两种方言描述相同的表、列、显式创建的索引，以及 CHECK/UNIQUE/FOREIGN KEY 约束名称。每个生成器仅针对自身数据库验证，因此只有此脚本能发现两个文件之间的偏差。名称按照 PostgreSQL 的 63 字节标识符上限进行规范化，SQLite 没有此限制。排除约束支撑索引和 PRIMARY KEY 名称，因为两种方言在这些方面允许存在差异。属于 PEP 723 脚本。

<a id="dockerdevops"></a>

### `docker/devops/`

本地 Docker Compose 开发环境，包含 Phoenix、OIDC、LDAP、SMTP、Grafana、Prometheus、Toxiproxy、Vite 开发服务及 Kubernetes 清单，见 `docker/devops/README.md`。

<a id="evaluators"></a>

### `evaluators/`

针对聊天、Playground 和评估器功能的 GraphQL 冒烟测试。

- `test_chat_mutation.py`、`test_chat_subscription.py`：`chatCompletion` 变更操作与订阅。
- `test_chat_over_dataset.py`、`test_chat_over_dataset_mutation.py`：`chatCompletionOverDataset`。
- `test_create_llm_evaluator.py`：`createDatasetLlmEvaluator` 变更操作。

<a id="experiments"></a>

### `experiments/`

- `generate_multipage_experiment_data.py`：创建包含 300 个示例的实验，用于分页测试。

<a id="fixtures"></a>

### `fixtures/`

演示与手动测试使用的 Notebook 测试数据：`ChatRAG-Bench.ipynb`、`multi-turn_chat_sessions.ipynb`、`vision.ipynb`。

<a id="generate_data_via_plpgsql"></a>

### `generate_data_via_plpgsql/`

基于 PL/pgSQL 的批量数据生成，用于性能测试，见 `generate_data_via_plpgsql/README.md`。

<a id="generate_spans"></a>

### `generate_spans/`

- `generate_spans_deeply_nested.py`：发送深层嵌套跨度树。
- `generate_spans_for_time_series.py`：发送分布在不同时间的跨度，用于时间序列图表（PEP 723 脚本）。

<a id="generate_spans_for_cost_calculations"></a>

### `generate_spans_for_cost_calculations/`

- `generate_spans_for_cost_calculations.py`：发送覆盖多种模型和供应商的跨度，用于测试费用计算。

<a id="generate_spans_for_large_session"></a>

### `generate_spans_for_large_session/`

- `generate_spans_for_large_session.py`：发送单个超大会话，用于会话视图压力测试。

<a id="llm_token_pricing_tables"></a>

### `llm_token_pricing_tables/`

- `litellm_model_prices.py`：获取 LiteLLM 模型定价 JSON，输出 `model_prices.csv` 和 `model_prices_by_token_type.csv`。

<a id="mock-llm-server"></a>

### `mock-llm-server/`

模拟 OpenAI / Anthropic / Google GenAI API 的 TypeScript 服务，带实时仪表盘，见 `mock-llm-server/README.md`。

<a id="perf"></a>

### `perf/`

- `get_spans_dataframe_for_random_conversation_id.py`：从 PostgreSQL 随机抽取 `conversation_id`，再测量 `Client.spans.get_spans_dataframe` 耗时。
- `postgres/postgres_explain_analyze.py`：对 `paste_queries_here.sql` 中的查询运行 `EXPLAIN ANALYZE`（PEP 723 脚本）。

<a id="prompts"></a>

### `prompts/`

- `compile_python_prompts.py`：将 YAML 提示词编译为 Python。
- `compile_typescript_prompts.py`：将 YAML 提示词编译为 TypeScript。

<a id="rag"></a>

### `rag/`

- `plotresults.py`：RAG 检索评估的绘图辅助脚本。

<a id="testing"></a>

### `testing/`

面向运行中 Phoenix 实例的冒烟测试。

- `dataset_upsert_smoke.py` / `.ts`：端到端测试数据集的更新或插入、更新流程。
- `experiment_runs_filters.ipynb`：交互式探索筛选器。
- `send_spans.py`：发送合成 OpenInference 跨度。

<a id="ts-span-generator"></a>

### `ts-span-generator/`

用于生成确定性且具有真实感的智能体追踪数据的 TypeScript 工具：事故调查对话包含逐渐增长的 LLM 消息历史（2→20 条）、带 JSON 参数和结果的工具调用，以及便于测试搜索的近似词汇。通过 `@arizeai/phoenix-otel` 使用 OTLP 发送到运行中的 Phoenix，见 `ts-span-generator/README.md`。

<a id="uv"></a>

### `uv/`

- `type_check`：由 Make 类型检查目标调用的包装脚本。

<a id="running-scripts"></a>

## 运行脚本

```bash
# In the project venv
uv run python scripts/<path>/<script>.py

# PEP 723 scripts (declare their own deps inline) work standalone
uv run scripts/ddl/generate_ddl_postgresql.py
uv run scripts/ddl/generate_ddl_sqlite.py
uv run scripts/generate_spans/generate_spans_for_time_series.py
uv run scripts/perf/postgres/postgres_explain_analyze.py
```

大部分跨度生成脚本假定可通过 `http://localhost:6006` 访问 Phoenix；直接访问数据库的脚本读取 `PHOENIX_SQL_DATABASE_URL`。
