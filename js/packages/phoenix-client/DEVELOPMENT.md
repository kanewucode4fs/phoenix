<a id="development-guide-for-arizeaiphoenix-client"></a>

# @arizeai/phoenix-client 开发指南

<a id="code-generation"></a>

## 代码生成

Phoenix 客户端通过代码生成保持 TypeScript 类型和 API 接口与后端 OpenAPI 模式同步。

- OpenAPI 模式（`openapi.json`）位于仓库根目录的 `schemas/` 中。
- 客户端使用 [`openapi-typescript`](https://github.com/drwpow/openapi-typescript) 从该模式生成 TypeScript 类型和 API 接口。
- 生成代码输出到 `phoenix-client` 包的 `src/__generated__/api/v1.ts`。

<a id="how-to-regenerate-the-client"></a>

### 如何重新生成客户端

若 OpenAPI 模式变化（例如更新后端或拉取新变更后）：

1. 确保 `schemas/` 目录中的 `openapi.json` 为最新版本。
2. 在 `phoenix-client` 目录运行代码生成脚本：

   ```sh
   pnpm run generate
   ```

3. 如有变化，提交更新后的生成文件。

**注意：** OpenAPI 模式变化时，务必重新生成并提交代码，确保客户端保持最新。
