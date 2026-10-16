<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-mcp">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        Arize Phoenix MCP 服务器
    </div>
</h1>

<p align="center">
    <a href="https://www.npmjs.com/package/@arizeai/phoenix-mcp">
        <img src="https://img.shields.io/npm/v/%40arizeai%2Fphoenix-mcp" alt="NPM 版本">
    </a>
    <a href="https://github.com/Arize-ai/phoenix/blob/main/js/packages/phoenix-mcp/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="许可证">
    </a>
    <img src="https://badge.mcpx.dev?status=on" title="已启用 MCP"/>
    <a href="https://cursor.com/install-mcp?name=phoenix&config=eyJjb21tYW5kIjoibnB4IC15IEBhcml6ZWFpL3Bob2VuaXgtbWNwQGxhdGVzdCAtLWJhc2VVcmwgaHR0cDovL2xvY2FsaG9zdDo2MDA2IC0tYXBpS2V5IHlvdXItYXBpLWtleSJ9">
        <img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="将 Arize Phoenix MCP 服务器添加到 Cursor" height=20 />
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=js/packages/phoenix-mcp/README.md" />
</p>

Phoenix MCP 服务器是面向 Arize Phoenix 平台的模型上下文协议实现，为 Phoenix 的功能提供统一接口。

Phoenix MCP 服务器可用于：

- **项目管理**：列出并浏览用于组织可观测性数据的项目
- **追踪、Span 和标注**：获取追踪、Span 及标注配置，用于分析和调试
- **会话**：浏览对话流程和会话级标注
- **提示词管理**：创建、列出、更新和迭代提示词
- **数据集**：浏览数据集并合成新示例
- **实验**：拉取实验结果，并借助 LLM 进行可视化

没有找到你的使用场景？`@arizeai/phoenix-mcp` 是[开源项目](https://github.com/Arize-ai/phoenix)！欢迎提交 Issue 和 PR。

<a id="installation"></a>

## 安装

此 MCP 服务器可通过 `npx` 使用，并可直接集成到 Claude Desktop、Cursor 等客户端。

```json
{
  "mcpServers": {
    "phoenix": {
      "command": "npx",
      "args": [
        "-y",
        "@arizeai/phoenix-mcp@latest",
        "--baseUrl",
        "https://my-phoenix.com",
        "--apiKey",
        "your-api-key"
      ]
    }
  }
}
```

<a id="development"></a>

## 开发

<a id="install"></a>

## 安装

此包通过 pnpm 工作区管理。

```sh
// From the /js/ directory
pnpm install
pnpm build
```

只有依赖或 phoenix-client 发生变化时才需要重复执行。

<a id="building"></a>

### 构建

构建项目：

```sh
pnpm build
```

<a id="development-mode"></a>

### 开发模式

以开发模式运行：

```bash
pnpm dev
```

<a id="debugging"></a>

### 调试

可通过以下命令构建并运行 MCP 检查器：

```bash
pnpm inspect
```

<a id="environment-variables"></a>

## 环境变量

开发时，服务器需要以下环境变量：

- `PHOENIX_API_KEY`: 你的 Phoenix API 密钥
- `PHOENIX_ENDPOINT`: Phoenix 基础 URL
- `PHOENIX_PROJECT`: 项目范围工具使用的可选默认项目（别名：`PHOENIX_PROJECT_NAME`）
- `PHOENIX_CLIENT_HEADERS`: 可选的 JSON 编码请求头

请在 `.env` 文件中设置这些变量，参考 `.env.example`。

运行时，服务器还会发现工作目录或其上级目录中最近的 `.env.phoenix` 文件。进程环境变量和命令行选项优先。如果较高优先级的 API 密钥与文件中的端点组合使用，服务器会发出一次警告后继续。设置 `PHOENIX_DISCOVER_CONFIG=false` 可禁用发现。

<a id="tool-coverage"></a>

## 工具覆盖范围

MCP 服务器覆盖 Phoenix 的主要操作流程：

**提示词** — `list-prompts`, `get-prompt`, `get-latest-prompt`, `get-prompt-by-identifier`, `get-prompt-version`, `list-prompt-versions`, `get-prompt-version-by-tag`, `list-prompt-version-tags`, `add-prompt-version-tag`, `upsert-prompt`

**项目** — `list-projects`, `get-project`

**追踪** — `list-traces`, `get-trace`

**Span** — `get-spans`, `get-span-annotations`

**会话** — `list-sessions`, `get-session`

**标注配置** — `list-annotation-configs`

**数据集** — `list-datasets`, `get-dataset`, `get-dataset-examples`, `get-dataset-experiments`, `add-dataset-examples`

**实验** — `list-experiments-for-dataset`, `get-experiment-by-id`

搜索 Phoenix 文档时，请使用独立的 Phoenix Docs MCP 服务器，不要使用此包。

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
- 🗺️ 查看我们的[路线图](https://github.com/orgs/Arize-ai/projects/45)，了解未来方向。

<a id="license"></a>

## 许可证

Apache 2.0
