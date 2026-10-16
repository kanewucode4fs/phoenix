<a id="arize-phoenix-plugin"></a>

# Arize Phoenix 插件

这是一个 [Codex 插件](https://developers.openai.com/codex/plugins)，采用可移植的 [Agent Plugins](https://agent-plugins.org) 格式。它注册 Phoenix [远程 MCP 服务](https://arize.com/docs/phoenix/integrations/remote-mcp)，使 Codex 能够探索 Phoenix 实例中的追踪记录、会话、数据集、实验和评估。

<a id="how-it-connects"></a>

## 连接方式

插件的 MCP URL 不能包含环境变量，因此插件注册的是一个小型 stdio 启动器 `scripts/phoenix-mcp`，而非固定 URL。启动器读取环境变量，并通过 `npx` 使用 [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) 桥接到 `<PHOENIX_ENDPOINT>/mcp`。

| 变量 | 作用 |
| -------- | ------ |
| `PHOENIX_ENDPOINT` | Phoenix 实例的基础 URL，例如 `https://phoenix.example.com`。默认值为 `http://localhost:6006`。 |
| `PHOENIX_API_KEY` | 可选。设置后，请求将携带此值作为 Bearer 令牌，无需浏览器登录。启动器将未展开的 `${PHOENIX_API_KEY}` 引用传给 `mcp-remote`，由后者从环境变量解析，因此密钥不会出现在进程参数中。否则，Codex 会在首次使用时打开浏览器，让你登录 Phoenix 账户。 |

这些变量与 `px` CLI 读取的变量相同。请在启动 Codex 的 shell 中导出。Codex 只转发插件声明的变量，因此 `mcp.json` 和 `.mcp.json` 中都列出了这两个变量。

需要 Node.js，以及提供 `/mcp` 接口的 Phoenix 19.0.0 或更高版本。

<a id="files"></a>

## 文件说明

| 文件 | 用途 |
| ---- | ------- |
| `plugin.json`, `mcp.json` | 可移植清单和 MCP 服务声明。 |
| `.codex-plugin/plugin.json`, `.mcp.json` | Codex 覆盖配置，将 `mcp.json` 中的 `${VAR}` 条目转换为转发的环境变量。Codex 先读取可移植文件，覆盖配置仅添加 `env_vars`。 |
| `scripts/phoenix-mcp` | stdio 启动器。 |

<a id="install-locally"></a>

## 本地安装

在仓库根目录运行：

```bash
codex plugin marketplace add .
codex plugin add arize-phoenix@arize-phoenix
```

在 Codex 中运行 `/mcp`，确认 `phoenix` 服务已连接。
