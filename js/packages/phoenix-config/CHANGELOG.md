# @arizeai/phoenix-config

## 0.5.0

### 次版本变更

- d04f0fc: 引入 `PHOENIX_ENDPOINT` 作为 API 访问的规范基础 URL，与用于追踪导出的 `PHOENIX_COLLECTOR_ENDPOINT` 配套。

  此前 TypeScript 客户端仅读取 `PHOENIX_HOST`，因此将 `PHOENIX_COLLECTOR_ENDPOINT` 指向远程 Phoenix 后再读取 Span，会静默访问 `http://localhost:6006`。客户端基础 URL 现在依次解析 `PHOENIX_ENDPOINT`、追踪导出变量 `PHOENIX_COLLECTOR_ENDPOINT` 和 `OTEL_EXPORTER_OTLP_ENDPOINT`（移除任何 `/v1/traces` 路径），最后使用旧版 `PHOENIX_HOST`，与 Python 客户端逐层一致，使相同环境从任一语言连接同一服务器。

  `PHOENIX_BASE_URL` 作为未文档化的兼容性回退，优先级低于追踪导出变量。客户端文档多年使用此名称，但没有代码读取它，因此依照文档设置的值此前无效；将其排在其他变量之后，可使这些配置开始生效，而不会重定向同时设置两者的用户。它也不再能够单独取代发现的 `.env.phoenix`，因此 shell 中遗留的旧值不会重定向 `px setup` 配置的项目。

  解析链中的空值和纯空白值现在均视为未设置，因此 `export PHOENIX_ENDPOINT=` 会回退到下一变量，不会使所有使用方滞留在 localhost。

  实验和测试套件追踪遵循与 `register()` 相同的规则：显式指定 `baseUrl` 创建的客户端将 Span 导出到该服务器；基础 URL 来自环境的客户端则由追踪导出变量决定。发现的 `.env.phoenix` 中存在无法解析的端点时，现在会警告后回退，不再中止运行，跨层级凭证警告也适用于此路径。

  `@arizeai/phoenix-config` 新增 `ENV_PHOENIX_ENDPOINT`、`ENV_OTEL_EXPORTER_OTLP_ENDPOINT`、`ENV_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`、`getBaseUrlFromEnvironment[WithSource]()`、`getBaseUrlFromValues()`（对注入的环境记录使用相同优先级）、`getTraceExportEndpointFromEnvironment()` 和 `PHOENIX_CONNECTION_ENV_KEYS`（用于保持测试环境整洁）。

## 0.4.0

### 次版本变更

- f94067b: 添加 px setup 脚本，用于 Agent 接入引导

## 0.3.0

### 次版本变更

- c0ab6a9: 新增 `.env.phoenix` 文件发现，作为 Phoenix 配置的回退来源。进程环境中不存在某项配置时，`@arizeai/phoenix-config` 从当前工作目录向上查找最近的 `.env.phoenix` 文件，并读取以 `PHOENIX_` 为前缀的键（dotenv 格式）。进程环境值优先，相关配置（凭证、OTel 端点/端口）从同一来源按组解析。忽略非当前用户拥有的文件；对跳过的文件、其他用户可访问的文件，以及与不同来源凭证配对的端点发出一次性警告。设置 `PHOENIX_DISCOVER_CONFIG=false` 禁用发现；调用 `clearEnvFileCache()` 刷新缓存结果。浏览器构建通过条件包导出选择不依赖 Node 的实现。`@arizeai/phoenix-cli` 将发现值的优先级置于配置档案之下；`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 通过共享解析逻辑读取 `.env.phoenix` 值。

## 0.2.0

### 次版本变更

- 1e7d9fc: 统一各 TypeScript 包的项目名称环境变量：所有接口现在都读取 `PHOENIX_PROJECT`（规范变量）和 `PHOENIX_PROJECT_NAME`（受支持别名），`PHOENIX_PROJECT` 优先，显式参数/标志仍高于两者。两者设为冲突值时，使用规范变量的值，并发出一次性警告列出两个值。`@arizeai/phoenix-config` 是该解析逻辑的唯一实现位置：提供共享的 `getProjectFromEnvironment()` 解析器，并在 `getEnvironmentConfig()` 中包含解析后的项目。`@arizeai/phoenix-cli`、`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 均使用它；`@arizeai/phoenix-otel` 现在依赖 `@arizeai/phoenix-config`，未传入 `projectName` 时，`register()` 通过共享解析器回退到这些变量，不再重复实现逻辑。

## 0.1.4

### 补丁变更

- 5d14f23: 在 README 的社区章节添加 LinkedIn 链接。

## 0.1.3

### 补丁变更

- b4ded15: 使用最新功能更新各包 README
  - phoenix-client：添加会话章节，说明 `listSessions`、`getSession` 和 `addSessionAnnotation`
  - phoenix-evals：添加完整预置评估器表格（简洁性、正确性、文档相关性、拒绝回答、工具评估器），修复 `bindEvaluator` 导入路径
  - phoenix-mcp：扩展工具覆盖范围章节，提供完整准确的工具列表
  - phoenix-config：以完整文档替换单行占位说明（安装、环境变量、使用示例）
  - phoenix-cli：添加 `px annotation-config` 命令文档

## 0.1.2

### 补丁变更

- e4bdcf6: 扩展 phoenix-mcp 服务器覆盖范围，并引入参数破坏性变更

  ### 破坏性变更

  - 工具参数重命名为 snake_case（`datasetIdentifier` → `dataset_id`/`dataset_name`、`experiment_id` 替代 `experiment_id`、`prompt_identifier`、`project_identifier` 等）
  - 移除 `resolveTraceIdByPrefix`，`get-trace` 现在要求精确追踪 ID
  - 移除旧版标识符回退模式（`requirePreferredIdentifier`、`legacyProjectIdentifier`）

  ### 新工具

  - `list-projects`, `get-project`, `list-traces`, `get-trace`, `get-spans`, `get-span-annotations`
  - `list-sessions`, `get-session`, `list-annotation-configs`, `phoenix-support`
  - `get-prompt-version-by-tag`, `list-prompt-version-tags`, `add-prompt-version-tag`

  ### 改进

  - 用通用 `fetchAllPages` 分页辅助函数替换重复的游标循环
  - 集中管理常量，去重 `extractSpanIds`，缓存 RunLLM 客户端
  - 将 `ENV_PHOENIX_PROJECT` 移到 `@arizeai/phoenix-config` 以便复用

## 0.1.1

### 补丁变更

- db24319: fix: 改进实验运行输出的格式和清晰度

## 0.1.0

### 次版本变更

- 0f2950e: 集中管理 Phoenix 配置
