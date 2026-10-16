# @arizeai/phoenix-testing

工作区内部测试工具，使用 [MSW（Mock Service Worker）](https://mswjs.io/) 模拟 Phoenix 服务器。请求处理器在运行时通过 [`@mswjs/source`](https://source.mswjs.io/) 从仓库的 OpenAPI 定义（`schemas/openapi.json`）生成，因此每个文档化端点都会返回符合模式的响应，无需手写模拟代码。

此包为私有包，仅支持在 Phoenix pnpm 工作区内部使用。

<a id="usage"></a>

## 用法

<a id="mock-every-phoenix-endpoint-nodejs-test-runners"></a>

### 模拟所有 Phoenix 端点（Node.js 测试运行器）

```ts
// vitest example
import { createMockServer } from "@arizeai/phoenix-testing/node";
import { afterAll, afterEach, beforeAll } from "vitest";

const server = await createMockServer();

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

Phoenix OpenAPI 定义中的每个操作都会返回根据其响应模式（或存在的示例）生成的数据。默认情况下，处理器绑定到 `http://localhost:6006`，与 `@arizeai/phoenix-client` 的默认基础 URL 一致，可通过 `baseUrl` 选项修改。

<a id="pin-down-specific-responses-type-safely"></a>

### 以类型安全的方式指定响应

`createHttp` 返回绑定到 Phoenix API `paths` 的 [`openapi-msw`](https://github.com/christoph-fricke/openapi-msw) `http` 命名空间。路径、路径参数、请求体和响应体都会依据 OpenAPI 定义进行类型检查：

```ts
import { createHttp } from "@arizeai/phoenix-testing";

const http = createHttp();

server.use(
  http.get("/v1/datasets/{id}", ({ params, response }) =>
    response(200).json({
      data: {
        id: params.id,
        name: "my dataset",
        description: null,
        metadata: {},
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        example_count: 7,
      },
    })
  )
);
```

传给 `createMockServer({ handlers })` 或通过 `server.use(...)` 注册的处理器优先于生成的处理器，因此测试可精确指定关注的响应，其他端点仍返回生成的占位数据。

## API

| 导出                                              | 说明                                                                               |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `createMockServer({ baseUrl, handlers })` (`/node`) | Node.js MSW 服务器，为每个 Phoenix 端点提供生成的处理器。                |
| `Server` (`/node`)                                  | `createMockServer` 返回的模拟服务器类型。                                      |
| `createOpenApiHandlers({ baseUrl })`                | 生成的 MSW 请求处理器，可组合到自定义配置中。                    |
| `createHttp({ baseUrl })`                           | 类型安全的 `http` 命名空间，用于编写覆盖默认行为的 Phoenix 处理器。                  |
| `getOpenApiDocument({ baseUrl })`                   | 工作区 Phoenix OpenAPI 文档的副本，其中 `servers` 指向 `baseUrl`。   |
| `DEFAULT_MOCK_BASE_URL`                             | `"http://localhost:6006"`：处理器绑定的默认基础 URL。                   |
| `pathsV1`, `componentsV1`, `operationsV1`           | 从 Phoenix API 定义生成的 OpenAPI 类型（通过 `openapi-typescript`）。       |
| `*` （重新导出的 `msw`）                             | `msw` 的全部导出，用于原始（非 OpenAPI）处理器，例如 GraphQL 或第三方主机。 |

<a id="regenerating-the-mocks"></a>

## 重新生成模拟

生成的 OpenAPI 类型源自仓库根目录的 `schemas/openapi.json`：

```bash
pnpm run generate
```

每次构建前都会自动运行（`prebuild`）。
