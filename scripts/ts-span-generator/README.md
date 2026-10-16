<a id="ts-span-generator"></a>

# TypeScript 跨度生成器（ts-span-generator）

生成确定性且具有真实感的智能体追踪数据，通过 OTLP 发送到 Phoenix 实例。无需模型凭证或运行真实智能体，即可利用包含大量消息的 LLM 跨度开发和测试界面功能。

生成的数据是一段“事故处理助手”的 SRE 对话：

- **追踪 1**：完整的事故调查，包含 10 个 LLM 跨度，输入消息历史从 2 条增长到 20 条；包含 6 次工具调用（`search_logs`、`get_metrics`、`get_config_diff`、`create_incident_action`），带 JSON 参数和结果；最后一条输出消息是一篇较长的 Markdown 事后复盘总结。
- **追踪 2**：简短的 3 条消息交互，用于对比。

两条追踪共享同一会话（`incident-2026-08-06-checkout`）和同一个 `user.id`。对话文本有意包含近似词汇（`timeout` / `timed out` / `time-out`、`authentication` / `auth-service` / `401 Unauthorized`、`database` / 拼写错误 `databse`、`connection pool` / `conn pool`、`rollback` / `rolled back`），便于测试搜索和文本匹配功能。

内容固定；时间戳相对于当前时间生成，因此数据始终能出现在最近时间范围的筛选结果中。

<a id="usage"></a>

## 用法

前置条件：Node.js >= 22.12，以及运行中的 Phoenix（默认 `http://localhost:6006`）。

```bash
npm install
npm start
# or against a non-default endpoint:
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006 npm start
```

如果 Phoenix 启用了认证，还需设置 `PHOENIX_API_KEY`。

数据默认写入 **`incident-copilot`** 项目（可通过 `PHOENIX_PROJECT_NAME` 覆盖）：每次运行生成 19 个跨度（2 个 AGENT、11 个 LLM、6 个 TOOL）。

<a id="verifying"></a>

## 验证

```bash
curl -s "http://localhost:6006/v1/projects/incident-copilot/spans?limit=50" \
  | node -e "let b='';process.stdin.on('data',c=>b+=c).on('end',()=>console.log(JSON.parse(b).data.length,'spans'))"
```
