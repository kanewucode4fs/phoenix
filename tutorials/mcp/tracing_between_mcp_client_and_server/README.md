# 为 MCP 客户端与服务端应用实现端到端追踪

本教程介绍如何在 MCP 客户端与服务端之间传播 OpenTelemetry（OTEL）上下文，实现完整的可观测性。`openinference-instrumentation-mcp` 包为客户端和服务端组件提供埋点支持。

## 什么是 MCP，为什么需要分布式追踪？

Anthropic 的模型上下文协议（MCP）架构的一项主要优势，是将 AI 模型与不同服务、机器和编程语言中的信息连接起来。这种分布式方式有以下优点：

1. **扩展 AI 能力**：让模型连接训练数据之外的专业知识与数据源。
2. **即插即用的组件**：无需重新训练模型，即可添加新的上下文提供方。
3. **多语言支持**：使用不同编程语言实现上下文提供方，同时保持兼容。

当请求经过多个服务时，调试会变得困难。如何跟踪请求的完整路径，定位问题发生的位置？

### 使用 OpenTelemetry 追踪 MCP 调用

OpenTelemetry 通过以下机制解决跨服务追踪问题：

- **跨服务保留上下文**：维持追踪 ID 与不同组件之间的关系。
- **跨网络边界传播**：自动处理网络请求中的上下文。
- **支持多种语言**：使用与不同编程语言兼容的标准格式。

正确接入埋点后，客户端调用服务端时：
1. 客户端创建 Span，记录该操作。
2. OTEL 上下文随 MCP 请求自动传播。
3. 服务端延续同一条追踪。
4. 所有上下文提供方继承该追踪上下文。
5. 在 Phoenix 中可以将整个交互查看为一条连通的追踪。

这些信息有助于排查复杂 AI 系统的问题、优化性能瓶颈，并理解不同组件如何影响应用行为。


## 环境准备

正确接入埋点后，追踪上下文会自动跨越 MCP 客户端与服务端边界，从而：

- 在同一条追踪中跟踪从客户端到服务端的请求。
- 观察请求生命周期各阶段的时延。
- 调试跨服务边界的问题。

### 配置环境

1. 将此目录作为独立项目打开，避免与 Phoenix 仓库其他目录混用，以防遮蔽 OpenAI 使用的 `agents` 包。

2. 安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 运行示例

1. 在本地运行 Phoenix，或连接[在线实例](https://app.phoenix.arize.com)。

2. 在 `.env` 中配置 `OPENAI_API_KEY` 和 `PHOENIX_COLLECTOR_ENDPOINT`。如果使用在线实例或启用了认证，还需设置 `PHOENIX_API_KEY`。

3. 运行 MCP 客户端。客户端会在运行时通过独立进程启动服务端。
   ```bash
   python client.py
   ```

4. 向 Agent 提问。

5. 在 Phoenix 中查看追踪：
![MCP 追踪](https://storage.googleapis.com/arize-phoenix-assets/assets/images/mcp-instrumentation.png)

### 工作原理

`openinference-instrumentation-mcp` 包会自动：

1. 为 MCP 客户端操作创建 Span。
2. 向 MCP 请求注入追踪上下文。
3. 在服务端提取并延续追踪上下文。
4. 将上下文关联到服务端创建的 OTEL Span。

这样，即使请求跨越服务边界，也能通过一条追踪查看完整流程。
