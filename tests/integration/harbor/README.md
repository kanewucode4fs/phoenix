<a id="harbor-plugin-integration-tests"></a>

# Harbor 插件集成测试

这些测试会针对 Phoenix 运行真实的 Harbor 作业。测试需要 Docker，会下载 Terminal-Bench
任务并调用付费模型 API，因此需要手动运行，不属于常规测试套件或 CI。

使用 `make dev-backend` 启动 Phoenix，或使用现有服务。在另一个终端中切换到仓库根目录，
确保命令能够读取 `OPENAI_API_KEY`，然后运行上下文压缩用例：

```bash
HARBOR_E2E_ENDPOINT=http://localhost:6006 \
HARBOR_E2E_ATIF_CASES=compaction \
HARBOR_E2E_KEEP=1 \
make harbor-plugin-e2e
```

通过 `HARBOR_E2E_ATIF_CASES` 指定本次改动需要的用例，多个名称以逗号分隔。
省略时会运行 `terminus,compaction,multi-step`。

| 用例 | 智能体 | 检查内容 |
| --- | --- | --- |
| `terminus` | 使用 `HARBOR_ATIF_MODEL` 的 Terminus-2 | 同一实验中的三个 Terminal-Bench 试验、运行关联、实测 LLM 耗时、相同时间的排序，以及幂等恢复 |
| `compaction` | 强制启用摘要的 Terminus-2 | 压缩跨度、后续执行轨迹、三个摘要子智能体的轨迹，以及幂等恢复 |
| `multi-step` | 使用 `HARBOR_ATIF_CLAUDE_MODEL` 的 Claude Code | 合成的三步 `fixtures/tasks/word-count` 任务、步骤跨度、步骤奖励，以及幂等恢复 |

`terminus` 和 `compaction` 默认使用 `openai/gpt-5-mini`，需要 `OPENAI_API_KEY`。
`multi-step` 默认使用 `anthropic/claude-sonnet-4-5`，需要 `ANTHROPIC_API_KEY`。
多步骤用例会将该密钥传给 Claude Code，并按 API 用量计费，不使用订阅计费。
可通过 `HARBOR_ATIF_MODEL` 和 `HARBOR_ATIF_CLAUDE_MODEL` 覆盖模型设置。

运行器会构建当前 Phoenix 客户端的 wheel 包。Harbor 默认使用最低支持版本 `0.21.0`；
可通过 `HARBOR_VERSION` 测试其他版本。

设置 `HARBOR_E2E_ENDPOINT` 可将结果保存在现有 Phoenix 实例中。未设置时，运行器会
使用独立数据库启动临时服务。运行成功后会删除临时工作区，除非设置了 `HARBOR_E2E_KEEP=1`。
运行失败时会保留工作区并打印路径。外部 Phoenix 服务的数据不会被删除。
