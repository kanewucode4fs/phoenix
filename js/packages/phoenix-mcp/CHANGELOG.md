# @arizeai/phoenix-mcp

## 4.3.16

### 补丁变更

- 更新依赖 [7b9f900]
  - @arizeai/phoenix-client@7.16.1

## 4.3.15

### 补丁变更

- 更新依赖 [f8ae2fc]
  - @arizeai/phoenix-client@7.16.0

## 4.3.14

### 补丁变更

- 更新依赖 [5b37f12]
  - @arizeai/phoenix-client@7.15.0

## 4.3.13

### 补丁变更

- 更新依赖 [aab229f]
  - @arizeai/phoenix-client@7.14.0

## 4.3.12

### 补丁变更

- 更新依赖 [c282563]
  - @arizeai/phoenix-client@7.13.0

## 4.3.11

### 补丁变更

- 更新依赖 [dab09f1]
  - @arizeai/phoenix-client@7.12.0

## 4.3.10

### 补丁变更

- 更新依赖 [2b73847]
  - @arizeai/phoenix-client@7.11.0

## 4.3.9

### 补丁变更

- 更新依赖 [c839254]
  - @arizeai/phoenix-client@7.10.0

## 4.3.8

### 补丁变更

- 更新依赖 [bf047af]
  - @arizeai/phoenix-client@7.9.0

## 4.3.7

### 补丁变更

- 更新依赖 [58b7017]
  - @arizeai/phoenix-client@7.8.0

## 4.3.6

### 补丁变更

- 更新依赖 [1cdff14]
  - @arizeai/phoenix-client@7.7.1

## 4.3.5

### 补丁变更

- 更新依赖 [37916d7]
- 更新依赖 [c48e50e]
- 更新依赖 [773c5e5]
- 更新依赖 [b27561d]
  - @arizeai/phoenix-client@7.7.0

## 4.3.4

### 补丁变更

- 更新依赖 [d328c3e]
  - @arizeai/phoenix-client@7.6.0

## 4.3.3

### 补丁变更

- 更新依赖 [0ed987a]
  - @arizeai/phoenix-client@7.5.0

## 4.3.2

### 补丁变更

- 更新依赖 [90729f3]
  - @arizeai/phoenix-client@7.4.0

## 4.3.1

### 补丁变更

- 更新依赖 [c892873]
  - @arizeai/phoenix-client@7.3.1

## 4.3.0

### 次版本变更

- e90ba00: 从 `PHOENIX_ENDPOINT` 解析 MCP 服务器基础 URL；仅设置追踪导出变量 `PHOENIX_COLLECTOR_ENDPOINT` 和 `OTEL_EXPORTER_OTLP_ENDPOINT` 时从中推断，最后使用旧版 `PHOENIX_HOST`，与 API 客户端及 `px` CLI 一致。此前 MCP 服务器仅读取 `PHOENIX_HOST`。

### 补丁变更

- 更新依赖 [d04f0fc]
  - @arizeai/phoenix-config@0.5.0
  - @arizeai/phoenix-client@7.3.0

## 4.2.8

### 补丁变更

- 更新依赖 [59aa7cb]
  - @arizeai/phoenix-client@7.2.0

## 4.2.7

### 补丁变更

- e35712a: 重新发布，以恢复失败的发布（版本已存在于 npm）
- 更新依赖 [e35712a]
  - @arizeai/phoenix-client@7.1.1

## 4.2.6

### 补丁变更

- 更新依赖 [df7057a]
  - @arizeai/phoenix-client@7.1.0

## 4.2.5

### 补丁变更

- 更新依赖 [a6c3f88]
  - @arizeai/phoenix-client@7.0.1

## 4.2.4

### 补丁变更

- 更新依赖 [4867e34]
  - @arizeai/phoenix-client@7.0.0

## 4.2.3

### 补丁变更

- @arizeai/phoenix-client@6.14.2

## 4.2.2

### 补丁变更

- @arizeai/phoenix-client@6.14.1

## 4.2.1

### 补丁变更

- 更新依赖 [d6b1cbb]
  - @arizeai/phoenix-client@6.14.0

## 4.2.0

### 次版本变更

- f94067b: 添加 px setup 脚本，用于 Agent 接入引导

### 补丁变更

- 更新依赖 [f94067b]
  - @arizeai/phoenix-client@6.13.0
  - @arizeai/phoenix-config@0.4.0

## 4.1.1

### 补丁变更

- c0ab6a9: 新增 `.env.phoenix` 文件发现，作为 Phoenix 配置的回退来源。进程环境中不存在某项配置时，`@arizeai/phoenix-config` 从当前工作目录向上查找最近的 `.env.phoenix` 文件，并读取以 `PHOENIX_` 为前缀的键（dotenv 格式）。进程环境值优先，相关配置（凭证、OTel 端点/端口）从同一来源按组解析。忽略非当前用户拥有的文件；对跳过的文件、其他用户可访问的文件，以及与不同来源凭证配对的端点发出一次性警告。设置 `PHOENIX_DISCOVER_CONFIG=false` 禁用发现；调用 `clearEnvFileCache()` 刷新缓存结果。浏览器构建通过条件包导出选择不依赖 Node 的实现。`@arizeai/phoenix-cli` 将发现值的优先级置于配置档案之下；`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 通过共享解析逻辑读取 `.env.phoenix` 值。
- 更新依赖 [c0ab6a9]
  - @arizeai/phoenix-config@0.3.0
  - @arizeai/phoenix-client@6.12.2

## 4.1.0

### 次版本变更

- 1e7d9fc: 统一各 TypeScript 包的项目名称环境变量：所有接口现在都读取 `PHOENIX_PROJECT`（规范变量）和 `PHOENIX_PROJECT_NAME`（受支持别名），`PHOENIX_PROJECT` 优先，显式参数/标志仍高于两者。两者设为冲突值时，使用规范变量的值，并发出一次性警告列出两个值。`@arizeai/phoenix-config` 是该解析逻辑的唯一实现位置：提供共享的 `getProjectFromEnvironment()` 解析器，并在 `getEnvironmentConfig()` 中包含解析后的项目。`@arizeai/phoenix-cli`、`@arizeai/phoenix-mcp` 和 `@arizeai/phoenix-otel` 均使用它；`@arizeai/phoenix-otel` 现在依赖 `@arizeai/phoenix-config`，未传入 `projectName` 时，`register()` 通过共享解析器回退到这些变量，不再重复实现逻辑。

### 补丁变更

- 更新依赖 [1e7d9fc]
  - @arizeai/phoenix-config@0.2.0
  - @arizeai/phoenix-client@6.12.1

## 4.0.19

### 补丁变更

- 更新依赖 [7947440]
  - @arizeai/phoenix-client@6.12.0

## 4.0.18

### 补丁变更

- 更新依赖 [7afa183]
  - @arizeai/phoenix-client@6.11.2

## 4.0.17

### 补丁变更

- 更新依赖 [a027ada]
  - @arizeai/phoenix-client@6.11.1

## 4.0.16

### 补丁变更

- 更新依赖 [7efabf6]
  - @arizeai/phoenix-client@6.11.0

## 4.0.15

### 补丁变更

- 4ce1b7d: 在 Phoenix REST 请求中显式发送 `User-Agent: phoenix-mcp` 头。Node 全局 `fetch`（undici）默认使用 `User-Agent: undici`，部分 Phoenix Cloud 边缘节点会因此以 302 重定向到 HTML 落地页，导致工具调用报 `Unexpected token < in JSON`。调用方提供的请求头仍优先（#13742）。

## 4.0.14

### 补丁变更

- 更新依赖 [0347f22]
  - @arizeai/phoenix-client@6.10.1

## 4.0.13

### 补丁变更

- 更新依赖 [6dceb10]
  - @arizeai/phoenix-client@6.10.0

## 4.0.12

### 补丁变更

- @arizeai/phoenix-client@6.9.3

## 4.0.11

### 补丁变更

- 更新依赖 [d0cc4c4]
  - @arizeai/phoenix-client@6.9.2

## 4.0.10

### 补丁变更

- 5d14f23: 在 README 的社区章节添加 LinkedIn 链接。
- 更新依赖 [5d14f23]
  - @arizeai/phoenix-config@0.1.4
  - @arizeai/phoenix-client@6.9.1

## 4.0.9

### 补丁变更

- 更新依赖 [2993b04]
- 更新依赖 [4e20267]
- 更新依赖 [2993b04]
  - @arizeai/phoenix-client@6.9.0

## 4.0.8

### 补丁变更

- 更新依赖 [e381885]
- 更新依赖 [187df7e]
  - @arizeai/phoenix-client@6.8.1

## 4.0.7

### 补丁变更

- 更新依赖 [a4dad8b]
  - @arizeai/phoenix-client@6.8.0

## 4.0.6

### 补丁变更

- 更新依赖 [e19a038]
  - @arizeai/phoenix-client@6.7.0

## 4.0.5

### 补丁变更

- 更新依赖 [8444575]
  - @arizeai/phoenix-client@6.6.2

## 4.0.4

### 补丁变更

- 更新依赖 [1449f3d]
  - @arizeai/phoenix-client@6.6.1

## 4.0.3

### 补丁变更

- 更新依赖 [c70eca6]
  - @arizeai/phoenix-client@6.6.0

## 4.0.2

### 补丁变更

- 更新依赖 [1028be5]
  - @arizeai/phoenix-client@6.5.5

## 4.0.1

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

## 4.0.0

### 主版本变更

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

### 补丁变更

- 更新依赖 [e4bdcf6]
  - @arizeai/phoenix-config@0.1.2
  - @arizeai/phoenix-client@6.5.3

## 3.1.5

### 补丁变更

- 更新依赖 [d204898]
  - @arizeai/phoenix-client@6.5.2

## 3.1.4

### 补丁变更

- 更新依赖 [91949d7]
  - @arizeai/phoenix-client@6.5.1

## 3.1.3

### 补丁变更

- 更新依赖 [9769f90]
  - @arizeai/phoenix-client@6.5.0

## 3.1.2

### 补丁变更

- 更新依赖 [83b7f68]
  - @arizeai/phoenix-client@6.4.0

## 3.1.1

### 补丁变更

- 更新依赖 [d951320]
  - @arizeai/phoenix-client@6.3.0

## 3.1.0

### 次版本变更

- 6d896e3: 为 `getSpans` 和 MCP `get-spans` 工具添加 `traceIds` 参数，按追踪 ID 过滤 Span。

### 补丁变更

- 更新依赖 [6d896e3]
  - @arizeai/phoenix-client@6.2.0

## 3.0.1

### 补丁变更

- 更新依赖 [b8ba989]
- 更新依赖 [6296d0a]
- 更新依赖 [6296d0a]
  - @arizeai/phoenix-client@6.1.0

## 3.0.0

### 主版本变更

- 03b10a8: feat: 将 zod 从 v3 升级到 v4

  破坏性变更：将 zod 从 v3 升级到 v4。这会改变使用
  `z.looseObject()`（此前为 `.passthrough()`）模式的 TypeScript 推断类型，现在其
  输出类型包含 `[x: string]: unknown`。使用这些类型的使用方可能需要
  更新代码。此外，`ZodError.errors` 已替换为
  `ZodError.issues`，`z.record()` 现在要求显式键模式，且
  `zod-to-json-schema` 已替换为原生 `z.toJSONSchema()`。

### 补丁变更

- 更新依赖 [03b10a8]
  - @arizeai/phoenix-client@6.0.0

## 2.3.7

### 补丁变更

- 更新依赖 [db24319]
- 更新依赖 [b18325b]
  - @arizeai/phoenix-client@5.9.0

## 2.3.6

### 补丁变更

- 更新依赖 [8be1940]
  - @arizeai/phoenix-client@5.8.2

## 2.3.5

### 补丁变更

- @arizeai/phoenix-client@5.8.1

## 2.3.4

### 补丁变更

- 更新依赖 [af4dc46]
  - @arizeai/phoenix-client@5.8.0

## 2.3.3

### 补丁变更

- 更新依赖 [01eb1fb]
  - @arizeai/phoenix-client@5.7.0

## 2.3.2

### 补丁变更

- 更新依赖 [ed59696]
  - @arizeai/phoenix-client@5.6.1

## 2.3.1

### 补丁变更

- 更新依赖 [0f2950e]
  - @arizeai/phoenix-client@5.6.0

## 2.3.0

### 次版本变更

- 5362ed2: 修复支持工具端点

### 补丁变更

- 更新依赖 [5132ce4]
  - @arizeai/phoenix-client@5.5.5

## 2.2.30

### 补丁变更

- 4208604: 触发 changeset 发布
- 更新依赖 [4208604]
  - @arizeai/phoenix-client@5.5.4

## 2.2.29

### 补丁变更

- c96475c: 触发 changeset 发布
- 更新依赖 [c96475c]
  - @arizeai/phoenix-client@5.5.3

## 2.2.28

### 补丁变更

- 857b617: 添加包链接
- 更新依赖 [857b617]
  - @arizeai/phoenix-client@5.5.2

## 2.2.27

### 补丁变更

- @arizeai/phoenix-client@5.5.1

## 2.2.26

### 补丁变更

- 更新依赖 [cb45336]
  - @arizeai/phoenix-client@5.5.0

## 2.2.25

### 补丁变更

- 更新依赖 [b87d2a4]
  - @arizeai/phoenix-client@5.4.1

## 2.2.24

### 补丁变更

- 更新依赖 [885be2a]
  - @arizeai/phoenix-client@5.4.0

## 2.2.23

### 补丁变更

- 更新依赖 [b000189]
- 更新依赖 [557865c]
- 更新依赖 [0c92232]
  - @arizeai/phoenix-client@5.3.0

## 2.2.22

### 补丁变更

- @arizeai/phoenix-client@5.2.1

## 2.2.21

### 补丁变更

- 更新依赖 [f9d8b06]
  - @arizeai/phoenix-client@5.2.0

## 2.2.20

### 补丁变更

- @arizeai/phoenix-client@5.1.1

## 2.2.19

### 补丁变更

- 更新依赖 [de6f111]
  - @arizeai/phoenix-client@5.1.0

## 2.2.18

### 补丁变更

- 更新依赖 [950fda5]
  - @arizeai/phoenix-client@5.0.0

## 2.2.17

### 补丁变更

- 更新依赖 [85430fa]
- 更新依赖 [c7cc7d9]
  - @arizeai/phoenix-client@4.2.0

## 2.2.16

### 补丁变更

- 更新依赖 [2981780]
  - @arizeai/phoenix-client@4.1.0

## 2.2.15

### 补丁变更

- 更新依赖 [e3a8ce2]
- 更新依赖 [c85780b]
  - @arizeai/phoenix-client@4.0.3

## 2.2.14

### 补丁变更

- 更新依赖 [1b71c66]
  - @arizeai/phoenix-client@4.0.2

## 2.2.13

### 补丁变更

- 更新依赖 [e72a9ad]
  - @arizeai/phoenix-client@4.0.1

## 2.2.12

### 补丁变更

- 更新依赖 [7732f99]
  - @arizeai/phoenix-client@4.0.0

## 2.2.11

### 补丁变更

- 更新依赖 [4f43901]
  - @arizeai/phoenix-client@3.2.0

## 2.2.10

### 补丁变更

- 更新依赖 [ee0c829]
  - @arizeai/phoenix-client@3.1.0

## 2.2.9

### 补丁变更

- 更新依赖 [8711bde]
- 更新依赖 [3e80a50]
  - @arizeai/phoenix-client@3.0.0

## 2.2.8

### 补丁变更

- 更新依赖 [fe55fc5]
  - @arizeai/phoenix-client@2.4.0

## 2.2.7

### 补丁变更

- 更新依赖 [83748e6]
  - @arizeai/phoenix-client@2.3.5

## 2.2.6

### 补丁变更

- a045486: 更新 phoenix-support-mcp

## 2.2.5

### 补丁变更

- 更新依赖 [20db91d]
  - @arizeai/phoenix-client@2.3.4

## 2.2.4

### 补丁变更

- 2609fcd: 将 JS 目标提升为 es2017，以使用原生 async
- 更新依赖 [2609fcd]
  - @arizeai/phoenix-client@2.3.3

## 2.2.3

### 补丁变更

- 更新依赖 [6ef8e47]
  - @arizeai/phoenix-client@2.3.2

## 2.2.2

### 补丁变更

- 更新依赖 [b3e30db]
  - @arizeai/phoenix-client@2.3.1

## 2.2.1

### 补丁变更

- 更新依赖 [3c97cc7]
  - @arizeai/phoenix-client@2.3.0

## 2.2.0

### 次版本变更

- 468f77b: 添加 phoenix-support 工具

## 2.1.11

### 补丁变更

- 更新依赖 [1906611]
- 更新依赖 [4c52db4]
  - @arizeai/phoenix-client@2.2.0

## 2.1.10

### 补丁变更

- 更新依赖 [5dd53be]
  - @arizeai/phoenix-client@2.1.1

## 2.1.9

### 补丁变更

- 更新依赖 [b162720]
  - @arizeai/phoenix-client@2.1.0

## 2.1.8

### 补丁变更

- 7f7aa06: 添加项目工具

## 2.1.7

### 补丁变更

- 更新依赖 [da7800a]
  - @arizeai/phoenix-client@2.0.1

## 2.1.6

### 补丁变更

- 更新依赖 [118e881]
  - @arizeai/phoenix-client@2.0.0

## 2.1.5

### 补丁变更

- 更新依赖 [536258e]
  - @arizeai/phoenix-client@1.3.0

## 2.1.4

### 补丁变更

- 更新依赖 [f7fae3b]
- 更新依赖 [9273417]
- 更新依赖 [4dd23c8]
  - @arizeai/phoenix-client@1.2.0

## 2.1.3

### 补丁变更

- 更新依赖 [fff5511]
  - @arizeai/phoenix-client@1.1.0

## 2.1.2

### 补丁变更

- 4cbb0e6: chore: 更新 README

## 2.1.1

### 补丁变更

- 37f766f: 更新 MCP 的 README

## 2.1.0

### 次版本变更

- a4f995d: 将 MCP 文件设为可执行命令
- 9f210de: 改为扁平结构

## 2.0.0

### 主版本变更

- 3acf533: feat(mcp): 首次发布 @arizeai/phoenix-mcp
