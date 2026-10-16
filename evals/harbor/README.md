<a id="harbor-evaluations-for-phoenix"></a>
# Phoenix 的 Harbor 评测

这些基准测试比较 Agent 与 Phoenix 交互的不同方式。它们使用
[Harbor](https://github.com/laude-institute/harbor) 构建环境、运行各个 Agent 并验证结果。
`arize-phoenix` Harbor 插件将每次运行作为数据集、实验、分数和追踪记录到配置的
Phoenix 实例中。你可以在 Phoenix 界面中比较各个实验条件。

| 作业文件 | 回答的问题 | 任务 | Phoenix 数据集 |
| --- | --- | --- | --- |
| `jobs/regression.yaml` | PXI 或使用 MCP 服务端或 px 的 Claude Code，能否完成多步骤错误分析，并通过爬山优化改进提示词？CI 会运行此基准。 | `tasks/regression/*` | `regression` |
| `jobs/trail-benchmark-dev.yaml` | 哪种 Phoenix 接口（MCP 服务端、px CLI 或 PXI）能最准确地回答相同的项目问题，其成本是多少？ | `tasks/trail-benchmark-dev/*` | `trail-benchmark-dev` |

| 路径 | 内容 |
| --- | --- |
| `agents/` | PXI，以及供 MCP 服务端和 px 使用的 Claude Code 或 Codex 配置 |
| `environments/` | 共享 Dockerfile，以及各数据库的测试数据准备脚本 |
| `jobs/` | 每个基准测试对应一个配置文件 |
| `tasks/` | 每个基准测试对应一个目录：任务分别位于 `regression/` 和 `trail-benchmark-dev/` 下 |
| `verifiers/` | `harbor_verifiers` 包：包含回复评分器、LLM 裁判和参考解答查询辅助函数，以 wheel 形式安装在镜像中 |
| `scripts/` | 用于暂存任务、构建 px 归档、选择作业子集和检查 CI 奖励的脚本 |

<a id="prerequisites"></a>
## 前置条件

- 安装 Python 3.12 或更新版本，并运行 `uv pip install "arize-phoenix-client[harbor]"`。
- 本地运行需安装 Docker；也可以设置 `DAYTONA_API_KEY` 以使用 Daytona。本地 Docker
  必须支持 Harbor 的网络白名单策略。较新版本的 Docker Desktop 支持此策略；如果安装的
  Docker 不支持，Harbor 会停止运行。
- Claude 实验条件需设置 `ANTHROPIC_API_KEY`。Codex 实验条件和 TRAIL 裁判需设置
  `OPENAI_API_KEY`。
- 运行 TRAIL 基准测试时，需要使用已接受
  [PatronusAI/TRAIL](https://huggingface.co/datasets/PatronusAI/TRAIL) 条款的 Hugging Face
  账号的 token。TRAIL 受访问限制，不得再分发。请使用自己的 token 初始化数据库，
  不要提交或上传该数据集或生成的测试数据。未提供 token 时，暂存过程会跳过 TRAIL 任务。
  CI 不设置此 token。

<a id="run-a-benchmark"></a>
## 运行基准测试

<a id="1-stage-the-tasks"></a>
### 1. 暂存任务

运行基准测试之前，先从仓库根目录暂存任务。暂存过程会构建 Phoenix wheel，创建测试
数据库和任务构建上下文，为 CLI Agent 构建 px 归档，并构建提供 Harbor 插件的客户端 wheel：

```bash
# 仅暂存回归任务。
make harbor-stage
# 同时初始化 TRAIL 测试数据并暂存其任务。
HF_TOKEN=... make harbor-stage
```

px 归档需要 Docker，构建耗时几分钟。如果作业没有 CLI Agent，可设置 `HARBOR_CLI=0`
跳过归档。使用 `HARBOR_CLI_PLATFORM` 可将目标平台从 `linux/amd64` 改为其他平台。
修改服务端、`verifiers/`、`environments/` 或测试数据后，需要重新暂存，因为镜像包含
这些文件的副本。`RESEED=1` 还会重新构建测试数据。`make harbor-run` 会拒绝启动任务
尚未暂存的作业。

<a id="2-run-a-job"></a>
### 2. 运行作业

暂存后运行作业文件。`HARBOR_JOB` 用于选择文件，`HARBOR_ARGS` 用于向 `harbor run`
传递参数：

```bash
# 按照 CI 的方式运行回归基准测试。
make harbor-run
# 使用本地 Docker 运行一次尝试。
make harbor-run HARBOR_ARGS='-e docker -k 1'
make harbor-run HARBOR_JOB=evals/harbor/jobs/trail-benchmark-dev.yaml HARBOR_ARGS='-e docker'
make harbor-run HARBOR_JOB=evals/harbor/jobs/trail-benchmark-dev.yaml HARBOR_ARGS='-a oracle -e docker'
make harbor-run HARBOR_JOB=evals/harbor/jobs/trail-benchmark-dev.yaml HARBOR_ARGS='-e docker -k 3 --job-name px-1.19'
```

`-a oracle` 不使用 Agent 或模型调用，而是运行每个任务的参考解答并交给验证器验证。
修改任务、测试数据或验证器后应运行此模式。所有奖励均为 1，表示环境能够启动、查询正常，
且每个参考答案都通过了评分器。但这并不验证评分器是否会拒绝错误答案。

如需仅运行部分实验条件或任务，请创建作业文件的精简副本，并将 `HARBOR_JOB` 设为该路径。
不要使用 `-a <agent>` 选择已有实验条件。此选项会将已配置的 Agent 替换为最简 Agent 条目，
并移除定义该实验条件的 MCP 服务端、环境和技能配置。

```bash
uv run --script evals/harbor/scripts/subset_job.py evals/harbor/jobs/trail-benchmark-dev.yaml \
  --agents claude-code-mcp codex-cli --tasks count-traces total-cost --out evals/harbor/.cache/subset.yaml
make harbor-run HARBOR_JOB=evals/harbor/.cache/subset.yaml HARBOR_ARGS='-e docker'
```

<a id="results"></a>
### 结果

插件从环境中读取 `PHOENIX_COLLECTOR_ENDPOINT` 和 `PHOENIX_API_KEY`。
使用默认端口的本地 Phoenix 实例不需要这两个变量。如果插件无法连接 Phoenix，
作业会在任何试验开始前失败。

插件会在上表所列的数据集上为每个实验条件记录一个实验。数据集以作业的任务目录命名，
因此无论作业文件副本包含全部任务还是任务子集，都会记录到同一个数据集。
设置 `HARBOR_DATASET=<name>` 可选择其他数据集；设置 `HARBOR_PLUGIN=`
可运行但不向 Phoenix 记录结果。

每次运行包含 `reward` 和其他验证器测量值。TRAIL 验证器还会添加 `tool_count` 和
`turn_count`，它们不影响奖励。插件会添加 Harbor 的 token 数量、费用、延迟，以及
`infra_ok` 分数和 Agent 的完整追踪；Harbor 报告异常时，该分数为 `0`。
运行 `make harbor-view` 可打开 Harbor 结果查看器。

<a id="benchmark-conditions"></a>
## 基准测试实验条件

同一作业中的所有 Agent 使用相同镜像和验证器，因此奖励分数比较的是相同测试条件下
不同 Phoenix 接口的表现。

| Agent | 运行内容 | 访问 Phoenix 的方式 |
| --- | --- | --- |
| `phoenix-chat-agent` | Phoenix 服务端内部的 PXI | Agent 会话聊天路由 |
| `claude-code-mcp` | Claude Code | 位于 `/mcp` 的远程 MCP 服务端 |
| `claude-code-cli` | Claude Code | 从当前检出代码构建的 `px`，以及公开的 `phoenix-cli` 技能 |
| `codex-mcp` | Codex | 远程 MCP 服务端 |
| `codex-cli` | Codex | 相同的 px 安装和技能 |
| `oracle` | 无 Agent | 通过 `-a oracle` 运行各任务的 `solution/solve.sh` |

Agent 阶段以无特权用户运行，无法打开 `/data/phoenix.db`。Agent 必须通过 Phoenix
访问数据。PXI 在服务端内部运行，使用服务端的数据库访问权限。这一差异属于 PXI 实验条件的一部分。

<a id="the-trail-benchmark"></a>
## TRAIL 基准测试

TRAIL 基准测试包含关于 `research-assistant` 项目的问题。每个实验条件都在最终回复中
回答各个问题，验证器对该回复评分。

每个任务通过 `tests/expected.json` 文件选择以下两种评分方法之一：

```json
{"exact": "ok", "source": "fixed reply requested by the instruction"}
{"reference": "117 traces", "notes": "...", "source": "solution/solve.sh against the seeded fixture"}
```

`exact` 将回复与固定字符串比较，忽略 Markdown 强调标记、字母大小写和末尾标点。
`reference` 请 LLM 裁判判断回复给出的答案是否与参考答案相同。允许措辞不同、补充正确的
上下文，以及四舍五入到参考答案的精度。数值不同、给出多个候选答案或回答其他问题都会
判为失败。`notes` 为裁判提供额外指引，例如“page_down 是同一个工具”。
`source` 记录参考值的推导方式。

裁判使用基于 `gpt-5-nano` 的 `phoenix.evals` 分类器。设置
`PHOENIX_EVAL_JUDGE_MODEL` 和 `PHOENIX_EVAL_JUDGE_PROVIDER` 可改用其他模型。
请将提供商主机添加到任务的 `[verifier]` 表中。

<a id="add-a-task"></a>
### 添加任务

```text
tasks/trail-benchmark-dev/<name>/
  instruction.md                 问题本身，不说明答案应放在哪里
  task.toml                      [task] 名称和描述，后接共享配置块
  .gitignore                     所有任务保持一致
  tests/test.sh                  所有任务保持一致
  tests/expected.json            参考答案
  solution/solve.sh              由 oracle 运行的参考解答
```

复制已有任务，并修改 `instruction.md`、`[task]` 表、解答和 `expected.json`。
单元测试会检查共享文件是否保持一致，以及 `expected.json` 格式是否正确。

编写从运行中的 Phoenix 实例计算参考值的解答。使用 `harbor_verifiers.phoenix_api`
通过 Phoenix 客户端读取 span 和标注，并通过 GraphQL 读取各 span 的费用。
暂存任务、运行 oracle，再将其答案复制到 `expected.json`。
使用 `source` 说明解答如何计算答案。

对于修改 Phoenix 状态而非回答问题的任务，请编写自定义 `test.sh`。
可在 `http://127.0.0.1:6006` 查询 Phoenix，或读取 `/data/phoenix.db`。
验证器以 root 运行。计算奖励，并调用
`harbor_verifiers.verify.write_reward(reward, **extra)` 以纳入轨迹测量值。

<a id="add-a-condition"></a>
### 添加实验条件

实验条件是 `jobs/trail-benchmark-dev.yaml` 中的一个 Agent 条目。复制一个条目，修改
类、模型、`kwargs`、`env` 或 `skills`，并为其起一个新名称。技能是包含 `SKILL.md`
的目录；Harbor 会为 Claude Code 和 Codex 安装这些技能。

如需比较 px 或服务端版本，请从另一个检出目录暂存任务，并使用 `--job-name` 标识版本。
此过程会改变镜像，但不会改变数据集，因此两个实验使用相同的数据集版本。

<a id="run-the-tests"></a>
### 运行测试

```bash
uv run --all-packages pytest tests/unit/harbor
```

通过 oracle 运行，联合测试任务环境、参考解答和验证器。

<a id="the-regression-benchmark"></a>
## 回归基准测试

`tasks/regression/error-analysis` 是基于人工准备数据库的两步场景。Agent 先对项目追踪
进行开放编码并写成笔记，再进行主轴编码，形成各维度的标注配置。其验证器位于任务的
`tests/` 目录下，直接读取数据库和 Agent 的附属文件。`jobs/regression.yaml`
在 Daytona 上运行该场景，每个实验条件尝试两次。在 CI 中，
`.github/workflows/harbor-evals.yml` 使用 `scripts/check_job_reward.py` 检查奖励。

如需替换测试数据，请上传新数据库并重新暂存：

```bash
gcloud storage cp --cache-control=no-store phoenix.db \
  gs://arize-phoenix-assets/evals/harbor/error-analysis/phoenix.db
RESEED=1 make harbor-stage HARBOR_CLI=0
```

`tasks/regression/prompt-hill-climb` 是一个三步场景，数据库中包含一个文本转 SQL
数据集 `banking_saas_dataset_clean`（28 个示例，其中一半预期输出 `REFUSED:` 字符串）。
Agent 编写精确匹配评估器并将其附加到数据集，以空提示词运行基线实验，持续迭代直到
某次实验通过全部 28 个示例，再比较首个和最后一个实验，并在最后一个实验中记录心得。
验证器使用带代码围栏、带填充、被修改及空输出探测评估器，要求最后一个实验得分为
28/28，并对照数据库检查比较结果：所指明的两个实验、表现发生变化的示例、比较链接，
以及保留原有内容的元数据笔记。测试数据库位于
`gs://arize-phoenix-assets/evals/harbor/prompt-hill-climb/phoenix.db`.

<a id="choose-the-client-plugin-version"></a>
## 选择客户端插件版本

`arize-phoenix` Harbor 插件随 `arize-phoenix-client` 发布。默认情况下，`make
harbor-stage` 从当前检出代码构建该包，输出到 `dist/phoenix-client`，而 `make
harbor-run` 从该 wheel 加载插件。因此，作业记录使用的是当前源码树中的插件，
包括尚未发布的改动。修改 `packages/phoenix-client` 后需要重新暂存。

如需使用已发布插件记录，请为两个目标都设置 `HARBOR_CLIENT_VERSION`：

```bash
make harbor-stage HARBOR_CLIENT_VERSION=3.5.0
make harbor-run HARBOR_CLIENT_VERSION=3.5.0
```

<a id="name-experiments"></a>
## 命名实验

插件为每个 Agent 配置创建一个实验，默认名称为
`{job.name} · {agent.name} · {agent.model}`。如需改名，通过 `HARBOR_ARGS` 传入模板：

```bash
make harbor-run HARBOR_ARGS="--plugin-kwarg 'experiment_name_template={job.name} · {agent.name}'"
```

| 字段 | 值 |
| --- | --- |
| `{job.name}` | Harbor 作业名称；未设置名称时使用作业 ID |
| `{job.id}` | 唯一的 Harbor 作业 ID |
| `{dataset.name}` | Phoenix 数据集名称 |
| `{agent.name}` | Harbor Agent 名称 |
| `{agent.model}` | 配置的模型名称，或 `default` |
| `{agent.short_digest}` | Agent 配置摘要的前 12 个字符 |

字符串字段支持标准格式规范。Python 中的
`phoenix.client.harbor.EXPERIMENT_NAME_TEMPLATE_FIELDS` 列出了这些字段。
只有一个 Agent 的作业也可以直接使用字面量 `experiment_name=...`。

插件通过作业 ID、数据集版本和 Agent 配置摘要标识实验，而不是通过名称。
两个作业可以同名且不会合并。如需在 Phoenix 中区分作业，请在实验名称中包含
`{job.name}` 或 `{job.id}`。

<a id="configure-network-allowlists"></a>
## 配置网络白名单

默认情况下，任务不允许访问任何外部主机。请在需要该主机的最小适用层级添加它。
这样可以避免因新增提供商而更改 `task.toml` 及其数据集版本。

| 层级 | 设置位置 | 适用范围 | 用途 |
| --- | --- | --- | --- |
| 任务 | `task.toml` 中的 `[environment]` | 整个试验 | 无 |
| 验证器 | `task.toml` 中的 `[verifier]` | 仅验证阶段 | 裁判的提供商 |
| 作业 | 作业文件中的 `environment.extra_allowed_hosts` | 作业中的所有 Agent | Phoenix 文档主机 |
| Agent | Agent 条目中的 `extra_allowed_hosts` | 该 Agent 的运行 | Agent 的 LLM 提供商 |

如需封闭运行，请从作业和 Agent 配置中移除允许的主机。Agent 主机配置在安装阶段不生效。
安装依赖必须已包含在镜像或上传的文件中，或者可通过作业级别允许的主机访问。
