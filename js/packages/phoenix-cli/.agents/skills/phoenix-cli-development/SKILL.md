---
name: phoenix-cli-development
description: >
  Phoenix CLI（`px`）设计与实现指南，涵盖名词-动词命令结构、面向人和编码 Agent 的双受众设计、
  Commander.js 模式、配置解析、输出格式、退出码以及新增或修改命令的约定。
  处理 phoenix-cli 命令时触发，包括新增命令、修改现有命令、重构命令结构或审查 CLI 代码。
  提及 `px` 命令、CLI 设计或向 CLI 添加新资源时也触发。
license: Apache-2.0
metadata:
  author: oss@arize.com
  version: "2.1.0"
  internal: true
---

<a id="phoenix-cli-design-specification"></a>

# Phoenix CLI 设计规范

Phoenix CLI（`px`）是 Phoenix AI 可观测性平台的命令行接口，同时面向两类不同受众：在终端键入命令的**人**，以及以编程方式执行命令的**编码 Agent**（Claude Code、Cursor、Codex、Gemini CLI）。

本规范使用 RFC 2119 关键字（MUST、SHOULD、MAY 等，分别译为必须、应该、可以）表示要求强度。

<a id="command-structure-noun-verb"></a>

## 命令结构：名词-动词

所有命令**必须**仿照 GitHub CLI（`gh`）遵循**名词-动词**模式：

```
px <resource> <action> [arguments] [options]
```

资源名称**必须**为**单数**，用于命名操作对象的类型，而非数量：

```bash
px project list              # not "px projects"
px project create            # not "px create-project"
px trace get <trace-id>
px dataset get <name-or-id>
px auth status
```

<a id="standard-verbs"></a>

### 标准动词

命令**应该**在所有资源中一致使用以下动词：

| 动词     | 用途                       | 是否接收参数 | 示例                             |
| -------- | ----------------------------- | --------------- | ----------------------------------- |
| `list`   | 列出/查询多个资源 | 否（使用标志） | `px project list --limit 10`        |
| `get`    | 按 ID 获取单个资源 | 是（必填）  | `px trace get <trace-id>`           |
| `create` | 创建新资源         | 视情况而定          | `px project create --name foo`      |
| `update` | 修改现有资源   | 是（必填）  | `px project update <id> --name bar` |
| `delete` | 删除资源             | 是（必填）  | `px project delete <id>`            |

并非每个资源都支持所有动词；如果主要通过 SDK 操作数据集，CLI **可以**不提供 `create`。命令**必须**只添加对该资源有意义的动词。

标准动词不能覆盖专用操作时，**建议**增加专用动词：

- `px auth login`, `px auth status`
- `px self update`
- `px docs fetch`
- `px api graphql <query>`

<a id="backward-compatibility-during-migration"></a>

### 迁移期间的向后兼容

CLI 正从扁平结构（`px projects`、`px traces`）演进为完整的名词-动词结构。过渡期间两种形式**可以**共存。迁移现有命令时：

1. **必须**将新的名词-动词形式创建为主命令
2. **应该**将旧形式保留为隐藏别名（Commander 的 `.alias()` 或隐藏命令），避免破坏现有脚本
3. 后续文档**必须**只记录名词-动词形式

<a id="dual-audience-design"></a>

## 双受众设计

CLI **必须**同样适合终端用户和编码 Agent 使用。每个输出数据的命令都**必须**支持 `--format`：

- **`pretty`**（默认）：便于人阅读的表格和格式
- **`json`**：带缩进的 JSON，供人检查结构化数据
- **`raw`**：紧凑单行 JSON，适合通过管道传入 `jq` 或供 Agent 使用

命令**可以**支持其他格式（如提示词的 `--format text`）。默认值始终**必须**为 `pretty`。

进度指示器**必须**写入 stderr。Agent **应该**传入 `--no-progress` 将其关闭。

```bash
# Agent-friendly invocation
px trace list --format raw --no-progress | jq '...'
```

<a id="semantic-exit-codes"></a>

### 语义化退出码

定义于 `src/exitCodes.ts`。命令**必须**使用命名常量，**不得**使用裸数字字面量。

| 退出码 | 常量           | 含义                                             |
| ---- | ------------------ | --------------------------------------------------- |
| 0    | `SUCCESS`          | 命令成功完成                      |
| 1    | `FAILURE`          | 未指定或意外错误                     |
| 2    | `CANCELLED`        | 用户取消（例如拒绝确认）      |
| 3    | `INVALID_ARGUMENT` | CLI 标志错误、缺少必填参数、输入无效 |
| 4    | `AUTH_REQUIRED`    | 未验证身份或权限不足       |
| 5    | `NETWORK_ERROR`    | 服务器连接或网络请求失败      |
| 6    | `NOT_VERIFIED`     | 已运行，但无法验证生成结果    |

<a id="interactive-default-with-non-interactive-mode"></a>

### 默认交互与非交互模式

缺少必填值或需要确认时，命令**可以**交互式提问，这是适合人的默认行为。`--no-input` 标志**必须**关闭所有提示，包括缺失值提示和破坏性操作确认。未连接 TTY 时（标准输入来自管道）也会自动启用非交互模式。

非交互模式中，若缺少必填值，命令**必须**立即以 `ExitCode.INVALID_ARGUMENT` 退出并打印正确调用方式。若原本会显示确认，命令**必须**按已确认继续执行：

```bash
# Human: missing --name triggers interactive prompt
px project create

# Agent: all inputs as flags, no prompts
px project create --name my-project --format raw --no-input

# Human: gets "Are you sure?" prompt
px dataset delete my-dataset

# Agent: skips confirmation
px dataset delete my-dataset --no-input --format raw
```

```
Error: Missing required flag --name.
  px project create --name <project-name>
```

<a id="idempotent-commands"></a>

### 幂等命令

命令**应该**尽可能幂等。同一命令执行两次**不得**产生重复资源或意外错误：

- `create` 命令**应该**支持 `--if-not-exists`，以返回现有资源而非失败
- 对不存在资源执行 `delete` 时，**应该**以 `ExitCode.SUCCESS` 退出（不视为错误）

<a id="return-structured-data-on-success"></a>

### 成功时返回结构化数据

修改命令（`create`、`update`、`delete`）**必须**在 stdout 中按选定的 `--format` 返回受影响资源。命令**不得**只打印“Project created.”之类的成功消息，而应输出资源，使 Agent 可以提取 ID、URL 等字段：

```bash
$ px project create --name foo --format raw
{"id":"proj_abc","name":"foo","createdAt":"2025-03-15T10:00:00Z"}
```

<a id="fail-fast-with-actionable-errors"></a>

### 快速失败并提供可操作错误

因输入无效导致命令失败时，错误消息**必须**包含正确的调用语法。遵循 `src/config.ts` 中 `getConfigErrorMessage()` 的现有模式：

- 说明错误所在
- 给出修正错误的正确命令
- 有帮助时建议相关命令（例如“可用项目：`px project list`”）

启用 `--format raw` 或 `--format json` 时，错误也**应该**以结构化 JSON 写入 stderr，以便 Agent 解析。使用 `StructuredError` 结构：

```typescript
interface StructuredError {
  error: string; // Human-readable error message
  code: string; // ExitCode constant name (e.g., "INVALID_ARGUMENT")
  hint?: string; // Suggested command to resolve the issue
}
```

```json
{
  "error": "Project not found",
  "code": "FAILURE",
  "hint": "px project list --format raw"
}
```

<a id="progressive-help-discovery"></a>

### 渐进式帮助发现

每个子命令**必须**包含带有至少一个具体示例的 `--help`。使用 Commander 的 `.addHelpText('after', ...)` 追加 `Examples:` 块：

```
$ px project create --help
Usage: px project create [options]

Create a new Phoenix project.

Options:
  --name <name>       Project name (required)
  --description <d>   Project description
  --format <format>   Output format (pretty|json|raw) (default: "pretty")
  -h, --help          Display help

Examples:
  px project create --name my-project
  px project create --name my-project --format raw
```

Agent 逐步发现功能：`px` → `px project` → `px project create --help`。每层**必须**提供足够信息以继续深入。

<a id="adding-a-new-command"></a>

## 添加新命令

<a id="options-interface"></a>

### 选项接口

每个处理器**必须**为其选项定义 TypeScript 接口，作为命令注册标志的类型化映射。字段名**必须**具有描述性，**不得**使用缩写。

跨命令重复出现的结构位于 `src/commands/options.ts`，**必须**复用，不得重新声明：

| 类型                            | 字段                                                      | 用途                                           |
| ------------------------------- | ----------------------------------------------------------- | ------------------------------------------------- |
| `ConnectionOptions`             | `endpoint`, `apiKey`                                        | 所有调用 Phoenix API 的命令            |
| `CommonOptions<TFormat>`        | + `format`, `progress`                                      | 所有打印资源的命令                |
| `ProjectScopedOptions<TFormat>` | + `project`                                                 | 注册 `--project` 的命令                |
| `AnnotationInclusionOptions`    | `includeAnnotations`, `includeNotes`                        | Span/追踪/会话读取                          |
| `DeleteOptions`                 | `endpoint`, `apiKey`, `progress`, `yes`                     | 删除动词（直接使用，不定义本地接口） |
| `AnnotateOptions`               | `name`, `label`, `score`, `explanation`, `annotatorKind`, … | `annotate` 动词                                  |
| `AddNoteOptions`                | `text`, `identifier`                                        | `add-note` 动词                                  |
| `AnnotationsDeleteOptions`      | 过滤条件 + `all`、`yes`                                      | `*-annotations delete` 命令                   |

命令标志与共享结构完全匹配时，**必须**直接使用该类型，不得声明相同的本地类型。否则，扩展对应基类，只声明该命令特有的标志：

```typescript
interface SpanListOptions
  extends ProjectScopedOptions<SpanOutputFormat>, AnnotationInclusionOptions {
  /**
   * `--span-kind <kinds...>`: Filter by OpenInference span kind — `LLM`,
   * `CHAIN`, `TOOL`, …
   *
   * @example ["LLM", "TOOL"]
   */
  spanKind?: string[];
}
```

每个字段**必须**带有 TSDoc 块，以标志原文及参数占位符开头，说明 `.option()` 调用中声明的默认值，并在具体值有助于理解用法时提供 `@example`。否定标志（`--no-progress`、`--no-input`）**必须**注明反向语义：Commander 默认设为 `true`，仅在传入标志时设为 `false`。

提示输入或要求确认的命令**必须**支持非交互模式：输入提示（`px setup`）使用 `--no-input`，破坏性操作确认通过 `ConfirmationOptions` 使用 `--yes`。

<a id="configuration-resolution"></a>

### 配置解析

CLI **必须**从多个来源解析配置，合并逻辑使用 `src/config.ts` 的 `resolveConfig()`。优先级：

1. **CLI 标志**（最高优先级） — `--endpoint`, `--api-key`, `--project`
2. **环境变量** — `PHOENIX_ENDPOINT`, `PHOENIX_API_KEY`, `PHOENIX_PROJECT` （别名：`PHOENIX_PROJECT_NAME`）
3. **默认值**：端点为 `http://localhost:6006`

命令处理器**不得**直接读取环境变量。

<a id="output-formatting"></a>

### 输出格式化

每种资源类型**应该**在 `src/commands/format*.ts` 中有格式化模块。创建新资源命令时，**必须**遵循现有模式创建对应格式化器。

- `formatTable.ts` — 共享表格渲染，根据终端宽度截断列
- `formatProjectsOutput()`、`formatTracesOutput()` 等：资源专用格式化器

格式化器**必须**接收 `format` 选项并返回字符串。

<a id="io-functions"></a>

### I/O 函数

命令**必须**使用 `src/io.ts` 中的辅助函数：

```typescript
writeOutput({ message }); // → stdout (data the user/agent wants)
writeError({ message }); // → stderr (errors)
writeProgress({ message, noProgress }); // → stderr (suppressible status updates)
```

**不得**直接使用 `console.log`。`writeOutput`/`writeError` 分离确保 stdout 仅包含数据输出，这是管道正确工作的**必要条件**。

<a id="naming-conventions"></a>

## 命名约定

代码**必须**遵循以下命名约定（另见 phoenix-typescript 技能）：

- **函数与变量**: `camelCase` — `createProjectCommand`, `projectListHandler`
- **类型与接口**: `PascalCase` — `ProjectListOptions`, `OutputFormat`
- **常量**: `SCREAMING_SNAKE_CASE` — `ExitCode.SUCCESS`, `CLI_VERSION`
- **文件**: `camelCase.ts` — `projects.ts`, `formatProjects.ts`
- **禁止缩写**：使用 `projectIdentifier`，而非 `projId`；使用 `annotationConfig`，而非 `annCfg`

<a id="testing"></a>

## 测试

测试使用 **vitest**，位于与 `src/` 结构对应的 `test/` 目录。

```bash
pnpm test          # run all tests
pnpm test:watch    # watch mode
```

HTTP 使用 `@arizeai/phoenix-testing` 模拟（根据 OpenAPI 定义生成的 MSW 处理器），测试**不得**替换全局 `fetch`。使用共享测试框架：

- `test/mockServer.ts`：在模块顶层调用 `const mock = setupMockPhoenixServer()`；每个文档化 Phoenix 端点返回模式生成的数据，未处理请求使测试失败。使用类型化 `http` 命名空间为每个测试指定精确响应：`mock.server.use(http.get("/v1/projects", ({ response }) => response(200).json({...})))`。在处理器内部捕获值，以断言请求（参数、查询、请求体）。
- `test/testUtils.ts`：`BASE_ARGS`（端点 + `--no-progress` 参数）、`mockProcessExit()`（抛出 `process.exit:<code>` 以断言退出码）和 `captureCliOutput()`（静默 stdout/stderr 的 Spy）。
- 原始非 OpenAPI 处理器（GraphQL、第三方主机）使用 `@arizeai/phoenix-testing` 重新导出的 msw（`HttpResponse`、`http`）；`HttpResponse.error()` 模拟网络失败。
- 已有的 fetch 依赖注入（如 OAuth 辅助函数中的 `fetchImpl` 参数）可以保持原样，无需 MSW。

添加命令时，测试**必须**覆盖：

- 通过 HTTP 验证处理器逻辑（使用类型化 MSW 处理器，不模拟客户端）
- 各格式模式的格式化器输出
- 边界情况：缺少配置、网络错误、空结果
- 错误路径的退出码正确性
- 仅使用生成处理器运行一次（不指定响应），证明命令对符合规范的数据可以端到端运行

<a id="build-and-run"></a>

## 构建与运行

```bash
pnpm build         # TypeScript → build/
pnpm dev           # Run from source via tsx (during development)
```

CLI 以 `@arizeai/phoenix-cli` 发布，可执行命令别名为 `px` 和 `phoenix-cli`。

<a id="global-options-placement"></a>

## 全局选项的位置

全局选项（`--endpoint`、`--api-key`）**必须**放在**动词**上，而非名词上。这是**必要要求**，因为 Commander 将选项绑定到定义该选项的命令：

```bash
# Correct — options on the verb
px project list --endpoint http://my-server:6006

# Wrong — options on the noun (Commander won't parse these)
px project --endpoint http://my-server:6006 list
```

<a id="checklist-for-adding-a-new-resource-command"></a>

## 添加新资源命令的检查清单

1. 创建 `src/commands/<resource>.ts`，通过 `create<Resource>Command()` 导出名词命令
2. 按需添加动词子命令（`list`、`get`、`create` 等）
3. 创建 `src/commands/format<Resource>.ts` 处理输出格式化
4. 定义选项接口，使用具有描述性的字段名
5. 使用 `resolveConfig()` 解析配置，使用 `createPhoenixClient()` 调用 API
6. 使用 `writeOutput()`/`writeError()` 处理 I/O，使用语义化 `ExitCode` 常量处理错误
7. 从 `src/commands/index.ts` 导出
8. 在 `src/cli.ts` 中通过 `program.addCommand()` 注册
9. 在 `test/` 添加测试
10. 运行 `pnpm test`，修复所有失败后再继续
11. 运行 `pnpm build`，修复所有类型错误后再继续
12. 更新 `README.md`，提供同时适合人和 Agent 的调用示例
13. 命令、标志、示例或输出结构变化时，更新 `.agents/skills/phoenix-cli/SKILL.md` 中对外提供的 Phoenix CLI 技能
14. 保持技能更新简洁：以最小实用示例和输出结构说明记录新能力，不要重复整份 README
15. 若命令提示输入或要求确认，需支持 `--no-input`（见 `InteractiveCommandOptions`）
16. 通过 `.addHelpText('after', ...)` 向 `--help` 添加至少一个示例
17. 修改命令在 stdout 返回受影响资源（不能只返回成功消息）
18. 手动使用 `--format raw` 和 `--no-input` 运行，验证 Agent 获得干净、可解析的输出
