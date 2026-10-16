<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-cli">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        @arizeai/phoenix-cli
    </div>
</h1>

<p align="center">
    <a href="https://www.npmjs.com/package/@arizeai/phoenix-cli">
        <img src="https://img.shields.io/npm/v/%40arizeai%2Fphoenix-cli" alt="NPM 版本">
    </a>
    <a href="https://arize.com/docs/phoenix/">
        <img src="https://img.shields.io/badge/docs-blue?logo=typescript&logoColor=white" alt="文档">
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=js/packages/phoenix-cli/README.md" />
</p>

[Arize Phoenix](https://github.com/Arize-ai/phoenix) 的命令行接口。直接在终端中获取追踪、检查数据集、查询实验并访问提示词，或通过管道将其传给 Claude Code、Cursor、Codex 和 Gemini CLI 等 AI 编码 Agent。

<a id="installation"></a>

## 安装

```bash
npm install -g @arizeai/phoenix-cli
# or run without installing:
npx @arizeai/phoenix-cli

# once installed globally, update in place:
px self update
```

<a id="configuration"></a>

## 配置

```bash
export PHOENIX_ENDPOINT=http://localhost:6006
export PHOENIX_PROJECT=my-project
export PHOENIX_API_KEY=your-api-key  # if authentication is enabled
```

CLI 标志（`--endpoint`、`--project`、`--api-key`）覆盖环境变量。本地交互使用时，`px auth login` 在当前配置档案中保存 OAuth 会话，该会话以登录用户的权限运行。两者均配置时，API 密钥优先。

| 变量                                 | 说明                                                                                    |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `PHOENIX_ENDPOINT`                       | Phoenix 基础 URL（规范配置）                                                                   |
| `PHOENIX_COLLECTOR_ENDPOINT`             | 追踪导出基础 URL，通常与 `PHOENIX_ENDPOINT` 相同；后者未设置时，`px` 使用此值 |
| `PHOENIX_HOST`                           | 基础 URL 的旧版回退配置                                                               |
| `PHOENIX_PROJECT`                        | 项目名称或 ID（规范配置）                                                                 |
| `PHOENIX_PROJECT_NAME`                   | 项目名称或 ID（上述配置的别名）                                                           |
| `PHOENIX_API_KEY`                        | API 密钥（启用身份验证时）                                                                   |
| `PHOENIX_CLIENT_HEADERS`                 | 以 JSON 字符串表示的自定义请求头                                                                  |
| `PHOENIX_CLI_DANGEROUSLY_ENABLE_DELETES` | 设为 `true` 时启用 CLI 删除命令                                                  |

删除命令默认禁用，需要设置 `PHOENIX_CLI_DANGEROUSLY_ENABLE_DELETES=true`。

CLI 还会发现当前工作目录或上级目录中最近的 `.env.phoenix` 文件。配置优先级依次为：CLI 标志、进程环境、当前配置档案、`.env.phoenix`、内置默认值。凭证作为一组解析，因此不会将进程 API 密钥与文件提供的客户端请求头混用。若较高优先级凭证与文件端点配对，CLI 会发出一次警告后继续。设置 `PHOENIX_DISCOVER_CONFIG=false` 可禁用发现。

<a id="profiles"></a>

## 配置档案

配置档案以 `prod` 或 `staging` 等名称保存 Phoenix 实例的端点、项目、API 密钥及请求头。激活档案后，每个 `px` 命令都会采用这些设置，无需重新导出环境变量。环境变量和 CLI 标志仍会覆盖当前档案，因此现有脚本继续有效。

```bash
px profile create prod --endpoint https://phoenix.example.com --project main \
                       --api-key sk-xxx --activate
px profile list                # all profiles, kubectl-style "current" column
px profile show                # the active profile (or pass <name>)
px profile use prod            # switch the active profile
px profile edit prod           # open in $EDITOR, validates on save
px profile delete prod         # remove a profile (--yes to skip prompt)
```

向 `auth login`、`auth logout` 或 `auth status` 传入 `--profile <name>`，可仅对本次调用使用当前档案以外的指定档案。

<a id="editor-autocompletion-via-schema"></a>

### 通过 `$schema` 实现编辑器自动补全

CLI 首次创建 `settings.json` 时会自动写入 `$schema` 字段，使 VS Code 和 JetBrains 等编辑器开箱即可验证及自动补全文件：

```json
{
  "$schema": "https://raw.githubusercontent.com/Arize-ai/phoenix/main/schemas/phoenix-cli-settings.json",
  "activeProfile": "prod",
  "profiles": { ... }
}
```

如果手动删除该行，CLI 不会重新添加。模式位于 Phoenix 仓库的 `schemas/phoenix-cli-settings.json`，并与已发布的 Zod 模式保持同步。当前指针固定为 `main`；注册后将改用 SchemaStore 条目。

要在 VS Code 中设置项目级关联，请添加到 `.vscode/settings.json`：

```json
{
  "json.schemas": [
    {
      "fileMatch": ["settings.json"],
      "url": "https://raw.githubusercontent.com/Arize-ai/phoenix/main/schemas/phoenix-cli-settings.json"
    }
  ]
}
```

<a id="commands"></a>

## 命令

### `pxi`

打开 **PXI**（Phoenix Intelligence），在终端中与 Phoenix Agent 交互式聊天。它连接到运行中的 Phoenix 实例，使用与浏览器助手相同的服务器端 Agent，可从终端调查失败追踪、迭代提示词并操作 Phoenix。

```bash
pxi                                                          # uses PHOENIX_ENDPOINT / PHOENIX_API_KEY
pxi --endpoint http://localhost:6006 --provider OPENAI --model gpt-5.4
npx -y @arizeai/phoenix-cli pxi                              # run without installing
```

`pxi` 要求 Phoenix 服务器为 **20.0.0 或更高版本**。启动时会检查服务器版本，若版本较旧则显示升级提示并退出。

聊天中的斜杠命令（`/help`、`/clear`、`/new`、`/temporary`、`/sessions`、`/model`、`/compact`、`/exit`）在本地处理。完整标志和斜杠命令参考、模型配置及隐私控制见 [PXI 文档](https://arize.com/docs/phoenix/pxi)。

---

### `px setup`

将应用接入 Phoenix。在应用根目录运行：

```bash
px setup                                          # interactive
px setup --endpoint https://phoenix.example.com   # skip the endpoint prompt
npx -y @arizeai/phoenix-cli setup                 # try without installing
```

配置流程将连接保存到被 Git 忽略的 `.env.phoenix`，然后可选地将插桩任务交给编码 Agent（Claude Code、Codex、Cursor、OpenCode），并等待真实追踪出现。之后可将 `px` 指向新项目并安装 Phoenix 技能，让 Agent 查询已捕获的数据。

过程中会提议将 Phoenix 文档 MCP 服务器连接到接手任务的 Agent：若 Agent 提供 CLI，则通过其 CLI（`claude mcp
add`）；否则通过项目配置文件（`.cursor/mcp.json`、`opencode.json`）。接受后会完全跳过 `.px/docs` 下载，改由 Agent 按需搜索文档，配置更快且节省 Token。任何失败都会回退到下载。传入 `--docs-mcp` 可无需询问直接接受，传入 `--no-docs-mcp` 则不再询问。

在 CI 或 Agent 中，传入标志代替回答提示：

```bash
# Connection only — write .env.phoenix, no source changes
px setup --no-input --endpoint http://localhost:6006 --project my-app

# Instrument too — requires --agent when there's no TTY to choose one
px setup --no-input --instrument --agent claude --yolo --language python --format raw

# Same, but connect the docs MCP instead of downloading the docs
px setup --no-input --instrument --agent claude --yolo --docs-mcp --format raw
```

执行插桩的运行只有在追踪确实到达时才算成功，Agent 自称完成不算。所有输出及退出码都会体现这一点：

| 退出码 | 含义                                                              |
| ---- | -------------------------------------------------------------------- |
| `0`  | 已验证、仅注册，或在提示中选择“稍后验证” |
| `1`  | 意外错误                                                     |
| `2`  | 已取消                                                            |
| `3`  | 缺失或无效标志（错误会打印正确调用方式）   |
| `4`  | 未验证身份，或凭证权限不足                |
| `5`  | 无法连接 Phoenix 端点                                 |
| `6`  | 等待超时且未发现追踪，尚未确认追踪正常工作    |

仅等待超时返回 `6`。不带 `--instrument` 注册，或在超时提示中选择“Finish setup — I'll verify later”，均以 `0` 退出，因此主动延后验证时，`px setup && npm run dev` 和 `set -e` 脚本仍能继续运行。

在 `--format json|raw` 中，`verification` 为 `verified`、`notVerified` 或 `deferred`，无需验证时不存在；`tracesVerified` 是 `verification == "verified"` 的布尔简写。`--format pretty` 打印 `traces:` 行。不要根据接手任务的 Agent 自身退出码评定运行：它可能正确修改应用后异常退出，也可能正常退出却未交付任何内容。

后续可重新运行各部分：

```bash
px setup instrument --agent codex   # instrument and verify again
px setup skills                     # install coding-agent skills only
```

#### `px setup mcp`

将 Phoenix **远程 MCP 服务器**（`<endpoint>/mcp`）注册到编码 Agent，使其能够搜索、查询和操作 Phoenix 数据。端点从 `--endpoint`、当前配置档案或 `PHOENIX_ENDPOINT` 推断，无需重新输入。

```bash
px setup mcp                        # pick scope (global default) + agent, interactively
px setup mcp --agent codex          # configure one agent
px setup mcp --agent claude --local # write this repo's config (.mcp.json)
```

支持的 Agent：`claude`、`codex`、`gemini`、`cursor`、`opencode`、`vscode`。Agent 提供 `mcp add` 时（Claude、Codex、Gemini、VS Code 全局配置），CLI 会调用它；其他情况则合并到配置文件（`~/.cursor/mcp.json`、`~/.config/opencode/opencode.json`、`.vscode/mcp.json`）。作用域为 `--global`（用户级，默认）或 `--local`（当前仓库；Codex 仅支持全局）。

身份验证默认使用 **OAuth**：配置仅包含 URL，Agent 首次使用时打开 Phoenix 浏览器登录。无界面客户端可通过 `--header`（可重复）传入 API 密钥 Bearer 头：

```bash
px setup mcp --agent codex --no-input --format raw
px setup mcp --agent claude --header 'Authorization: Bearer ${PHOENIX_API_KEY}'
```

---

### `px self update`

检查 npm 注册表中的最新 CLI 发布，存在新版本时原位更新已安装的全局 CLI。

```bash
px self update          # show current/latest and update if needed
px self update --check  # show current/latest without installing
```

支持自动更新通过全局 `npm`、`pnpm`、`bun` 以及标准 `deno install -g` 包装器安装的 CLI。

### `px trace list [directory]`

从配置的项目获取近期追踪。所有输出均为 JSON。

```bash
px trace list --limit 10                          # stdout (pretty)
px trace list --format raw --no-progress | jq    # pipe-friendly compact JSON
px trace list ./my-traces --limit 50             # save as JSON files to directory
px trace list --last-n-minutes 60 --limit 20     # filter by time window
px trace list --since 2026-01-13T10:00:00Z       # since ISO timestamp
px trace list --since 2026-01-13T10:00:00Z --until 2026-01-14T10:00:00Z # time range
```

| 选项                      | 说明                                                 | 默认值  |
| --------------------------- | ----------------------------------------------------------- | -------- |
| `[directory]`               | 将追踪保存为目录中的 JSON 文件                      | stdout   |
| `-n, --limit <number>`      | 追踪数量（最新优先）                             | 10       |
| `--last-n-minutes <number>` | 仅最近 N 分钟的追踪                         | —        |
| `--since <timestamp>`       | 从 ISO 时间戳起的追踪                                  | —        |
| `--until <timestamp>`       | Span 在 ISO 时间戳之前开始的追踪（不包含该时刻） | —        |
| `--format <format>`         | `pretty`、`json` 或 `raw`                                  | `pretty` |
| `--no-progress`             | 关闭进度输出                                    | —        |
| `--include-annotations`     | 包含追踪和 Span 标注                          | —        |
| `--include-notes`           | 包含追踪和 Span 笔记                                | —        |

```bash
# Find ERROR traces
px trace list --limit 50 --format raw --no-progress | jq '.[] | select(.status == "ERROR")'

# Sort by duration, take top 5 slowest
px trace list --limit 20 --format raw --no-progress | jq 'sort_by(-.duration) | .[0:5]'

# Extract LLM model names used
px trace list --limit 50 --format raw --no-progress | \
  jq -r '.[].spans[] | select(.span_kind == "LLM") | .attributes["llm.model_name"]' | sort -u
```

---

### `px trace get <trace-id>`

按 ID 获取单条追踪。

```bash
px trace get abc123def456
px trace get abc123def456 --format raw | jq '.spans[] | select(.status_code != "OK")'
px trace get abc123def456 --file trace.json
px trace get abc123def456 --include-notes --format raw | jq '{traceNotes: .notes, spanNotes: [.spans[].notes]}'
```

---

### `px trace annotate <trace-id>`

按 OpenTelemetry 追踪 ID 创建或更新人工追踪标注。

```bash
px trace annotate abc123def456 --name reviewer --label pass
px trace annotate abc123def456 --name reviewer --score 0.9 --format raw --no-progress
px trace annotate abc123def456 --name evaluator --label pass --annotator-kind LLM
px trace annotate abc123def456 --name reviewer --explanation "needs follow-up"
```

---

### `px trace add-note <trace-id>`

按 OpenTelemetry 追踪 ID 为追踪添加笔记。

```bash
px trace add-note abc123def456 --text "needs follow-up"
px trace add-note abc123def456 --text "agent triage complete" --format raw --no-progress
```

---

### `px trace-annotations delete`

删除配置项目的追踪标注。必须指定 `--all`（删除所有匹配行），**或**同时指定 `--start-time` 和 `--end-time`，将删除限制在 `[start_time, end_time)` 窗口内。`--name`、`--identifier` 和 `--annotator-kind` 只用于缩小范围，绝不能单独授权请求。删除默认禁用，请先设置 `PHOENIX_CLI_DANGEROUSLY_ENABLE_DELETES=true`。

```bash
px trace-annotations delete --identifier "$PHOENIX_CODING_IDENTIFIER" --all -y
px trace-annotations delete --identifier "$PHOENIX_CODING_IDENTIFIER" --all -y --format raw --no-progress
px trace-annotations delete --start-time 2026-01-01T00:00:00Z --end-time 2026-01-02T00:00:00Z -y
```

输出（json/raw）： `{ deleted: true, target: "trace", filter: { identifier?, name?, annotator_kind?, start_time?, end_time?, all? } }`.

---

### `px span list [file]`

从配置的项目获取 Span，支持过滤选项，输出为 JSON。

```bash
px span list --limit 50                                    # stdout (pretty)
px span list --span-kind LLM --limit 20                    # only LLM spans
px span list --status-code ERROR --format raw --no-progress # pipe-friendly error spans
px span list --name chat_completion --trace-id abc123       # filter by name and trace
px span list --span-id abc123 def456                        # fetch specific spans by ID
px span list --parent-id null                               # root spans only
px span list spans.json --limit 100 --include-annotations   # save to file with annotations
px span list --last-n-minutes 30 --span-kind TOOL RETRIEVER # multiple span kinds
px span list --since 2026-07-01T00:00:00Z --until 2026-07-02T00:00:00Z # time range
```

| 选项                      | 说明                                                                                                                                  | 默认值  |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `[file]`                    | 将 Span 以 JSON 保存到文件                                                                                                                   | stdout   |
| `-n, --limit <number>`      | Span 最大数量（最新优先）                                                                                                       | `100`    |
| `--last-n-minutes <number>` | 仅最近 N 分钟的 Span                                                                                                           | —        |
| `--since <timestamp>`       | 从 ISO 时间戳起的 Span                                                                                                                    | —        |
| `--until <timestamp>`       | 在 ISO 时间戳之前开始的 Span（不包含该时刻）                                                                                               | —        |
| `--span-kind <kinds...>`    | 按 Span 类型过滤 (`LLM`, `CHAIN`, `TOOL`, `RETRIEVER`, `EMBEDDING`, `AGENT`, `RERANKER`, `GUARDRAIL`, `EVALUATOR`, `DECISION`, `UNKNOWN`) | —        |
| `--status-code <codes...>`  | 按状态码过滤 (`OK`, `ERROR`, `UNSET`)                                                                                               | —        |
| `--name <names...>`         | 按 Span 名称过滤                                                                                                                       | —        |
| `--trace-id <ids...>`       | 按追踪 ID 过滤                                                                                                                        | —        |
| `--span-id <ids...>`        | 按 OpenTelemetry Span ID 过滤。要求 Phoenix 服务器 >= 19.6.0。                                                                       | —        |
| `--parent-id <id>`          | 按父 Span ID 过滤（使用 `"null"` 表示仅根 Span）                                                                                  | —        |
| `--include-annotations`     | 输出中包含 Span 标注                                                                                                       | —        |
| `--include-notes`           | 输出中包含 Span 笔记                                                                                                             | —        |
| `--format <format>`         | `pretty`、`json` 或 `raw`                                                                                                                   | `pretty` |
| `--no-progress`             | 关闭进度输出                                                                                                                     | —        |

```bash
# Find all ERROR spans
px span list --status-code ERROR --format raw --no-progress | jq '.[] | {name, status_code}'

# Get LLM spans with token counts
px span list --span-kind LLM --format raw --no-progress | \
  jq '.[] | {name, model: .attributes["llm.model_name"], tokens: (.attributes["llm.token_count.prompt"] + .attributes["llm.token_count.completion"])}'

# Root spans only, sorted by name
px span list --parent-id null --format raw --no-progress | jq 'sort_by(.name)'
```

---

### `px span annotate <span-id>`

按 OpenTelemetry Span ID 创建或更新人工 Span 标注。

```bash
px span annotate 7e2f08cb43bbf521 --name reviewer --label pass
px span annotate 7e2f08cb43bbf521 --name reviewer --score 0.9 --format raw --no-progress
px span annotate 7e2f08cb43bbf521 --name checker --score 1 --annotator-kind CODE
px span annotate 7e2f08cb43bbf521 --name reviewer --explanation "looks good"
```

---

### `px span add-note <span-id>`

按 OpenTelemetry Span ID 为 Span 添加笔记。

```bash
px span add-note 7e2f08cb43bbf521 --text "double-check tool output"
px span add-note 7e2f08cb43bbf521 --text "verified by agent" --format raw --no-progress
```

---

### `px span-annotations delete`

删除配置项目的 Span 标注。授权条件与 `px trace-annotations delete` 相同，要求 `--all` 或同时指定 `--start-time` 和 `--end-time`。

```bash
px span-annotations delete --identifier "$PHOENIX_CODING_IDENTIFIER" --all -y
```

---

### `px dataset list`

列出所有数据集。

```bash
px dataset list --format raw --no-progress | jq '.[].name'
```

---

### `px dataset get <dataset-identifier>`

从数据集获取示例。

```bash
px dataset get my-dataset --format raw | jq '.examples[].input'
px dataset get my-dataset --split train --split test
px dataset get my-dataset --version <version-id>
px dataset get my-dataset --file dataset.json
```

---

### `px experiment list --dataset <name-or-id>`

列出数据集的实验。

```bash
px experiment list --dataset my-dataset --format raw --no-progress | \
  jq '.[] | {id, successful_run_count, failed_run_count}'
```

---

### `px experiment get <experiment-id>`

获取单个实验及全部运行数据（输入、输出、评估、追踪 ID）。

```bash
# Find failed runs
px experiment get RXhwZXJpbWVudDox --format raw --no-progress | \
  jq '.[] | select(.error != null) | {input, error}'

# Average latency
px experiment get RXhwZXJpbWVudDox --format raw --no-progress | \
  jq '[.[].latency_ms] | add / length'
```

---

### `px prompt list`

列出所有提示词。

```bash
px prompt list --format raw --no-progress | jq '.[].name'
```

---

### `px prompt get <prompt-identifier>`

获取提示词。`text` 格式适合通过管道传给 AI 助手。

```bash
px prompt get my-evaluator --format text --no-progress | claude -p "Review this prompt"
px prompt get my-evaluator --tag production --format json | jq '.template'
```

| 选项              | 说明                        | 默认值  |
| ------------------- | ---------------------------------- | -------- |
| `--tag <name>`      | 按标签获取版本                 | —        |
| `--version <id>`    | 获取指定版本               | 最新版本   |
| `--format <format>` | `pretty`、`json`、`raw` 或 `text` | `pretty` |

---

### `px project list`

列出所有可用 Phoenix 项目。

```bash
px project list                                           # pretty output
px project list --format raw --no-progress | jq '.[].name'
px project list --limit 5
```

| 选项              | 说明                         | 默认值  |
| ------------------- | ----------------------------------- | -------- |
| `--limit <number>`  | 每页项目最大数量 | —        |
| `--format <format>` | `pretty`、`json` 或 `raw`          | `pretty` |
| `--no-progress`     | 关闭进度输出            | —        |

---

### `px project get <name>`

按精确名称获取单个 Phoenix 项目。输出为单条记录（非数组），JSON 和 raw 模式输出裸对象。名称未匹配时，以 `ExitCode.FAILURE`（1）退出，并在 `--format json|raw` 下向 stderr 写入 `StructuredError` JSON 对象。

```bash
px project get my-project
px project get my-project --format raw --no-progress | jq -r '.id'
px project get my-project --format json
```

| 选项              | 说明                         | 默认值  |
| ------------------- | ----------------------------------- | -------- |
| `--format <format>` | `pretty`、`json` 或 `raw`          | `pretty` |
| `--limit <number>`  | 底层查询的页面大小 | `100`    |
| `--no-progress`     | 关闭进度输出            | —        |

未匹配时的 stderr（raw）： `{"error":"Project 'foo' not found","code":"FAILURE","hint":"px project list --format raw"}`.

---

### `px session list`

列出项目会话。

```bash
px session list                                            # latest 10 sessions
px session list --limit 20 --order asc                     # oldest first
px session list --format raw --no-progress | jq '.[].session_id'
px session list --include-annotations --include-notes --format raw | jq '.[].notes'
```

| 选项                  | 说明                                  | 默认值  |
| ----------------------- | -------------------------------------------- | -------- |
| `-n, --limit <number>`  | 会话最大数量                   | `10`     |
| `--order <order>`       | 排序方向：`asc` 或 `desc`                  | `desc`   |
| `--include-annotations` | 包含会话标注，不含笔记 | —        |
| `--include-notes`       | 存在会话笔记时包含笔记           | —        |
| `--format <format>`     | `pretty`、`json` 或 `raw`                   | `pretty` |
| `--no-progress`         | 关闭进度输出                     | —        |

---

### `px session get <session-id>`

查看会话的对话流程。

```bash
px session get my-session-id
px session get my-session-id --file session.json
px session get my-session-id --include-annotations --format raw | jq '.session.annotations'
px session get my-session-id --include-notes --format raw | jq '.session.notes'
```

| 选项                  | 说明                                  | 默认值  |
| ----------------------- | -------------------------------------------- | -------- |
| `--file <path>`         | 将会话保存到文件，不输出到 stdout       | —        |
| `--include-annotations` | 包含会话标注，不含笔记 | —        |
| `--include-notes`       | 存在会话笔记时包含笔记           | —        |
| `--format <format>`     | `pretty`、`json` 或 `raw`                   | `pretty` |
| `--no-progress`         | 关闭进度输出                     | —        |

---

### `px session annotate <session-id>`

按 GlobalID 或用户提供的 `session_id` 创建或更新人工会话标注。

```bash
px session annotate my-session-id --name reviewer --label pass
px session annotate my-session-id --name reviewer --score 0.9 --format raw --no-progress
px session annotate my-session-id --name evaluator --label pass --annotator-kind LLM
px session annotate my-session-id --name reviewer --explanation "needs follow-up"
```

---

### `px session add-note <session-id>`

按 GlobalID 或用户提供的 `session_id` 为会话添加笔记。要求 Phoenix 服务器 `14.17.0` 或更高版本。

```bash
px session add-note my-session-id --text "needs follow-up"
px session add-note my-session-id --text "agent triage complete" --format raw --no-progress
```

---

### `px session-annotations delete`

删除配置项目的会话标注。授权条件与追踪/Span 对应命令相同，要求 `--all` 或同时指定 `--start-time` 和 `--end-time`。

```bash
px session-annotations delete --identifier "$PHOENIX_CODING_IDENTIFIER" --all -y
```

---

标注配置有三种类型：`CATEGORICAL`（固定标签集合，每个标签可选关联数值分数）、`CONTINUOUS`（数值范围）和 `FREEFORM`（自由文本）。`create`、`get`、`update`、`delete` 与 `list` 一起提供完整增删改查。

<a id="specifying-categorical-values"></a>

#### 指定分类值

`create` 和 `update` 接收分类标签的方式相同，只需学习一次。优先使用可重复、适合 shell 的标志；JSON 形式是适合批量/Agent 的替代方式。

```bash
# Repeatable flag: label with an optional score (label=score, or just label)
--value good=1 --value bad=0 --value needs-review

# JSON payload (handy for agents or large label sets)
--values '[{"label":"good","score":1},{"label":"bad","score":0}]'
```

两种形式互斥，只能传入其中一种。

---

### `px annotation-config list`

列出 Phoenix 实例定义的标注配置。

```bash
# Show all annotation configs as a table
px annotation-config list

# Extract config names as JSON (agent-friendly)
px annotation-config list --format raw --no-progress | jq -r '.[].name'

# Fetch at most 10 configs
px annotation-config list --limit 10
```

| 选项              | 说明                | 默认值  |
| ------------------- | -------------------------- | -------- |
| `--format <format>` | `pretty`、`json` 或 `raw` | `pretty` |
| `--no-progress`     | 关闭进度输出   | —        |

---

### `px annotation-config get <config-identifier>`

按名称或 ID 获取单个标注配置，并按选定 `--format` 写入 stdout（`raw`/`json` 为单个对象）。

```bash
# Look up a config by name
px annotation-config get response-quality

# Resolve a config name to its ID (agent-friendly)
px annotation-config get response-quality --format raw --no-progress | jq -r '.id'

# Inspect the labels of a categorical config
px annotation-config get response-quality --format raw --no-progress | jq '.values'
```

| 选项              | 说明                | 默认值  |
| ------------------- | -------------------------- | -------- |
| `--format <format>` | `pretty`、`json` 或 `raw` | `pretty` |
| `--no-progress`     | 关闭进度输出   | —        |

---

### `px annotation-config create`

通过 `POST /v1/annotation_configs` 创建新标注配置，并按选定 `--format` 将创建的配置写入 stdout。

```bash
# Pass/fail quality rating with scored labels (higher is better)
px annotation-config create --type CATEGORICAL --name response-quality \
  --value good=1 --value bad=0 --optimization-direction MAXIMIZE

# Sentiment labels without scores
px annotation-config create --type CATEGORICAL --name sentiment \
  --value positive --value neutral --value negative

# Confidence score between 0 and 1
px annotation-config create --type CONTINUOUS --name confidence --lower-bound 0 --upper-bound 1

# Free-text feedback from human reviewers
px annotation-config create --type FREEFORM --name reviewer-notes --description 'Free-form reviewer feedback'

# Create from a JSON payload and capture the new config ID (agent-friendly)
px annotation-config create --type CATEGORICAL --name response-quality \
  --values '[{"label":"good","score":1},{"label":"bad","score":0}]' \
  --format raw --no-progress | jq -r '.id'
```

| 选项                           | 说明                                           | 默认值  |
| -------------------------------- | ----------------------------------------------------- | -------- |
| `--type <type>`                  | `CATEGORICAL`、`CONTINUOUS` 或 `FREEFORM`（必填） | —        |
| `--name <name>`                  | 标注配置名称（必填）                     | —        |
| `--description <description>`    | 说明                                           | —        |
| `--optimization-direction <dir>` | `MINIMIZE`、`MAXIMIZE` 或 `NONE`                     | `NONE`   |
| `--value <label[=score]>`        | 分类标签（可重复；CATEGORICAL 配置）   | —        |
| `--values <json>`                | JSON 格式的分类值（CATEGORICAL 配置）      | —        |
| `--lower-bound <number>`         | 下界（CONTINUOUS/FREEFORM 配置）             | —        |
| `--upper-bound <number>`         | 上界（CONTINUOUS/FREEFORM 配置）             | —        |
| `--threshold <number>`           | 阈值（FREEFORM 配置）                          | —        |
| `--format <format>`              | `pretty`、`json` 或 `raw`                            | `pretty` |
| `--no-progress`                  | 关闭进度输出                              | —        |

`--type` 和 `--name` 必填；`CATEGORICAL` 配置还要求至少一个值。`--type` 和 `--optimization-direction` 不区分大小写。输入无效时（包括不适用于所选类型的标志）以 `INVALID_ARGUMENT` 退出。

---

### `px annotation-config update <config-identifier>`

按名称或 ID 更新标注配置，仅修改传入字段。命令获取现有配置、合并标志，并通过 `PUT /v1/annotation_configs/{id}` 写回结果。配置的 `type` 不可变；若需修改，必须删除后重新创建。更新后的配置按选定 `--format` 写入 stdout。

```bash
# Change only the description; every other field is preserved
px annotation-config update response-quality --description 'Pass/fail rating from human review'

# Rename a config and set its optimization direction
px annotation-config update response-quality --name answer-quality --optimization-direction MAXIMIZE

# Replace the label set of a categorical config
px annotation-config update response-quality --value good=1 --value acceptable=0.5 --value bad=0

# Widen the range of a continuous config
px annotation-config update confidence --lower-bound -1 --upper-bound 1

# Update and capture the config ID (agent-friendly)
px annotation-config update response-quality --description 'Updated' --format raw --no-progress | jq -r '.id'
```

| 选项                           | 说明                                         | 默认值  |
| -------------------------------- | --------------------------------------------------- | -------- |
| `--name <name>`                  | 新名称                                            | —        |
| `--description <description>`    | 新说明                                     | —        |
| `--optimization-direction <dir>` | `MINIMIZE`、`MAXIMIZE` 或 `NONE`                   | —        |
| `--value <label[=score]>`        | 分类标签（可重复；CATEGORICAL 配置） | —        |
| `--values <json>`                | JSON 格式的分类值（CATEGORICAL 配置）    | —        |
| `--lower-bound <number>`         | 下界（CONTINUOUS/FREEFORM 配置）           | —        |
| `--upper-bound <number>`         | 上界（CONTINUOUS/FREEFORM 配置）           | —        |
| `--threshold <number>`           | 阈值（FREEFORM 配置）                        | —        |
| `--format <format>`              | `pretty`、`json` 或 `raw`                          | `pretty` |
| `--no-progress`                  | 关闭进度输出                            | —        |

至少需要一个字段标志。输入无效时（包括不适用于配置类型的标志，例如连续型配置使用 `--value`）以 `INVALID_ARGUMENT` 退出。

---

### `px annotation-config delete <config-id>`

按 ID 删除标注配置。与所有删除命令一样，未设置 `PHOENIX_CLI_DANGEROUSLY_ENABLE_DELETES=true` 时禁用；未传入 `--yes` 时会要求确认。

```bash
# Delete with an interactive confirmation prompt
px annotation-config delete QW5ub3RhdGlvbkNvbmZpZzoxMjM=

# Skip the confirmation prompt (for scripts and agents)
px annotation-config delete QW5ub3RhdGlvbkNvbmZpZzoxMjM= --yes

# Resolve a name to its ID, then delete it
px annotation-config get response-quality --format raw --no-progress | jq -r '.id' | xargs px annotation-config delete --yes
```

| 选项          | 说明              | 默认值 |
| --------------- | ------------------------ | ------- |
| `-y, --yes`     | 跳过确认提示 | —       |
| `--no-progress` | 关闭进度输出 | —       |

---

### `px auth login`

通过浏览器 OAuth 流程登录，并将令牌保存在所选配置档案中。URL 始终打印到 stderr，方便 SSH 和无界面用户手动打开。OAuth CLI 会话以登录用户的权限运行。

CLI 自动为 REST、GraphQL 和 PXI 请求刷新即将到期的访问令牌。请求被以 `401` 拒绝时，触发一次刷新和重试；轮换后的令牌保存回所选配置档案。

```bash
px auth login
px auth login --no-browser
px auth login --profile staging --format raw
```

| 选项              | 说明                            | 默认值  |
| ------------------- | -------------------------------------- | -------- |
| `--endpoint <url>`  | Phoenix API 端点                   | —        |
| `--api-key <key>`   | Phoenix API 密钥                        | —        |
| `--profile <name>`  | 保存 OAuth 令牌的配置档案       | 当前档案   |
| `--no-browser`      | 打印 URL，不打开浏览器    | —        |
| `--no-input`        | 不提示粘贴重定向 URL | —        |
| `--format <format>` | `pretty`、`json` 或 `raw`             | `pretty` |

### `px auth logout`

清除所选配置档案中的 OAuth 令牌。退出登录会尽力在服务器上撤销刷新令牌，不修改已配置的 API 密钥。

```bash
px auth logout
px auth logout --profile staging
px auth logout --format raw
```

### `px auth status`

显示当前 Phoenix 身份验证状态，包括配置端点、凭证来源、身份，以及适用时的 OAuth 访问级别/到期时间。

```bash
px auth status
px auth status --endpoint http://localhost:6006
px auth status --profile staging --format raw
```

| 选项              | 说明                | 默认值  |
| ------------------- | -------------------------- | -------- |
| `--endpoint <url>`  | Phoenix API 端点       | —        |
| `--api-key <key>`   | Phoenix API 密钥            | —        |
| `--profile <name>`  | 要使用的配置档案             | 当前档案   |
| `--format <format>` | `pretty`、`json` 或 `raw` | `pretty` |

---

### `px api graphql <query>`

对 Phoenix API 执行已验证身份的 GraphQL 查询。输出为 `{"data": {...}}` JSON，可通过管道使用 `jq '.data.<field>'` 提取值。仅允许查询，拒绝变更和订阅。

```bash
px api graphql '<query>' [--endpoint <url>] [--api-key <key>]
```

将确切 HTTP 请求预览为 `curl`，但不执行：

```bash
px api graphql '{ projects { edges { node { name } } } }' --curl
px api graphql '{ projects { edges { node { name } } } }' --curl --show-token
```

`--curl` 将等价请求打印到 stdout 后退出，不发起网络调用。授权头默认脱敏，包括通过 `PHOENIX_API_KEY` 或 `PHOENIX_CLIENT_HEADERS` 提供的值。仅在明确需要生成命令包含原始凭证时使用 `--show-token`。

当前范围和行为：

- `--curl` 当前仅支持 `px api graphql`。
- `--curl` 打印请求，不执行请求。
- `--show-token` 仅与 `--curl` 一起使用时有效。
- 授权脱敏和请求头规范化与 `fetch` 实际请求行为保持一致。

使用内省发现可用字段：

```bash
$ px api graphql '{ __schema { queryType { fields { name } } } }' | jq '.data.__schema.queryType.fields[].name'
"projects"
"datasets"
"prompts"
"evaluators"
"projectCount"
"datasetCount"
...

$ px api graphql '{ __type(name: "Experiment") { fields { name type { name } } } }' | \
    jq '.data.__type.fields[] | {name, type: .type.name}'
{"name":"id","type":"ID"}
{"name":"name","type":"String"}
{"name":"runCount","type":"Int"}
{"name":"errorRate","type":"Float"}
{"name":"averageRunLatencyMs","type":"Float"}
```

**项目：**

```bash
$ px api graphql '{ projects { edges { node { name traceCount tokenCountTotal } } } }' | \
    jq '.data.projects.edges[].node'
{"name": "default", "traceCount": 1482, "tokenCountTotal": 219083}
```

**数据集：**

```bash
$ px api graphql '{ datasets { edges { node { name exampleCount experimentCount } } } }' | \
    jq '.data.datasets.edges[].node'
{"name": "eval-golden-set", "exampleCount": 120, "experimentCount": 4}
{"name": "rag-test-cases", "exampleCount": 50, "experimentCount": 1}
```

**实验：**

```bash
# List experiments per dataset with error rate and avg latency
$ px api graphql '{
  datasets {
    edges {
      node {
        name
        experiments {
          edges {
            node { name runCount errorRate averageRunLatencyMs }
          }
        }
      }
    }
  }
}' | jq '.data.datasets.edges[].node | {dataset: .name, experiments: [.experiments.edges[].node]}'

# Find experiments with failures
$ px api graphql '{
  datasets { edges { node { name experiments { edges { node { name errorRate runCount } } } } } }
}' | jq '.. | objects | select(.errorRate? > 0) | {name, errorRate, runCount}'
```

**计数概览：**

```bash
$ px api graphql '{ projectCount datasetCount promptCount evaluatorCount }'
{"data": {"projectCount": 1, "datasetCount": 12, "promptCount": 3, "evaluatorCount": 2}}
```

---

### `px docs fetch`

下载 Phoenix 文档 Markdown 文件供编码 Agent 使用。从 [llms.txt](https://arize.com/docs/phoenix/llms.txt) 索引获取页面，按工作流类别过滤，并写入本地目录，同时自动生成索引文件。

```bash
px docs fetch                                # fetch default workflows
px docs fetch --workflow tracing             # fetch only tracing docs
px docs fetch --workflow tracing --workflow evaluation
px docs fetch --dry-run                      # preview without downloading
px docs fetch --refresh                      # clear output dir and re-download
```

| 选项               | 说明                                                                                                                                    | 默认值                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `--workflow <name>`  | 按工作流类别过滤（可重复）。取值： `tracing`, `evaluation`, `datasets`, `prompts`, `integrations`, `sdk`, `self-hosting`, `all` | `tracing`, `evaluation`, `datasets`, `prompts`, `integrations` |
| `--output-dir <dir>` | 下载文档的输出目录                                                                                                           | `.px/docs`                                                     |
| `--dry-run`          | 仅发现链接，不写入文件                                                                                                        | `false`                                                        |
| `--refresh`          | 下载前清空输出目录                                                                                                      | `false`                                                        |
| `--strict`           | 任意页面下载失败时使命令失败                                                                                                        | `false`                                                        |
| `--workers <n>`      | 并发下载工作线程数                                                                                                          | `10`                                                           |

---

<a id="json-output-shape"></a>

## JSON 输出结构

所有命令都输出 JSON。通过管道传递时，使用 `--format raw` 获取紧凑 JSON，并使用 `--no-progress` 关闭 stderr 进度输出：

```bash
px trace list --format raw --no-progress | jq ...
px dataset list --format raw --no-progress | jq ...
```

追踪 JSON 结构：

```json
{
  "traceId": "abc123def456",
  "status": "OK",
  "duration": 1250,
  "spans": [
    {
      "name": "chat_completion",
      "span_kind": "LLM",
      "status_code": "OK",
      "attributes": {
        "llm.model_name": "gpt-4",
        "llm.token_count.prompt": 512,
        "llm.token_count.completion": 256,
        "input.value": "What is the weather?",
        "output.value": "The weather is sunny..."
      }
    }
  ]
}
```

`px api graphql` 输出始终将结果包裹在 `{"data": {...}}` 中，可通过管道使用 `jq '.data.<field>'` 提取。

---

<a id="community"></a>

## 社区

- 🌍 [Slack 社区](https://join.slack.com/t/arize-ai/shared_invite/zt-3r07iavnk-ammtATWSlF0pSrd1DsMW7g)
- 📚 [文档](https://arize.com/docs/phoenix)
- 🌟 [GitHub](https://github.com/Arize-ai/phoenix)
- 🐞 [报告问题](https://github.com/Arize-ai/phoenix/issues)
- 𝕏 [@ArizePhoenix](https://twitter.com/ArizePhoenix)
- 💼 [LinkedIn](https://www.linkedin.com/showcase/113218220)
