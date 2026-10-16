<a id="arize-phoenix-plugin-for-claude-code"></a>

# 面向 Claude Code 的 Arize Phoenix 插件

这是一个 [Claude Code 插件](https://code.claude.com/docs/en/plugins)，用于将 Claude Code 连接到你的 Phoenix 实例。它注册 Phoenix [远程 MCP 服务](https://arize.com/docs/phoenix/integrations/remote-mcp)，并附带公开的 Phoenix 技能，使 Claude Code 能够探索追踪记录、运行评估并为应用接入插桩。

<a id="what-you-get"></a>

## 提供的能力

| 组件 | 说明 |
| --------- | ---------- |
| `phoenix` MCP 服务 | 通过 Streamable HTTP 连接 `<PHOENIX_ENDPOINT>/mcp`。默认连接本地 Phoenix：`http://localhost:6006`。首次使用时在浏览器中登录 Phoenix 账户。 |
| `phoenix-cli` 技能 | 使用 `px` CLI 获取追踪记录、检查数据集和实验，以及查询 GraphQL。 |
| `phoenix-evals` 技能 | 构建和运行评估器。 |
| `phoenix-tracing` 技能 | 使用 OpenInference 为应用接入插桩。 |

这些技能通过符号链接指向 [`.agents/skills/`](../../../.agents/skills/) 中的公开技能。Claude Code 安装插件时会复制解析后的文件，因此仓库内无需重复保存。

<a id="configure"></a>

## 配置

插件只有一个设置项：**Phoenix 端点**。启用插件时，Claude Code 会询问该值。请填写不带末尾斜杠的 Phoenix 基础 URL，例如 `https://phoenix.example.com`。本地 Phoenix 可保留默认值 `http://localhost:6006`。插件会自动追加 `/mcp`。

非交互安装时，可向 `claude plugin install` 传入 `--config endpoint=https://phoenix.example.com`。之后要修改，可在 Claude Code 中运行 `/plugin configure arize-phoenix@arize-phoenix`，或编辑用户设置（`~/.claude/settings.json`）中的 `pluginConfigs`：

```json
{
  "pluginConfigs": {
    "arize-phoenix@arize-phoenix": {
      "options": { "endpoint": "https://phoenix.example.com" }
    }
  }
}
```

此设置仅配置 MCP 服务。`phoenix-cli` 技能使用的 `px` CLI 会从 shell 读取 `PHOENIX_ENDPOINT`；如果 Phoenix 启用了认证，还会读取 `PHOENIX_API_KEY`，因此也需要导出这些变量。

MCP 服务通过浏览器中的 OAuth 登录，不提供 API 密钥设置项。无界面使用时，请自行注册服务：`px setup mcp --agent claude --header 'Authorization: Bearer ${PHOENIX_API_KEY}'`。

需要提供 `/mcp` 接口的 Phoenix 19.0.0 或更高版本。

<a id="install"></a>

## 安装

```bash
claude plugin marketplace add Arize-ai/phoenix
claude plugin install arize-phoenix@arize-phoenix
```

在 Claude Code 中运行 `/mcp`，确认 `phoenix` 服务已连接，并完成登录。

本地开发时，可从检出的代码添加插件市场：在仓库根目录运行 `claude plugin marketplace add ./`。末尾斜杠不可省略，单独的 `.` 会被判为无效来源。

使用 `claude plugin validate plugins/claude/arize-phoenix` 检查改动。它会警告三个 `skills/` 条目是未被跟随的符号链接；这是预期现象，因为 `validate` 读取组件时不会跟随符号链接，而会话加载插件时会跟随。对已安装副本运行 `claude plugin details arize-phoenix@arize-phoenix`，可确认解析后的清单：三个技能和一个 MCP 服务。

<a id="evals"></a>

## 评测

插件行为测试位于 `evals/`，可从本目录运行 `claude plugin eval .`。用例格式、评分器、MCP 模拟服务和 CI 用法见[使用评测测试插件](https://code.claude.com/docs/en/plugin-evals)。`evals/results/` 中的运行输出已被 Git 忽略。
