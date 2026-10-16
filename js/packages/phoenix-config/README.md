<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-config">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        @arizeai/phoenix-config
    </div>
</h1>

<p align="center">
    <a href="https://www.npmjs.com/package/@arizeai/phoenix-config">
        <img src="https://img.shields.io/npm/v/%40arizeai%2Fphoenix-config" alt="NPM 版本">
    </a>
    <a href="https://arize-ai.github.io/phoenix/">
        <img src="https://img.shields.io/badge/docs-blue?logo=typescript&logoColor=white" alt="文档">
    </a>
</p>

供 `@arizeai/phoenix-otel` 和 `@arizeai/phoenix-client` 共用的配置解析工具，提供读取 Phoenix 环境变量的类型化辅助函数。

<a id="installation"></a>

## 安装

```bash
npm install @arizeai/phoenix-config
```

<a id="environment-variables"></a>

## 环境变量

| 变量                     | 常量                         | 说明                                                                   |
| ---------------------------- | -------------------------------- | ----------------------------------------------------------------------------- |
| `PHOENIX_ENDPOINT`           | `ENV_PHOENIX_ENDPOINT`           | 访问 API 的 Phoenix 基础 URL                                               |
| `PHOENIX_HOST`               | `ENV_PHOENIX_HOST`               | Phoenix 服务器绑定主机；仅作为 API 基础 URL 的旧版回退读取 |
| `PHOENIX_API_KEY`            | `ENV_PHOENIX_API_KEY`            | Phoenix 身份验证的 API 密钥                                            |
| `PHOENIX_CLIENT_HEADERS`     | `ENV_PHOENIX_CLIENT_HEADERS`     | 客户端请求的 JSON 编码自定义请求头                               |
| `PHOENIX_COLLECTOR_ENDPOINT` | `ENV_PHOENIX_COLLECTOR_ENDPOINT` | OTel 收集器端点 URL                                                   |
| `PHOENIX_PORT`               | `ENV_PHOENIX_PORT`               | Phoenix HTTP 端口（整数）                                                   |
| `PHOENIX_GRPC_PORT`          | `ENV_PHOENIX_GRPC_PORT`          | Phoenix OpenTelemetry gRPC 端口（整数）                                 |
| `PHOENIX_PROJECT`            | `ENV_PHOENIX_PROJECT`            | 项目范围操作的默认项目名称（规范变量）                |
| `PHOENIX_PROJECT_NAME`       | `ENV_PHOENIX_PROJECT_NAME`       | `PHOENIX_PROJECT` 的受支持别名                                         |
| `PHOENIX_LOG_LEVEL`          | `ENV_PHOENIX_LOG_LEVEL`          | 日志详细程度：`debug`、`info`、`warn`、`error` 或 `silent`                  |
| `PHOENIX_DISCOVER_CONFIG`    | `ENV_PHOENIX_DISCOVER_CONFIG`    | 设为 `false` 可禁用 `.env.phoenix` 文件发现                       |

<a id="credential-file-discovery-envphoenix"></a>

## 凭证文件发现（`.env.phoenix`）

进程环境中未设置某个 Phoenix 配置时，辅助函数从当前工作目录开始向文件系统根目录逐级查找 `.env.phoenix`，在首个匹配处停止，并读取其中以 `PHOENIX_` 为前缀的键（dotenv 格式）：

在该文件中存储凭证前，请将 `.env.phoenix` 加入仓库忽略规则（Phoenix 仓库已忽略它）。

```bash
# .env.phoenix
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
PHOENIX_API_KEY=your-api-key
```

进程环境变量始终优先，文件绝不会覆盖已设置的值，不以 `PHOENIX_` 为前缀的键会被忽略。关联配置按组解析：只要进程环境设置了任一凭证（`PHOENIX_API_KEY`、`PHOENIX_CLIENT_HEADERS`），整个凭证组都会忽略文件，因此绝不会混用进程和文件中的凭证。设置 `PHOENIX_DISCOVER_CONFIG=false` 可完全禁用发现。

`.env.phoenix` 中的端点仍可与显式提供或进程环境提供的凭证组合使用。这种情况下，使用方会发出一次性警告，指出凭证来源、端点变量和发现的文件；绝不记录凭证值。需要感知来源的使用方应使用 `getStrFromEnvironmentWithSource()` 和 `getCredentialsFromEnvironmentWithSource()`，不要自行重建来源层级。

发现结果按工作目录缓存，持续整个进程生命周期（包括未发现文件的结果）。长期运行的进程若在首次配置查询后才创建文件，可调用 `clearEnvFileCache()` 重新发现。

<a id="usage"></a>

## 用法

<a id="reading-all-configuration"></a>

### 读取全部配置

```typescript
import { getEnvironmentConfig } from "@arizeai/phoenix-config";

const config = getEnvironmentConfig();
// Returns a typed object with all recognized Phoenix env vars:
// {
//   PHOENIX_HOST: "http://localhost:6006",
//   PHOENIX_API_KEY: "my-key",
//   PHOENIX_CLIENT_HEADERS: { "X-Custom": "value" },
//   PHOENIX_COLLECTOR_ENDPOINT: "http://localhost:6006",
//   PHOENIX_PORT: 6006,
//   PHOENIX_GRPC_PORT: 4317,
//   PHOENIX_LOG_LEVEL: "info",
//   PHOENIX_PROJECT: "my-project",
// }
```

<a id="resolving-the-project-name"></a>

### 解析项目名称

`PHOENIX_PROJECT` 是规范项目名称变量，`PHOENIX_PROJECT_NAME` 是受支持别名。使用 `getProjectFromEnvironment()` 按正确优先级解析两者（`PHOENIX_PROJECT` 优先；若两者设置为冲突值，会发出一次性警告）：

```typescript
import { getProjectFromEnvironment } from "@arizeai/phoenix-config";

const project = getProjectFromEnvironment();
// Reads PHOENIX_PROJECT, then PHOENIX_PROJECT_NAME, or undefined if neither is set
```

<a id="reading-individual-values"></a>

### 读取单个值

```typescript
import {
  getStrFromEnvironment,
  getIntFromEnvironment,
  getHeadersFromEnvironment,
  ENV_PHOENIX_ENDPOINT,
  ENV_PHOENIX_PORT,
  ENV_PHOENIX_CLIENT_HEADERS,
} from "@arizeai/phoenix-config";

// Read a string environment variable
const endpoint = getStrFromEnvironment(ENV_PHOENIX_ENDPOINT);
// Returns "http://localhost:6006" or undefined

// Read an integer environment variable
const port = getIntFromEnvironment(ENV_PHOENIX_PORT);
// Returns 6006 or undefined

// Read and parse a JSON-encoded headers object
const headers = getHeadersFromEnvironment(ENV_PHOENIX_CLIENT_HEADERS);
// Returns { "Authorization": "Bearer token" } or undefined
```

<a id="using-constants"></a>

### 使用常量

```typescript
import {
  ENV_PHOENIX_ENDPOINT,
  ENV_PHOENIX_HOST,
  ENV_PHOENIX_API_KEY,
  ENV_PHOENIX_CLIENT_HEADERS,
  ENV_PHOENIX_COLLECTOR_ENDPOINT,
  ENV_PHOENIX_PORT,
  ENV_PHOENIX_GRPC_PORT,
  ENV_PHOENIX_PROJECT_NAME,
  ENV_PHOENIX_PROJECT,
  ENV_PHOENIX_LOG_LEVEL,
} from "@arizeai/phoenix-config";

// Use constants instead of raw strings to avoid typos
const apiKey = process.env[ENV_PHOENIX_API_KEY];
```

<a id="types"></a>

## 类型

```typescript
import type { EnvironmentConfig } from "@arizeai/phoenix-config";
// Inferred return type of getEnvironmentConfig()
```

<a id="community"></a>

## 社区

加入我们的社区，与数千名 AI 开发者交流：

- 🌍 加入我们的 [Slack 社区](https://join.slack.com/t/arize-ai/shared_invite/zt-3r07iavnk-ammtATWSlF0pSrd1DsMW7g).
- 📚 阅读 [Phoenix 文档](https://arize.com/docs/phoenix).
- 💡 在 _#phoenix-support_ 频道提问并反馈。
- 🌟 为我们的 [GitHub](https://github.com/Arize-ai/phoenix) 加星。
- 🐞 通过 [GitHub Issues](https://github.com/Arize-ai/phoenix/issues) 报告问题。
- 𝕏 在 [𝕏](https://twitter.com/ArizePhoenix) 关注我们。
- 💼 在 [LinkedIn](https://www.linkedin.com/showcase/113218220) 关注我们。
