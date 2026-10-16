<a id="pxi-evals"></a>

# PXI 评估

本目录是 PXI 专用评估工作的权威入口。评估框架将使用真实模型的 PXI 服务端评估作为 Phoenix 实验运行。

<a id="layout"></a>

## 目录结构

- `harness/` 针对 Phoenix 数据集运行真实 PXI Agent 实验。
- `datasets/` 存储评估框架与 CI 工作流共享的 YAML 数据集。
- `evaluators/` 存储基于 `(output, expected)` 对的实验评估器。
- `online_evals/` 评估已接收的 PXI 追踪并添加标注。
- `trace_ingest/` 为未来的追踪转数据集工具预留。

评估框架和评估器的快速单元测试位于 `tests/unit/pxi/evals/`。

<a id="online-production-evals"></a>

## 生产环境在线评估

在线运行器在数据接收后评估近期 PXI span。它使用标注作为检查点：在补全追踪数据或调用评估器前，跳过已经带有该评估器标注名称和标识符的目标。默认 48 小时重叠窗口可补偿遗漏的计划运行，同时避免重复评估同一目标。

追踪评估器位于 `evals/pxi/online_evals/evaluators/`；运行 CLI 并传入 `--help` 可列出当前已注册的评估器。它们与 `evals.pxi.evaluators` 保持分离，因为后者实现基于 `(output, expected)` 对的实验契约，而在线评估器接收补全后的 `(target_span, trace_spans)` 对，并为目标 span 添加标注。

每个评估器声明一个 `SpanSelector`；选择器相同的评估器共享发现查询：

- **根目标** — `tool_count_per_turn` 和 `user_friction` 选择 `names=("pxi.turn",)`、`span_kinds=("AGENT",)`、`parent_id="null"`，因此它们为每条追踪中的一个轮次根节点评分并添加标注，且共享一次查询。
- **TOOL 目标** — `suggestion_accepted` 根据审批属性 `pxi.approval.source="user"` 和 `span_kinds=("TOOL",)` 选择目标，不限制父节点，因此可标注轮次内任意位置的独立工具 span。它不指定任何工具名称。

采样以 `trace_id` 为键，因此同一轮次内的所有目标会一起被采样。

所有 LLM 评估器共享同一套裁判配置：`PHOENIX_AGENTS_EVALS_PROVIDER` / `PHOENIX_AGENTS_EVALS_MODEL`，默认使用 OpenAI `gpt-5.5`。支持的提供方为 `openai`（`OPENAI_API_KEY`）、`anthropic`（`ANTHROPIC_API_KEY`）和 `google`（`GOOGLE_GENERATIVE_AI_API_KEY`）。未知提供方名称或缺少对应 API 密钥时，会在启动阶段、发现追踪之前一次性报错。

评估器接收追踪结构的输入，并将结果作为 span 标注附加至目标 span。运行器不创建或更新项目标注配置；如需显示或优化元数据，请在 Phoenix 中单独配置。

<a id="suggestion_accepted"></a>

### `suggestion_accepted`

这是一个确定性的 CODE 评估器，用于记录需审批的 PXI 建议所对应的人工决策。由于一个轮次可能包含多个决策，它会分别标注每个 TOOL span。

| 记录结果 | 标注 |
|---|---|
| `pxi.approval.decision = "rejected"` | `rejected` / `0.0` |
| `pxi.approval.decision = "accepted"` | `accepted` / `1.0` |
| 其他情况 | *不添加标注* |

需审批的工具会在输出中添加 `approval: {decision, source}`。服务端将其提升为 `pxi.approval.decision` 和 `pxi.approval.source`，供评估器发现目标并分类。

评估器不会标注以下情况：

- 自动接受（`pxi.approval.source: "auto"`，即绕过编辑权限）；
- 仍待审批、取消或出错的工具，均不作标记；
- 未知或格式错误的决策。

标注仅包含 `{"tool_name": ...}`。发现过程不依赖工具名称允许列表，因此新工具只要输出该标记即可被覆盖。

在该标记发布前记录的 span 无法被发现或回填。

`submit_code_evaluator_draft` 和 `submit_llm_evaluator_draft` 的对话框决策未写入工具输出，因此尚未被衡量。在 [#15033](https://github.com/Arize-ai/phoenix/issues/15033) 解决前，接受率和拒绝率均排除这两个工具。

预览而不写入任何内容：

```bash
PHOENIX_PROJECT=pxi_dev \
uv run python -m evals.pxi.online_evals.run --eval suggestion_accepted --dry-run
```

标注标识符是评估器专用、带版本的检查点。评估器的评分语义或评分准则变化时，应递增其 `vN` 标识符；下一次重叠运行会以新标识回填近期目标，同时保留之前的结果序列。运行器会为每个 LLM 评估器标识符追加 `provider:model`，因此更换裁判会自动生成独立的结果序列。检查点仅依据运行器自身评估器的标注名称；人工反馈和其他标注绝不会阻止运行。

采样具有确定性，且仅以追踪为键：采样率相同的评估器选择完全相同的追踪，低采样率评估器的选择是高采样率选择的严格子集，因此被采样的追踪不会仅获得部分标注。

使用标准 Phoenix 客户端环境变量在本地运行：

```bash
PHOENIX_PROJECT=pxi_dev \
uv run python -m evals.pxi.online_evals.run --dry-run
```

运行器等待五分钟后才认为目标已稳定，默认评估所有适用目标，并发执行评估（最多 8 个处理中任务），避免串行调用 LLM 裁判。评估器异常仅影响该目标：记录日志、计入汇总中的 `errors`，然后继续运行（进程以非零状态退出，使计划运行能够暴露失败）。结构性追踪异常（工具 span 并非轮次根节点的后代、祖先缺失、存在环）会明确报错：稳定后的追踪应当完整，因此异常表示 span 丢失或追踪回归，而非可跳过的轮次。如果实际使用中这类告警过于频繁，再评估是否降级为警告并跳过。

计划工作流每天在 UTC 00:17 和 12:17 运行两次，也可手动启动。上述 CLI 入口可随时在本地运行。工作流日志仅包含聚合计数，不包含追踪输入或输出。

计划任务的裁判配置来自 GitHub 仓库变量 `PHOENIX_AGENTS_EVALS_PROVIDER` 和 `PHOENIX_AGENTS_EVALS_MODEL`，默认值为 `openai` 和 `gpt-5.5`。将对应提供方凭证存入同名 Actions secret（工作流目前映射了 `OPENAI_API_KEY` 和 `ANTHROPIC_API_KEY`；接入其他提供方时需新增映射）。Phoenix 和提供方凭证仅对最终评估步骤开放。

初始计划任务项目为 `pxi_dev`。Phoenix Cloud 生产 PXI 追踪位于 `pxi_phoenix_cloud`；仅在使用新格式开发追踪验证运行器后，才应添加该项目。

<a id="adding-an-online-evaluator"></a>

### 添加在线评估器

评估器是一个异步函数，接收一个目标 span 及其追踪中所有已补全的 span。它返回 `phoenix.evals` 的 `Score`，目标不适用时返回 `None`：

```python
from collections.abc import Sequence

from phoenix.client.__generated__ import v1
from phoenix.evals.evaluators import Score


async def evaluate(target: v1.Span, spans: Sequence[v1.Span]) -> Score | None:
    if not spans:
        return None
    return Score(score=1.0, label="example", explanation="why")
```

声明一个 `EvaluatorSpec`，包含名称、选择器、评估函数、标注者类型、采样率和带版本的标识符。轮次级评估器使用 `PXI_TURN_ROOT_SELECTOR`。标注者类型控制裁判凭证校验和模型专用检查点。LLM 评估器（`annotator_kind="LLM"`）自动共享 `evals/pxi/online_evals/judge.py` 中的裁判配置：运行器在启动时校验裁判凭证，并为其检查点标识符追加 `provider:model`。

在 `evals/pxi/online_evals/evaluators/__init__.py` 注册该规范，并在 `tests/unit/pxi/evals/online_evals/` 添加有针对性的测试。运行器级测试应断言持久化标注的精确结构，以及与该评估器相关的失败、不适用、采样和检查点行为。

<a id="run-locally"></a>

## 本地运行

评估框架构建生产环境的只读 MCP 目录，其中包括 PXI 技能，以及服务端 bash 工具。技能、参考资料和目录发现均正常执行。对 `bash` 和 MCP `execute` 的调用与浏览器操作一样会被延迟：这些示例仅评分下一步请求的操作，不对应用数据实际执行。评估框架不会启动 Phoenix 数据库或沙箱工作进程。缺少后端工具或技能目录时，会在请求模型前失败，并报告为任务错误，而非行为未达标。

有两种方式运行评估：

- **pytest 测试套件**（`pytest evals/pxi -c evals/pxi/pytest.ini`）是 CI 执行并作为通过检查依据的入口，参见 [Pytest 评估框架与聚合通过检查](#pytest-harness-and-aggregate-gate)。
- `evals/pxi/harness/run_experiment.py` 是单数据集运行器，提供最丰富的本地失败输出（在终端显示每个示例的完整报告），仍是手动调试单个数据集的最佳方式。

通过 `run_experiment.py` 运行单个数据集时，先启动 Phoenix，再执行：

```bash
uv run python evals/pxi/harness/run_experiment.py --dataset set_spans_filter
```

运行应用内链接测试套件：

```bash
uv run python -m evals.pxi.harness.run_experiment --dataset in_app_links
```

默认调用运行 `regression` 划分。手动实验可使用 `--splits`：

```bash
uv run python -m evals.pxi.harness.run_experiment --dataset set_spans_filter --splits dev val
```

仅当评估器在 `regression` 示例上失败时，`--fail-on-regression` 才以非零状态退出。运行器会在标准输出打印汇总及 Phoenix 实验 URL。

<a id="failure-reports"></a>

## 失败报告

控制台汇总保留紧凑、截断的表格，便于快速浏览。如需完整输出，可使用以下两个标志：

<a id="--print-report-local-use"></a>

### `--print-report`（本地使用）

传入 `--print-report`，可在运行结束时将完整 Markdown 失败报告输出至标准输出。全部示例通过时不执行任何操作。

```bash
uv run python -m evals.pxi.harness.run_experiment \
  --dataset set_spans_filter --print-report
```

这是在本地查看完整失败详情的推荐方式：输入、预期输出、Agent 实际工具调用、各评估器的分数、标签、解释及 Phoenix 追踪链接，均集中显示在终端，无需写入文件。

<a id="--report-dir-dir-artifact-use"></a>

### `--report-dir DIR`（产物使用）

传入 `--report-dir`，每次数据集运行会写入两个文件：

- **`<dataset>.report.json`** — 机器可读：包含运行元数据（实验名称和 URL、Git SHA/分支、模型、提供方、划分、时间戳），以及每个*未通过或出错*示例的记录，保留完整且未截断的 `input`、`expected`、`actual_output`（含 Agent 的每次工具调用）、各评估器的分数、标签、解释、错误及任何 `task_error`；若该次运行已追踪，还包含每个示例的追踪 URL（`<base-url>/redirects/traces/<trace_id>`）。通过的示例仅计入数量。
- **`<dataset>.report.md`** — 以适合 Agent 阅读的 Markdown 提供相同内容：顶部汇总表、每个失败示例的独立章节（消息历史折叠于 `<details>`），以及包含精确本地命令的复现页脚。整份报告由哨兵标记包围（`===== BEGIN PXI EVAL REPORT: <dataset> =====` / `===== END ... =====`），便于从 CI 日志中搜索提取。可直接将其粘贴给编码 Agent 诊断并修复失败，报告已包含完整上下文。

这些文件是单数据集最完整的本地产物。CI 本身不再调用 `run_experiment.py`，而是运行 pytest 套件和通过检查（参见 [CI](#ci)），并渲染自己的报告。两条路径以相同方式嵌入日志内容：GitHub Actions 会将任何以 `::` 开头的行解释为工作流命令（例如 `::endgroup::` 关闭日志组，`::error::` 创建标注），因此工作流先将报告写入文件，再在 `::stop-commands::` 块中使用 `cat` 输出，以在记录日志期间暂停命令处理。完整模式参见 `.github/workflows/pxi-evals.yml`。

若报告超过 GitHub 嵌入限制（步骤摘要约 1 MiB，每行日志约 64 KiB），Markdown 层会回退为摘要和 JSON 产物链接；JSON 文件绝不截断示例数据。两层均会有意遮蔽一项内容：pydantic_ai 在 `messages[].instructions` 中重复的静态系统提示词（每次模型请求约 55 KB）会替换为占位符，因为它属于产品提示词，而非示例数据；完整文本始终可通过追踪 URL 查看。

上传任何内容之前，运行器会检查已配置 Phoenix URL 的 `/healthz`（默认 `http://localhost:6006`，如设置了 `PHOENIX_COLLECTOR_ENDPOINT` / `OTEL_EXPORTER_OTLP_ENDPOINT` 则使用对应值）。使用共享 Phoenix 端点时：

```bash
export PHOENIX_COLLECTOR_ENDPOINT=https://your-phoenix.example.com
export PHOENIX_API_KEY=...
uv run python evals/pxi/harness/run_experiment.py --dataset set_spans_filter
```

任务错误（异常类型和截断消息，不含堆栈）会作为实验任务输出的一部分上传至 Phoenix。针对共享 Phoenix 调试时，避免将凭证粘贴进请求 URL。

任务输出保存 PXI Agent 运行中序列化的 Pydantic AI 消息。工具评估器从这些消息中读取 `tool-call` 部分，因此工具选择和工具参数检查覆盖轮次内发出的每次工具调用。

<a id="pytest-harness-and-aggregate-gate"></a>

## Pytest 评估框架与聚合通过检查

整个数据集目录也以参数化 pytest 测试运行，每个示例对应一个 `@pytest.mark.phoenix` 测试项，记录至 Phoenix 实验。测试本身不作断言：它们将每个 `(example, evaluator)` 的一个数据点写入 schema-4 JSON 产物，由独立通过检查根据 `thresholds.yaml` 判断通过或失败。原始行保留稳定的 pytest 节点 ID 和评估器证据。聚合 `scored`/`assessed` 计数仅包含数值型评估器判定；提供方、设置和评估器错误单独计入 `infra`。任务错误（Agent 运行未产生任何输出）与明确的行为未达标一样获得一次重试，因为两者都没有提供可靠信号；若任务错误再次出现，则报告为重复任务错误，仍不进入通过率分母。这就是 CI 的运行方式。

```bash
# 运行回归划分并写入 pxi-eval-results.json
uv run pytest evals/pxi -c evals/pxi/pytest.ini -m regression

# 判定通过或失败（违反阈值或运行无效、不完整时以非零状态退出）
uv run python -m evals.pxi.gate pxi-eval-results.json --thresholds evals/pxi/thresholds.yaml
```

CI 的两次尝试流程会规划精确的节点 ID，仅重跑这些节点并写入第二份产物，然后对两次尝试中同一评估器的判定进行对账。按与 CI 完全相同的方式端到端运行：初始产物写入独立路径，重试前将节点 ID 重新定位到 pytest 的 rootdir，且仅在规划实际生成节点 ID 时重试：

```bash
# 1. 初始运行写入独立产物。
PXI_EVAL_RESULTS_PATH=pxi-eval-results-initial.json \
  uv run pytest evals/pxi -c evals/pxi/pytest.ini -m regression

# 2. 规划：写入检查单元格中可评估未达标的节点 ID（若没有此类节点，
#    或运行无法衡量，则生成空文件）。
uv run python -m evals.pxi.gate pxi-eval-results-initial.json \
  --thresholds evals/pxi/thresholds.yaml \
  --retry-nodeids-out pxi-eval-retry-nodeids.txt

# 3. 仅重试这些节点（若有），写入第二份产物，然后对账。
#    gate.py 输出相对于 evals/pxi 的节点 ID（使用
#    `-c evals/pxi/pytest.ini` 时的 pytest rootdir）；从仓库根目录运行前，
#    先将其重新定位到该路径，否则 pytest 将收集不到测试项。
if [[ -s pxi-eval-retry-nodeids.txt ]]; then
  mapfile -t bare_nodeids < pxi-eval-retry-nodeids.txt
  retry_nodeids=("${bare_nodeids[@]/#/evals/pxi/}")
  PXI_EVAL_RESULTS_PATH=pxi-eval-results-retry.json \
    uv run pytest -c evals/pxi/pytest.ini "${retry_nodeids[@]}"
  uv run python -m evals.pxi.gate pxi-eval-results-initial.json \
    --thresholds evals/pxi/thresholds.yaml \
    --retry-artifact pxi-eval-results-retry.json
else
  # 无需重试：初始运行已判定通过或失败。
  uv run python -m evals.pxi.gate pxi-eval-results-initial.json \
    --thresholds evals/pxi/thresholds.yaml
fi
```

`--retry-nodeids-out`（规划）和 `--retry-artifact`（对账）是该流程中互斥的两个阶段，同时传入会报错，因此已复现的未达标结果不会因意外重新进入规划模式而漏过。任何调用都可传入 `--decision-out decision.json`，额外将结构化判定（`kind`、`label`、`exit_code`、`retry_nodeids`、计数）输出为 JSON；CI 读取该文件，无需抓取 Markdown 摘要。

`pytest.ini` 是完整、独立的配置：`pytest -c <file>` 会替换根配置，而非继承它，因此该文件声明评估运行所需的全部设置（异步模式、会话循环作用域、导入模式、划分标记），并省略根测试套件的 `--doctest-modules`。设置 `PXI_EVAL_RESULTS_PATH` 可控制产物写入位置（默认是当前目录的 `pxi-eval-results.json`）。

<a id="thresholds"></a>

### 阈值

`thresholds.yaml` 为每个划分设置最低通过率，并允许按数据集或评估器覆盖。数据集可能包含的每个划分（`regression`、`dev`、`holdout`、`val`）均已枚举：如果某个 `(evaluator, split)` 数据点没有匹配策略，也未明确设置 `gating: false`，则视为违规，不能静默通过。回归划分必须达到 100%；`dev`/`holdout` 较宽松；`val` 仅记录，不影响通过检查。放宽阈值会降低检查标准，应在 PR 描述中明确说明，不要与无关修改混在一起。

通过检查还会对**无法衡量的运行采取默认拒绝**，以状态码 2 退出：产物缺失、格式错误、不完整或含有脏数据；定向重试遗漏或新增节点 ID；检查单元格没有可评估行；或检查单元格中的代码**评估器自身抛出异常**（`evaluator_error`，属于评分工具缺陷，绝不重试，也不会通过静默排除而变成通过）。这些结果标记为无法衡量，而非回归。设置 `PHOENIX_API_KEY` 时（即 CI），如果插件未记录任何内容，通过检查也默认拒绝：插件会将初始化失败降级为警告，因此缺少此检查时，绿色结果可能意味着“未向 Phoenix 记录任何内容”。没有密钥的本地运行跳过此检查，因为本地记录是可选的。

需要重试的示例数超过 `--retry-cap`（默认 15）后，通过检查完全跳过重试确认，仅依据第一次尝试作出判断：该规模表明失败具有结构性，逐个确认只会延迟本已确定的结果。若超限由违反阈值的行为**未达标**触发，则报告为**失败过多，无法逐项确认**（退出码 1，区别于逐示例确认的回归）。若超限由未解决的**任务错误**触发，即大多数示例未产生可评估结果，则属于**无法衡量**（退出码 2），绝不能通过：少量通过行不能代表大部分未实际完成的运行。

另外两种结果可防止已复现的未达标被绿色总状态掩盖。如果两次尝试均复现未达标，但通过率仍达到或超过小于 1.0 的覆盖阈值，则标记为**通过但存在容忍的未达标**（退出码 0），以保留其可见性。如果第一次尝试是任务错误，仅重试产生未达标，则**不**属于已确认回归：它只有一次可评估尝试，并非相同未达标出现两次，且唯一一次重试已用完，因此记录为不可评估，不会使通过检查变红。这些低于 1.0 的回归阈值覆盖是有意采用的临时措施（参见 `thresholds.yaml`）；计划在语料重新建立基线（使用发布的默认模型，k≥3）且每个稳定失败均已处理后，逐步恢复严格的 `1.0` 默认值：重试确认在衡量层吸收波动，持续不稳定的示例明确隔离至不参与通过检查的划分，而不是通过数值余量容忍。阈值系统本身保留，继续作为划分默认值、dev/holdout 宽松策略和 `gating: false` 隔离的策略层。逐步收紧属于后续语料和策略步骤，不在此次衡量语义变更范围内。

<a id="regression-gate-vs-full-collection-sync"></a>

### 回归通过检查与完整收集同步

传入的标记决定以下取舍：

- **`-m regression`** 仅运行回归划分。phoenix-client 插件将按标记过滤的运行视为部分收集，仅向 Phoenix 数据集**追加**内容，不清理已删除的示例。这是成本较低的 PR 检查。
- **不传标记**（`pytest evals/pxi -c evals/pxi/pytest.ini`）表示完整收集：插件更新同步数据集，并**清理** YAML 中已不存在的示例。合并后在 `main` 上运行，以保持 Phoenix 数据集的权威性；它会运行每个划分的真实模型示例，因此成本高于回归检查。

<a id="model-configuration"></a>

## 模型配置

任务使用 Phoenix Agent 环境变量选择模型：

```bash
export PHOENIX_AGENTS_ASSISTANT_PROVIDER=OPENAI
export PHOENIX_AGENTS_ASSISTANT_MODEL=gpt-5.4
```

提供方凭证从常规提供方环境变量读取，例如 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`。

文档 MCP 工具集遵循与 Phoenix 服务端相同的生产启用条件：Agent 助手不能被禁用，且必须允许外部资源。助手默认启用；外部资源需要显式开启：

```bash
export PHOENIX_ALLOW_EXTERNAL_RESOURCES=true
```

任一条件未满足时，实验仍会运行，但 Agent 不会获得文档 MCP 工具。

<a id="datasets"></a>

## 数据集

数据集位于 `evals/pxi/datasets/*.yaml`。每个文件包含：

- `dataset_name`
- 可选的 `description`
- `evaluators`
- `examples`

每个示例需要稳定的 `id`、列表形式且恰好包含一个划分的 `splits` 字段，以及符合评估器要求的 `input`、`expected` 和 `metadata` 结构。当前工具调用评估器的示例通常使用 `input.messages`、`expected.tools`，并在 `expected.tool_call_args` 中存放预期工具参数。浏览器操作接口后的行为通过 `expected.ui_operations`（必需或禁止的操作名称，与实际 `execute_browser_action` 脚本中的 `ui.<name>(...)` 调用匹配）和 `expected.ui_operation_args`（将相同匹配器词汇用于调用参数源码）进行断言。

由于 `search_browser_actions` 和 `execute_browser_action` 是外部工具，Agent 发出其中第一个调用时，该次运行便结束。因此，对操作选择或参数评分的示例会在 `input.messages` 中预置发现步骤：包含助手的 `search_browser_actions` 调用，以及携带按真实 `renderUIOperationCatalog` 格式渲染的目录片段的工具返回。这样 Agent 从循环中途恢复时已持有目录，被评分的步骤就是它接下来生成的 `execute_browser_action` 脚本。针对新轮次的负向示例不进行预置。

示例 ID 必须唯一，因为运行器使用它们进行稳定的 upsert。回归示例使用 `splits: [regression]`。

每个数据集示例都必须声明列表形式的 `splits: [...]`，即使它只属于一个划分：

```yaml
examples:
  - id: llm-spans
    splits: [regression]
    input:
      messages:
        - role: user
          content: Show me only LLM spans.
```

划分含义：

| 划分 | 规模 | 用途 |
| --- | --- | --- |
| `regression` | 较小，10—50 个示例 | 快速留出回归检查；评估框架默认使用。 |
| `dev` | 较大，约 100 个以上示例 | 手动实验、消融实验和失败分析。 |
| `val` | 较小，10—50 个示例 | 优化器评分信号。 |
| `holdout` | 任意规模 | 保留为留出测试集，用于最终比较和泛化测试。 |

每个示例恰好属于一个划分。运行器将 YAML `splits` 列表原样传递至 Phoenix 客户端上传载荷。

<a id="inputs"></a>

## 输入

新 fixture 应使用 `GET /v1/agent_sessions/{session_id}/messages` 返回的公共 `PhoenixUIMessage` 对话记录。它是存储的对话产物。聊天 POST 现在会向服务端管理的会话发送新消息或工具输出，因此 fixture 并非字面意义上的 POST 请求体。

```yaml
input:
  messages:
    - id: user-1
      role: user
      parts:
        - type: text
          text: Keep the error filter, but only show root spans.
      metadata:
        phoenix:
          type: user
          currentDateTime: "2026-04-03T12:00:00-07:00"
          timeZone: America/Los_Angeles
          editPermission: manual
          uiContexts:
            project:
              type: project
              projectNodeId: UHJvamVjdDoxMg==
              spanFilter: "status_code == 'ERROR'"
```

已完成的工具调用及其输出一起存放于助手消息部分：

```yaml
- id: assistant-1
  role: assistant
  parts:
    - type: tool-search_browser_actions
      toolCallId: search-1
      state: output-available
      input: {query: filter the spans table}
      output: "<the public browser operation catalog>"
```

对话记录必须以用户消息或已完成的工具输出结束。待处理调用和审批会被拒绝。使用合成标识符和结果；不要提交私有生产对话。在每个用户轮次的元数据中保留其 UI 状态和浏览器时钟。生产适配器会在对应轮次渲染变化的状态，并保留结构化工具结果。

已有数据集可以保留紧凑的 `role/content/tool_calls` 写法。fixture 编译器将每个工具返回与其调用配对，将结果校验为 `PhoenixUIMessage`，再使用与生产环境相同的对话适配器。工具 `content` 可以是对象。尤其是 `bash` 会返回 `command`、`stdout`、`stderr`、`exitCode`、耗时、字节数和截断标志。原始 GraphQL JSON 应位于 `stdout` 内，而非工具结果顶层。

对于紧凑 fixture，`input.contexts` 使用公共上下文联合类型，描述当前用户轮次。省略上下文表示没有页面上下文，不会隐式指定项目。不要混用顶层上下文和按轮次存储的 UI 状态。

优先断言公共 UI 操作参数、最终过滤谓词、链接和产物。除非发现顺序本身就是待测行为，否则不要断言特定顺序。目录片段仍然只隔离一个步骤，无法验证针对完整浏览器目录的发现。这些离线评估在延迟操作处停止，无法证明脚本已运行、数据库查询已成功，或 UI 变更已产生预期状态；这些结果由浏览器 E2E 测试覆盖。脚本参数提取和工具调用预算仍属于依赖实现的检查，应谨慎使用。

`test_agent_task_inputs.py` 通过当前公共消息模型和生产适配器校验每个 fixture，并根据已发布的结果 schema 检查预置 bash 结果，从而在真实评估消耗 token 前发现传输格式漂移。

<a id="matcher-vocabulary"></a>

## 匹配器词汇

`tool_call_args_match` 评估器使用子集语义比较预期参数和实际参数（忽略实际参数中多余的键）。相同词汇也适用于 `expected.ui_operation_args[<operation>]`，以文本方式匹配实际 `execute_browser_action` 脚本中 `ui.<operation>(...)` 调用的 JavaScript 参数源码（字面量会断言键和值出现在源码中）。每个预期值要么是字面量（通过 `==` 比较），要么是**匹配器对象**，即所有顶层键均来自以下词汇的字典：

| 匹配器 | 含义 |
|---|---|
| `equals: <value>` | 显式相等，与直接使用字面量相同。 |
| `contains_all: [<str>, ...]` | 实际值必须是包含所有子字符串的字符串。用于不依赖子句顺序的 DSL 匹配（`["span_kind == 'LLM'", "latency_ms >= 5000"]` 接受任意顺序）。 |
| `contains_any: [<str>, ...]` | 实际值必须是包含至少一个子字符串的字符串。 |
| `not_contains: [<str>, ...]` | 实际值必须是完全不包含这些子字符串的字符串。 |
| `any: true` | 实际参数中必须存在该键，值不受约束。 |
| `non_empty: true` | 该键必须存在，且包含非空白文本。 |
| `absent: true` | 实际参数中不得存在该键。 |

若要完全不约束某个参数，只需在 `expected` 中省略它，子集匹配会忽略未提及的实际键。仅在键是否存在本身重要时使用 `any: true`；需要字符串内容时使用 `non_empty: true`；省略本身就是待测行为时使用 `absent: true`。

对于关注效率的示例，添加 `expected.budgets.max_tool_calls` 并启用 `tool_call_count_within_limit` 评估器。当只读示例必须允许不同准备路径时，改用 `expected.budgets.max_repeated_tool_calls`。重复调用指工具名称和 JSON 参数与评分输出中先前调用相同，对象键顺序和调用 ID 不影响判断。第一个匹配调用之后的每次调用均计入上限。不同技能和修正后的参数不算重复。若同时提供两种限制，则同时生效。

仅当再次执行相同请求不会增加新信息时，才使用零重复预算。它不能替代延迟或总成本衡量，也无法检测参数不同但不必要的调用。优先使用 bash 的示例可通过 `bash_command_substrings_match` 检查命令意图，无需要求精确的 shell 语法。

<a id="manual-ci"></a>

## 手动 CI

`expected.tools` 还可包含 `exact_match: true`，将 `correct_tools_called` 从“必须调用所有必需工具”切换为“实际工具序列必须与要求的序列完全一致”（无额外调用、无重复、顺序相同）。

`expected.tool_call_args` 为每个工具名称保存一个预期参数映射，或一组可接受参数映射。匹配有意在以下三个方面保持宽松：

1. **单次调用使用子集匹配。** 当*所有*预期 `(key, value)` 对均存在时，调用即通过；实际调用可以包含数据集中未提及的额外参数键。
2. **多次调用任一匹配即可。** 同一工具在一个轮次被调用多次时，只要其中*任意一次*满足预期键值对，检查即通过。
3. **预期结构支持多种变体。** 工具有多个预期参数映射时，任意变体满足即可。

字面量通过 `==` 比较。如需不依赖顺序的字符串匹配，使用上述匹配器词汇。例如 `contains_all: ["span_kind == 'LLM'", "latency_ms >= 5000"]` 接受任意子句顺序，但不会让所有字符串字面量都忽略顺序。虽然子集匹配通常允许额外实际键，但对于必须省略的键，应使用 `absent: true`。

工具和操作参数键必须与精确的输入 schema 一致，包括 camelCase。对于 `spansFilter.set`，这意味着 `condition`，而且仅有 `condition`，因为根 span 作用域在过滤 DSL 内表达（`parent_id is None`），不是独立参数。

<a id="evaluators"></a>

## 评估器

代码评估器位于 `evals/pxi/evaluators/`，使用 `phoenix.evals` 的 `@create_evaluator(name=..., kind="code")`。实验评估器可绑定 `output`、`input`、`expected` 和 `metadata`。简单的 `bool`、`int` 或 `float` 返回值会转换为 Phoenix 分数；字典返回值可包含标签、解释和调试元数据。

<a id="what-belongs-here"></a>

## 适用范围

对于可从服务端管理的 Agent 输出中衡量、面向模型的 PXI 行为，使用 Python 服务端评估，包括工具选择和延迟工具参数。当行为依赖浏览器渲染、前端分发、页面状态切换或视觉/UI 断言时，使用 Playwright。

<a id="ci"></a>

## CI

`PXI Evals` GitHub Actions 工作流针对 Phoenix Cloud 运行真实回归评估。修改 `evals/**` 或 `src/phoenix/server/agents/**` 的 PR 会触发它；维护者也可从 Actions 选项卡手动运行。

在 PR 上，作业运行 `pytest evals/pxi -c evals/pxi/pytest.ini -m regression` 以记录初始产物。随后通过检查为检查单元格中可评估的未达标和任务错误输出精确节点 ID。仅这些节点再运行一次，写入独立重试产物，最终检查对两份产物进行对账。重试通过表示绿色的**不稳定失败恢复**。退出码 1 要求同一评估器的未达标在两次尝试中均可评估，且对账后单元格违反固定阈值；重复任务错误报告为无法衡量，绝不视为回归。即使 pytest 以非零状态退出，通过检查也会运行，因此崩溃或不完整运行会以状态码 2 退出，不会被当作通过或伪装成 Agent 回归。

手动 `workflow_dispatch` 运行接收 `mode` 输入：

- `regression`（默认）— 与 PR 作业相同的回归通过检查。
- `full` — 完整收集运行（不按划分过滤），以清理同步方式更新 Phoenix 数据集，删除 YAML 中已不存在的示例。数据集变更合并后，在 `main` 上触发；它会运行每个划分的真实模型示例，因此成本高于回归检查。

<a id="reading-a-ci-failure"></a>

### 解读 CI 失败

失败输出通过三个渠道发布，按开发者或编码 Agent 的使用方式排序：

1. **作业日志（主要供 Agent 使用）。** 通过检查失败时，报告嵌入日志中的折叠组 `PXI EVAL REPORT (agent-readable)` 和 `::stop-commands::` 块。报告列出每个已确认失败、不稳定失败和基础设施问题示例；包含两次尝试的评估器标签、分数和解释；保留 pytest 节点 ID；链接初始及重试 Phoenix 实验；还包含对账后每个单元格的分母和策略。从失败检查获取报告只需两条命令：

   ```bash
   gh pr checks <pr-number>           # 从 URL 获取失败运行的 ID
   gh run view <run-id> --log-failed  # 适合 Agent 阅读的报告
   ```

   点击摘要中的任一 Phoenix 链接，即可查看完整输入、Agent 输出、工具调用、标注和追踪。摘要本身即可交给编码 Agent，无需从原始日志重建各次尝试的示例归属。
2. **步骤摘要（供开发者使用）。** 运行摘要页显示通过检查判定，并在 `<details>` 块中提供相同报告，便于从浏览器复制粘贴。
3. **产物（供程序使用）。** 每次运行都会将初始产物、可选重试产物、精确重试节点列表和渲染后的摘要上传为 `pxi-eval-reports-<run-id>` 产物：

   ```bash
   gh run download <run-id> -n pxi-eval-reports-<run-id>
   ```

<a id="static-filter-predicate-comparisons"></a>

### 静态过滤谓词比较

`condition: {filter_equals: "span_kind in ['LLM', 'TOOL']"}` 使用 Python DSL AST 比较解码后的 `ui.spansFilter.set` 条件。它接受引号和空白变化、AND/OR 子句重排以及等价的字面量成员列表；拒绝缺失或额外谓词，并保留 AND 与 OR 的区别。

该匹配器支持一次无条件操作，参数可为字符串字面量或 `const` 字符串绑定，包括简写属性、注释、静态模板及调用后的 UIResult 返回保护。动态表达式、条件调用和多次过滤调用均默认拒绝。脚本绝不执行。其他匹配器保留现有子字符串语义；它不是完整的 JavaScript 或语义过滤评估器。
