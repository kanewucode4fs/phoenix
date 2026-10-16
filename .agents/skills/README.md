<a id="phoenix-coding-agent-skills"></a>

# Phoenix 编程智能体技能

本目录包含指导编程智能体使用 Phoenix 的[技能](https://docs.anthropic.com/en/docs/claude-code/skills)，可用于 Claude Code、Cursor 和其他兼容工具。

<a id="public-skills"></a>

## 公开技能

| 技能 | 说明 |
| ----- | ----------- |
| [phoenix-cli](phoenix-cli/) | 使用 Phoenix CLI 调试 LLM 应用：获取追踪，为跨度和追踪添加标注，分析错误，检查数据集，以及查询 GraphQL API。 |
| [phoenix-error-analysis](phoenix-error-analysis/) | 阅读抽样的追踪、跨度或会话，撰写自由格式笔记，再将其归纳为范围明确的单维度标注，并统计数量，以确定评测目标和修复优先级。 |
| [phoenix-evals](phoenix-evals/) | 使用 Phoenix 为 AI/LLM 应用构建、运行和验证评估器。优先使用代码，将需要细致判断的部分交给 LLM，并对照人工判断验证结果。 |
| [phoenix-tracing](phoenix-tracing/) | 使用 Phoenix 追踪 LLM 应用所需的 OpenInference 语义约定和埋点方法，涵盖配置、跨度类型和生产部署。 |

插件分发与开发配置是不同入口：[Cursor 插件](../../.cursor-plugin/README.md) 的清单引用 `phoenix-cli`、`phoenix-evals`、`phoenix-tracing` 三个技能；[Claude Code 插件](../../plugins/claude/arize-phoenix/README.md) 和 [Codex 插件](../../plugins/codex/arize-phoenix) 的实现保存在 `plugins/`。移动技能前需同步核对各插件的引用。工程目录导航见 [项目文档总索引](../../docs/00-总索引.md)。

<a id="internal-skills"></a>

## 内部技能

本目录中的其他技能供 Phoenix 自身的开发人员使用，并在其 `SKILL.md` 的 frontmatter 中包含以下标记：

```yaml
metadata:
  internal: true
```
