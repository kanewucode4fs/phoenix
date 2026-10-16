# @arizeai/phoenix-cli

## 1.18.8

### 补丁变更

- 更新依赖 [7b9f900]
  - @arizeai/phoenix-client@7.16.1

## 1.18.7

### 补丁变更

- 更新依赖 [f8ae2fc]
  - @arizeai/phoenix-client@7.16.0

## 1.18.6

### 补丁变更

- c72f77b: PXI 斜杠命令提示现在有高亮行：方向键移动选择（两端循环），Tab 补全，Enter 执行，因此 `/he` 会执行 `/help`。单独输入 `/` 会列出所有命令，`/help` 排在首位，因此 `/` + Enter 不会造成影响。
- 更新依赖 [5b37f12]
  - @arizeai/phoenix-client@7.15.0

## 1.18.5

### 补丁变更

- 更新依赖 [aab229f]
  - @arizeai/phoenix-client@7.14.0

## 1.18.4

### 补丁变更

- 更新依赖 [c282563]
  - @arizeai/phoenix-client@7.13.0

## 1.18.3

### 补丁变更

- 更新依赖 [dab09f1]
  - @arizeai/phoenix-client@7.12.0

## 1.18.2

### 补丁变更

- 更新依赖 [2b73847]
  - @arizeai/phoenix-client@7.11.0

## 1.18.1

### 补丁变更

- 更新依赖 [c839254]
  - @arizeai/phoenix-client@7.10.0

## 1.18.0

### 次版本变更

- bf047af: 新增 Meta（Muse Spark 模型）作为内置的 OpenAI 兼容模型提供商（`META`）。

### 补丁变更

- 更新依赖 [bf047af]
  - @arizeai/phoenix-client@7.9.0

## 1.17.0

### 次版本变更

- 58b7017: 新增 Z.ai（GLM 模型）作为内置的 OpenAI 兼容模型提供商（`ZAI`）。

### 补丁变更

- 更新依赖 [58b7017]
  - @arizeai/phoenix-client@7.8.0

## 1.16.5

### 补丁变更

- 3a836f7: PXI 会话推荐使用 claude-fable-5-1

## 1.16.4

### 补丁变更

- 更新依赖 [1cdff14]
  - @arizeai/phoenix-client@7.7.1

## 1.16.3

### 补丁变更

- 更新依赖 [37916d7]
- 更新依赖 [c48e50e]
- 更新依赖 [773c5e5]
- 更新依赖 [b27561d]
  - @arizeai/phoenix-client@7.7.0

## 1.16.2

### 补丁变更

- 更新依赖 [d328c3e]
  - @arizeai/phoenix-client@7.6.0

## 1.16.1

### 补丁变更

- 2435eba: PXI 会话推荐使用 gemini-3.7-flash，从推荐列表移除已被替代的 gemini-3.5-flash，并补充缺失的 claude-opus-5 条目

## 1.16.0

### 次版本变更

- 0ed987a: 重新启用 PXI Agent 会话服务器版本检查。连接的 Phoenix 服务器早于 Agent 会话聊天契约（服务器 < 20.0.0）时，PXI 现在会在启动时快速失败并给出明确升级提示，而不是首次发送时返回 404。phoenix-client 为其余 Agent 会话路由（列出、获取、局部更新、压缩、工具输出）添加能力要求，从包根入口导出全部 Agent 会话要求，并通过客户端配置的 fetch 调用 `getServerVersion`。

### 补丁变更

- 更新依赖 [0ed987a]
  - @arizeai/phoenix-client@7.5.0

## 1.15.2

### 补丁变更

- 更新依赖 [90729f3]
  - @arizeai/phoenix-client@7.4.0

## 1.15.1

### 补丁变更

- 更新依赖 [c892873]
  - @arizeai/phoenix-client@7.3.1

## 1.15.0

### 次版本变更

- e90ba00: `px` 现在先从 `PHOENIX_ENDPOINT`（API 访问的规范配置）解析端点；仅设置追踪导出变量 `PHOENIX_COLLECTOR_ENDPOINT` 和 `OTEL_EXPORTER_OTLP_ENDPOINT` 时从中推断，最后使用旧版 `PHOENIX_HOST`，与 SDK 和 API 客户端保持一致。此前 CLI 仅读取 `PHOENIX_HOST`，并静默回退到 `http://localhost:6006`。

  仅从追踪导出变量推断的端点仍低于当前配置档案的优先级，因此为应用追踪导出这些变量不会使已验证身份的命令转向其他端点。

  `px setup` 将 `PHOENIX_ENDPOINT` 和 `PHOENIX_COLLECTOR_ENDPOINT` 都写入 `.env.phoenix`（OTel SDK 读取收集器变量），在该目录中运行的其他所有 `px` 命令现在也会遵循该文件。CLI 消息使用 `PHOENIX_ENDPOINT` 名称。

### 补丁变更

- de2ee8d: 告知 `px setup` 插桩 Agent：`PHOENIX_COLLECTOR_ENDPOINT` 是基础 URL，接收完整 OTLP URL 的导出器（如 `@mastra/arize` 的 `ArizeExporter`）必须使用 `<endpoint>/v1/traces`，并在“追踪未验证”提示中指出此错误。将这类导出器指向基础 URL 会丢弃所有 Span，且不报错。
- 更新依赖 [d04f0fc]
  - @arizeai/phoenix-config@0.5.0
  - @arizeai/phoenix-client@7.3.0

## 1.14.1

### 补丁变更

- 更新依赖 [59aa7cb]
  - @arizeai/phoenix-client@7.2.0

## 1.14.0

### 次版本变更

- df9db47: 运行未知命令且已发布更新版本时，建议升级 `px`。

## 1.13.1

### 补丁变更

- 1d9dd4e: 修复配置档案包含过期 OAuth 凭证、但 Phoenix 服务器现已允许匿名访问时的 `px auth status`

## 1.13.0

### 次版本变更

- f816b5b: 将 `pxi` 终端客户端默认模型从 Anthropic `claude-opus-4-8` 改为 `claude-opus-5`。仍可通过 `--model` 覆盖。

## 1.12.0

### 次版本变更

- 3f5ef25: 为 `px project list` 添加不区分大小写的 `--name-contains` 过滤器。

## 1.11.1

### 补丁变更

- e35712a: 重新发布，以恢复失败的发布（版本已存在于 npm）
- 更新依赖 [e35712a]
  - @arizeai/phoenix-client@7.1.1

## 1.11.0

### 次版本变更

- df7057a: 为 `px span list` 添加 `--span-id` 过滤器，支持按 OpenTelemetry Span ID 获取 Span（要求 Phoenix 服务器 >= 19.6.0）。为 `px span list` 和 `px trace list` 添加 `--until`，通过不包含结束时刻的时间戳限定范围，与 `--since` 配合指定时间区间。

### 补丁变更

- 更新依赖 [df7057a]
  - @arizeai/phoenix-client@7.1.0

## 1.10.5

### 补丁变更

- 更新依赖 [a6c3f88]
  - @arizeai/phoenix-client@7.0.1

## 1.10.4

### 补丁变更

- 4867e34: 将 `ai` 依赖更新到 v7，以匹配 `@arizeai/phoenix-client` 的 `ai@^7.0.0` peer 要求，避免安装 CLI 时出现无法解析的 peer 冲突。CLI 仅使用 AI SDK 的 UI 消息传输 API，它们在 v7 中未发生变化。
- 更新依赖 [4867e34]
  - @arizeai/phoenix-client@7.0.0

## 1.10.3

### 补丁变更

- @arizeai/phoenix-client@6.14.2

## 1.10.2

### 补丁变更

- @arizeai/phoenix-client@6.14.1

## 1.10.1

### 补丁变更

- 1f3c4b6: `px auth login` 现在会在启动浏览器流程前探测服务器的 `.well-known/oauth-authorization-server` 发现文档；服务器不可达时以网络错误干净退出，服务器不支持 OAuth 登录时以身份验证错误退出

## 1.10.0

### 次版本变更

- 3abafcf: 新增 `px setup mcp`，将 Phoenix 远程 MCP 服务器注册到编码 Agent（Claude Code、Cursor、Codex 等），默认使用 OAuth，支持通过 `--header` 使用 API 密钥验证身份，并提供本地/全局作用域

## 1.9.1

### 补丁变更

- d6b1cbb: 为 Phoenix TypeScript 客户端添加可复用、支持凭证刷新的 fetch 封装，
  用于 OAuth 验证的 CLI API 和 PXI 请求，并将每个
  配置档案绑定到签发其 OAuth 令牌的端点。
- 更新依赖 [d6b1cbb]
  - @arizeai/phoenix-client@6.14.0

## 1.9.0

### 次版本变更

- f94067b: 添加 px setup 脚本，用于 Agent 接入引导

### 补丁变更

- 更新依赖 [f94067b]
  - @arizeai/phoenix-client@6.13.0
  - @arizeai/phoenix-config@0.4.0

## 1.8.1

### 补丁变更

- c0ab6a9: 新增 `.env.phoenix` 文件发现，作为 Phoenix 配置的回退来源。进程环境中不存在某项配置时，`@arizeai/phoenix-config` 从当前工作目录向上查找最近的 `.env.phoenix` 文件，并读取以 `PHOENIX_` 为前缀的键（dotenv 格式）。进程环境值优先，相关配置（凭证、OTel 端点/端口）从同一来源按组解析。忽略非当前用户拥有的文件；对跳过的文件、其他用户可访问的文件，以及与不同来源凭证配对的端点发出一次性警告。设置 `PHOENIX_DISCOVER_CONFIG=false` 禁用发现；调用 `clearEnvFileCache()` 刷新缓存结果。浏览器构建通过条件包导出选择不依赖 Node 的实现。`@arizeai/phoenix-cli` 将发现值的优先级置于配置档案之下；`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 通过共享解析逻辑读取 `.env.phoenix` 值。
- 更新依赖 [c0ab6a9]
  - @arizeai/phoenix-config@0.3.0
  - @arizeai/phoenix-client@6.12.2

## 1.8.0

### 次版本变更

- 1e7d9fc: 统一各 TypeScript 包的项目名称环境变量：所有接口现在都读取 `PHOENIX_PROJECT`（规范变量）和 `PHOENIX_PROJECT_NAME`（受支持别名），`PHOENIX_PROJECT` 优先，显式参数/标志仍高于两者。两者设为冲突值时，使用规范变量的值，并发出一次性警告列出两个值。`@arizeai/phoenix-config` 是该解析逻辑的唯一实现位置：提供共享的 `getProjectFromEnvironment()` 解析器，并在 `getEnvironmentConfig()` 中包含解析后的项目。`@arizeai/phoenix-cli`、`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 均使用它；`@arizeai/phoenix-otel` 现在依赖 `@arizeai/phoenix-config`，未传入 `projectName` 时，`register()` 通过共享解析器回退到这些变量，不再重复实现逻辑。

### 补丁变更

- 更新依赖 [1e7d9fc]
  - @arizeai/phoenix-config@0.2.0
  - @arizeai/phoenix-client@6.12.1

## 1.7.0

### 次版本变更

- d4282c5: 改进终端中的 PXI 工具调用渲染：每个调用现在显示状态符号（运行时为旋转指示器，之后为 ✓/✗/?/⊘）、工具专属图标，以及从输入推导的单行操作摘要。Bash 调用显示模型编写的摘要、所执行命令的片段，失败时还显示退出码和 stderr 片段；`load_skill` 和 `read_skill_resource` 完成后折叠为简洁单行。

## 1.6.2

### 补丁变更

- 更新依赖 [7947440]
  - @arizeai/phoenix-client@6.12.0

## 1.6.1

### 补丁变更

- 6240c13: fix(cli): 改进 pxi 预检网络错误
- f3809ed: **PXI：** 为 `pxi` 终端客户端添加斜杠命令支持。输入 `/clear` 重置对话历史，`/exit` 退出，`/help` 列出可用命令。输入提示现在以黄色高亮命令 Token，并在输入时展示实时补全列表。
- 更新依赖 [7afa183]
  - @arizeai/phoenix-client@6.11.2

## 1.6.0

### 次版本变更

- 70246e9: **测试版：** 为 `@arizeai/phoenix-cli` 添加 `pxi` 终端客户端。在 shell 中通过 `npx -y @arizeai/phoenix-cli pxi`（或 `pxi` 可执行命令）启动交互式 PXI（Phoenix Intelligence）聊天。它连接到运行中 Phoenix 实例的服务器 Agent 端点，与浏览器体验使用相同 Agent，并在启动时执行模型预检，将配置问题呈现为清晰错误。通过 `PHOENIX_HOST`/`--endpoint` 配置端点，通过 `--provider`/`--model` 选择模型（默认 Anthropic `claude-opus-4-8`）。

  此功能处于测试阶段，未来发布中可能变化。

## 1.5.3

### 补丁变更

- 更新依赖 [a027ada]
  - @arizeai/phoenix-client@6.11.1

## 1.5.2

### 补丁变更

- 更新依赖 [7efabf6]
  - @arizeai/phoenix-client@6.11.0

## 1.5.1

### 补丁变更

- 更新依赖 [0347f22]
  - @arizeai/phoenix-client@6.10.1

## 1.5.0

### 次版本变更

- 6dceb10: 将标注批量删除命令重构为实体在前的复合名词：
  `px span delete-annotations` 改为 `px span-annotations delete`，
  `px trace delete-annotations` 改为 `px trace-annotations delete`，以及
  `px session delete-annotations` 改为 `px session-annotations delete`。标志
  集合、授权条件（`--all` XOR `[--start-time, --end-time)`）、载荷
  结构及退出码不变。

  为 `addTraceNote`、`addSpanNote` 和
  `addSessionNote`（及生成的 REST 类型）添加可选请求体字段 `identifier`。非空时，笔记按
  `(entity_id, name='note', identifier)` 更新或插入，因此重复调用时，
  相同标识符会覆盖已有笔记，而不是追加。为
  辅助函数提供 `identifier` 时，现在还会调用
  `ensureServerCapability` 检查新增标识符请求体参数的
  能力要求，使调用方在旧 Phoenix 服务器上快速失败（否则服务器会
  静默丢弃该字段并追加自动生成的笔记）。

### 补丁变更

- 更新依赖 [6dceb10]
  - @arizeai/phoenix-client@6.10.0

## 1.4.3

### 补丁变更

- @arizeai/phoenix-client@6.9.3

## 1.4.2

### 补丁变更

- 更新依赖 [d0cc4c4]
  - @arizeai/phoenix-client@6.9.2

## 1.4.1

### 补丁变更

- 5d14f23: 在 README 的社区章节添加 LinkedIn 链接。
- 更新依赖 [5d14f23]
  - @arizeai/phoenix-config@0.1.4
  - @arizeai/phoenix-client@6.9.1

## 1.4.0

### 次版本变更

- ab62d3d: 为 Phoenix CLI 添加命名配置档案：`px profile list|show|create|edit|use|delete`。档案保存到 `~/.px/settings.json`（或 `$XDG_CONFIG_HOME/px/settings.json`，权限 `0600`），作为内置默认值与环境变量之间的新层级参与配置解析。`px auth status` 展示当前档案，并接收 `--profile <name>` 限定调用。其他命令遵循已保存的当前档案。

  设置文件通过 JSON Schema 验证；模式提交在 `schemas/phoenix-cli-settings.json`，可在 `settings.json` 的 `$schema` 字段引用，以便编辑器自动补全。

### 补丁变更

- 4e20267: 为 Phoenix CLI 添加会话标注和笔记命令，并为 TypeScript 客户端添加会话笔记辅助函数。创建会话笔记要求 Phoenix 服务器 14.17.0 或更高版本。
- 更新依赖 [2993b04]
- 更新依赖 [4e20267]
- 更新依赖 [2993b04]
  - @arizeai/phoenix-client@6.9.0

## 1.3.1

### 补丁变更

- 更新依赖 [e381885]
- 更新依赖 [187df7e]
  - @arizeai/phoenix-client@6.8.1

## 1.3.0

### 次版本变更

- a4dad8b: 为 `px` 添加追踪笔记支持。新命令 `px trace add-note <trace-id> --text <text>` 创建追踪笔记；`px trace get` 和 `px trace list` 现在支持 `--include-notes`，将追踪笔记和 Span 笔记与标注分开获取及渲染。要求 Phoenix 服务器 >= 14.13.0。

### 补丁变更

- 更新依赖 [a4dad8b]
  - @arizeai/phoenix-client@6.8.0

## 1.2.0

### 次版本变更

- e19a038: 为 `px span list` 添加 `--attribute` 过滤器，按属性键值对过滤（如 `--attribute "llm.model_name:gpt-4"`）。仅按第一个 `:` 分隔，因此值可包含冒号。重复标志可用 AND 组合多个过滤器。值看似数字或布尔值时，可用 JSON 引号强制字符串匹配（如 `'user.id:"12345"'`）。要求 Phoenix 服务器 >= 14.9.0。

### 补丁变更

- 更新依赖 [e19a038]
  - @arizeai/phoenix-client@6.7.0

## 1.1.0

### 次版本变更

- 7944fe7: 为 `px` 添加 Span 笔记支持。新命令 `px span add-note <span-id>` 在 Span 上创建笔记；`px span list`、`px trace get` 和 `px trace list` 现在支持 `--include-notes`，随 Span 一起获取和渲染笔记。

## 1.0.5

### 补丁变更

- 更新依赖 [8444575]
  - @arizeai/phoenix-client@6.6.2

## 1.0.4

### 补丁变更

- 更新依赖 [1449f3d]
  - @arizeai/phoenix-client@6.6.1

## 1.0.3

### 补丁变更

- 更新依赖 [c70eca6]
  - @arizeai/phoenix-client@6.6.0

## 1.0.2

### 补丁变更

- 更新依赖 [1028be5]
  - @arizeai/phoenix-client@6.5.5

## 1.0.1

### 补丁变更

- f8d5871: 在 Commander.js 选项解析器的 parseInt 中使用显式进制

## 1.0.0

### 主版本变更

- 4b5dd70: 将 Phoenix CLI 资源命令重构为名词-动词格式。

  这对 CLI 使用方是破坏性变更。`px projects`、
  `px traces`、`px spans`、`px datasets`、`px sessions`、`px experiments` 和
  `px prompts` 等扁平命令已替换为单数资源命令和动词
  子命令，例如 `px project list`、`px trace list`、`px trace get`、
  `px span list`、`px dataset list`、`px dataset get`、`px session list`、
  `px session get`、`px experiment list`、`px experiment get`、`px prompt list`，
  以及 `px prompt get`。

  帮助文本和文档已更新，以反映新命令结构。

## 0.12.1

### 补丁变更

- b4ded15: 使用最新功能更新各包 README

  - phoenix-client：添加会话章节，说明 `listSessions`、`getSession` 和 `addSessionAnnotation`
  - phoenix-evals：添加完整预置评估器表格（简洁性、正确性、文档相关性、拒绝回答、工具评估器），修复 `bindEvaluator` 导入路径
  - phoenix-mcp：扩展工具覆盖范围章节，提供完整准确的工具列表
  - phoenix-config：以完整文档替换单行占位说明（安装、环境变量、使用示例）
  - phoenix-cli：添加 `px annotation-config` 命令文档

- 更新依赖 [b4ded15]
  - @arizeai/phoenix-client@6.5.4
  - @arizeai/phoenix-config@0.1.3

## 0.12.0

### 次版本变更

- 4444b46: 添加 `px self update`，让 Phoenix CLI 能检查已发布的新版本
  并原位升级自身。

  该命令现在：

  - 展示当前及最新发布的 CLI 版本
  - 支持通过 `--check` 仅检查状态
  - 更新由 `npm`、`pnpm` 和 `bun` 管理的全局安装
  - 重用包装器安装标志，更新标准 `deno install -g` 包装器安装

### 补丁变更

- 更新依赖 [e4bdcf6]
  - @arizeai/phoenix-config@0.1.2
  - @arizeai/phoenix-client@6.5.3

## 0.11.1

### 补丁变更

- 71d2b1b: 通过更清晰的横幅和帮助输出改进 Phoenix CLI 启动体验。
  - 展示更简洁的横幅说明和版本标签。
  - 仅在确实存在更新 CLI 版本时显示更新指引。
  - 将提示词帮助文本统一为 `prompt-identifier`。

## 0.11.0

### 次版本变更

- 3bccd12: 为 `px api graphql` 添加 `--curl` 支持，让用户可以打印等价
  请求而不执行。授权头默认脱敏，
  明确需要时可用 `--show-token` 显示原始令牌。

## 0.10.1

### 补丁变更

- d204898: docs: 在包 README 中记录近期新增的命令和方法
- 更新依赖 [d204898]
  - @arizeai/phoenix-client@6.5.2

## 0.10.0

### 次版本变更

- 65e52c2: 添加 `px spans` 命令，用于通过过滤器获取 Span。
  美化输出使用表格格式，与 `px projects` 和 `px datasets` 等 CLI 命令一致。

## 0.9.2

### 补丁变更

- 更新依赖 [91949d7]
  - @arizeai/phoenix-client@6.5.1

## 0.9.1

### 补丁变更

- d320b93: 将 llms.txt 解析器迁移到标准 llmstxt.org Markdown 链接格式（`- [Title](url): Description`）

## 0.9.0

### 次版本变更

- c0836c3: 添加 `px docs fetch` 命令，为编码 Agent 下载 Phoenix 文档 Markdown。
  从 llms.txt 索引获取，支持工作流过滤、并发下载和自动生成索引文件。

## 0.8.0

### 次版本变更

- 62666f6: 添加 `px annotation-config list` 命令，列出全部标注配置。

  新命令通过基于游标的分页从 `GET /v1/annotation_configs` 获取标注配置，支持 `--format pretty|json|raw`、`--limit`、`--endpoint`、`--api-key` 和 `--no-progress` 选项。

- d647a32: 在无参数运行 `px` 时展示的 CLI 引导中添加 ASCII 艺术横幅。
  在 Phoenix 标志旁展示连接的服务器 URL 和项目名称。
- a6319de: 为所有 `list` 命令使用紧凑 ASCII 表格替换冗长的框线列表输出。

  `px datasets list`、`px experiments list`、`px prompts list`、`px sessions list`、
  `px projects list` 和 `px annotation-config list` 等命令现在将结果渲染为对齐表格
  （与 `console.table` 风格一致），替代多行框线卡片。这使较长的
  列表更易快速浏览。`--format json` 和 `--format raw` 输出保持不变。

- 4e7b7c2: 为 CLI 添加语义化退出码，以支持脚本和 CI 集成。

  命令现在使用有意义的退出码，不再在失败时始终返回 `1`：

  | 退出码 | 含义 | 说明 |
  | ---- | ---------------- | ------------------------------------------------------ |
  | `0` | 成功 | 命令成功完成 |
  | `1` | 失败 | 未指定或意外错误 |
  | `2` | 已取消 | 用户取消操作 |
  | `3` | 参数无效 | CLI 标志错误、缺少必填参数或输入无效 |
  | `4` | 需要身份验证 | 未验证身份或权限不足 |
  | `5` | 网络错误 | 连接服务器失败或网络请求失败 |

### 补丁变更

- 更新依赖 [9769f90]
  - @arizeai/phoenix-client@6.5.0

## 0.7.4

### 补丁变更

- 更新依赖 [83b7f68]
  - @arizeai/phoenix-client@6.4.0

## 0.7.3

### 补丁变更

- 更新依赖 [d951320]
  - @arizeai/phoenix-client@6.3.0

## 0.7.2

### 补丁变更

- 更新依赖 [6d896e3]
  - @arizeai/phoenix-client@6.2.0

## 0.7.1

### 补丁变更

- 更新依赖 [b8ba989]
- 更新依赖 [6296d0a]
- 更新依赖 [6296d0a]
  - @arizeai/phoenix-client@6.1.0

## 0.7.0

### 次版本变更

- 03b10a8: 添加 `px sessions` 和 `px session` 命令，通过 REST API 浏览多轮对话会话。

### 补丁变更

- 更新依赖 [03b10a8]
  - @arizeai/phoenix-client@6.0.0

## 0.6.0

### 次版本变更

- 67e8111: 添加 `px api graphql` 命令，对 Phoenix API 执行原始 GraphQL 查询。仅允许查询，拒绝变更和订阅。输出为格式化 JSON，适合通过管道传给 `jq`。

### 补丁变更

- 更新依赖 [db24319]
- 更新依赖 [b18325b]
  - @arizeai/phoenix-client@5.9.0
  - @arizeai/phoenix-config@0.1.1

## 0.5.2

### 补丁变更

- 更新依赖 [8be1940]
  - @arizeai/phoenix-client@5.8.2

## 0.5.1

### 补丁变更

- @arizeai/phoenix-client@5.8.1

## 0.5.0

### 次版本变更

- 27f5470: 添加 px auth status 命令

## 0.4.0

### 次版本变更

- af4dc46: 为 Phoenix CLI 添加提示词内省命令
  - `px prompts`：列出全部可用提示词及名称和说明
  - `px prompt <identifier>`：显示指定提示词，支持 `--tag` 和 `--version` 选项
  - `--format text`：使用 XML 风格角色标签输出提示词内容，以便通过管道传给 Claude Code 等 AI 助手
  - 美化输出现在包含完整工具定义及参数、类型和说明
  - 为 phoenix-client 添加 `listPrompts` 函数

### 补丁变更

- 更新依赖 [af4dc46]
  - @arizeai/phoenix-client@5.8.0

## 0.3.1

### 补丁变更

- 更新依赖 [01eb1fb]
  - @arizeai/phoenix-client@5.7.0

## 0.3.0

### 次版本变更

- c71dc1d: 为 CLI 添加标注参数

## 0.2.0

### 次版本变更

- 32343ff: 为 CLI 添加数据集和实验命令：

  - `px datasets`：列出全部可用 Phoenix 数据集及示例数量和元数据
  - `px dataset <name-or-id>`：从数据集获取示例，支持可选的 `--split` 和 `--version` 过滤器
  - `px experiments --dataset <name-or-id>`：列出数据集实验，可选将完整实验数据导出到目录
  - `px experiment <experiment-id>`：获取单个实验及全部运行数据、评估和追踪 ID

  所有命令都支持 `--format pretty|json|raw` 输出模式，兼顾人工阅读与机器处理。

## 0.1.0

### 次版本变更

- d69eb80: 初始追踪导出 API

## 0.0.4

### 补丁变更

- 4208604: 触发 changeset 发布

## 0.0.3

### 补丁变更

- c96475c: 触发 changeset 发布

## 0.0.2

### 补丁变更

- 857b617: 添加包链接

## 0.0.1

### 补丁变更

- 30242a6: 初始 CLI
