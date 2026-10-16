# @arizeai/phoenix-otel

## 2.2.0

### 次版本变更

- 5420522: `register()` 现在从按优先级排列的链解析追踪导出目的地，不再仅使用 `PHOENIX_COLLECTOR_ENDPOINT`：依次为显式 `url`、`PHOENIX_COLLECTOR_ENDPOINT`、OpenTelemetry 标准 `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`（依规范原样使用）和 `OTEL_EXPORTER_OTLP_ENDPOINT`（追加 OTLP 追踪路径的基础 URL）、`PHOENIX_ENDPOINT`，最后为 `http://localhost:6006`。

  设置了 `PHOENIX_COLLECTOR_ENDPOINT` 的配置不变。变化针对此前丢失全部 Span 的情况：仅设置 `PHOENIX_ENDPOINT` 或 OpenTelemetry 变量时，此前会导出到没有服务监听的 localhost。现在这些 Span 会到达指定服务器。追踪导出的解析来源优先级低于 `PHOENIX_COLLECTOR_ENDPOINT` 时，会输出信息行说明哪个变量提供目的地，使解析过程可见。

  `PHOENIX_COLLECTOR_ENDPOINT` 可接收基础 URL 或完整 OTLP 追踪 URL：缺少 `/v1/traces` 路径时追加，已存在时保持；该路径中的双分隔符或尾部斜杠会被规范化，使导出器直接访问正确路由。空值和纯空白值视为未设置，回退到下一变量。

### 补丁变更

- 更新依赖 [d04f0fc]
  - @arizeai/phoenix-config@0.5.0

## 2.1.0

### 次版本变更

- dc451a6: 从包根入口重新导出 `OTLPTraceExporter`，并添加仅支持 ESM 的 `@arizeai/phoenix-otel/vercel` 子路径，重新导出 `@arizeai/openinference-vercel`（Span 处理器、`isOpenInferenceSpan` 和类型）。自定义 Span 处理器配置（如通过 `register()` 的 `spanProcessors` 选项过滤 Vercel AI SDK / Eve 追踪）现在可从 `@arizeai/phoenix-otel` 导入全部所需内容，无需安装底层包。

## 2.0.0

### 主版本变更

- 30f0827: 将 `@arizeai/openinference-vercel` 升级到 v3，它将 AI SDK v7（`@ai-sdk/otel`）Span 转换为 OpenInference。AI SDK 遥测仍需应用显式配置，因为其注册表作用于整个进程。此包保留最低 Node.js 18 要求及 ESM/CommonJS 入口：由于 `@arizeai/openinference-vercel` v3 仅支持 ESM，OpenInference Span 处理器通过动态导入延迟加载（加载完成前记录的 Span 会缓冲后重放），并导出 `LazyOpenInferenceSpanProcessor` 支持自定义提供程序配置。不再转换 AI SDK v6 Span；AI SDK v6 请继续使用 1.x。

## 1.2.0

### 次版本变更

- f94067b: 添加 px setup 脚本，用于 Agent 接入引导

### 补丁变更

- 更新依赖 [f94067b]
  - @arizeai/phoenix-config@0.4.0

## 1.1.1

### 补丁变更

- c0ab6a9: 新增 `.env.phoenix` 文件发现，作为 Phoenix 配置的回退来源。进程环境中不存在某项配置时，`@arizeai/phoenix-config` 从当前工作目录向上查找最近的 `.env.phoenix` 文件，并读取以 `PHOENIX_` 为前缀的键（dotenv 格式）。进程环境值优先，相关配置（凭证、OTel 端点/端口）从同一来源按组解析。忽略非当前用户拥有的文件；对跳过的文件、其他用户可访问的文件，以及与不同来源凭证配对的端点发出一次性警告。设置 `PHOENIX_DISCOVER_CONFIG=false` 禁用发现；调用 `clearEnvFileCache()` 刷新缓存结果。浏览器构建通过条件包导出选择不依赖 Node 的实现。`@arizeai/phoenix-cli` 将发现值的优先级置于配置档案之下；`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 通过共享解析逻辑读取 `.env.phoenix` 值。
- 更新依赖 [c0ab6a9]
  - @arizeai/phoenix-config@0.3.0

## 1.1.0

### 次版本变更

- 1e7d9fc: 统一各 TypeScript 包的项目名称环境变量：所有接口现在都读取 `PHOENIX_PROJECT`（规范变量）和 `PHOENIX_PROJECT_NAME`（受支持别名），`PHOENIX_PROJECT` 优先，显式参数/标志仍高于两者。两者设为冲突值时，使用规范变量的值，并发出一次性警告列出两个值。`@arizeai/phoenix-config` 是该解析逻辑的唯一实现位置：提供共享的 `getProjectFromEnvironment()` 解析器，并在 `getEnvironmentConfig()` 中包含解析后的项目。`@arizeai/phoenix-cli`、`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 均使用它；`@arizeai/phoenix-otel` 现在依赖 `@arizeai/phoenix-config`，未传入 `projectName` 时，`register()` 通过共享解析器回退到这些变量，不再重复实现逻辑。

### 补丁变更

- 更新依赖 [1e7d9fc]
  - @arizeai/phoenix-config@0.2.0

## 1.0.2

### 补丁变更

- 559acf8: 在 README 记录 `hideLLMTools` / `OPENINFERENCE_HIDE_LLM_TOOLS` 追踪配置选项

## 1.0.1

### 补丁变更

- 5d14f23: 在 README 的社区章节添加 LinkedIn 链接。

## 1.0.0

### 主版本变更

- 1449f3d: 从 phoenix-otel 重新导出 OpenInference 语义约定，并更新 phoenix-client 从 phoenix-otel 导入，不再直接依赖 @arizeai/openinference-semantic-conventions。

## 0.4.3

### 补丁变更

- 1028be5: 将整理过的包文档和示例打包到 npm 包的 `docs/` 下。

## 0.4.2

### 补丁变更

- 03b10a8: 将 `@arizeai/phoenix-otel` 的 OpenTelemetry 依赖统一为兼容的 v2 版本集合。

## 0.4.1

### 补丁变更

- 7456462: 将 `DiagLogLevel` 重新导出为运行时值，便于使用方直接从 `@arizeai/phoenix-otel` 导入。

## 0.4.0

### 次版本变更

- a8896db: feat: 增强与 ai-sdk v6 遥测的兼容性

## 0.3.4

### 补丁变更

- 4208604: 触发 changeset 发布

## 0.3.3

### 补丁变更

- c96475c: 触发 changeset 发布

## 0.3.2

### 补丁变更

- 857b617: 添加包链接

## 0.3.1

### 补丁变更

- ce5febf: 规范化 URL，去除尾部斜杠

## 0.3.0

### 次版本变更

- 419ea76: feat: 升级 @arizeai/openinference-vercel，改善 AI SDK 支持

## 0.2.1

### 补丁变更

- 8bbff3a: README 示例

## 0.2.0

### 次版本变更

- de6f111: 重构为在整个客户端中使用 phoenix-otel

## 0.1.0

### 次版本变更

- 08c7419: 支持向 register 传入插桩"

## 0.0.1

### 补丁变更

- c9a35c3: phoenix-otel 首次发布
