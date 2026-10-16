<a id="mastra-agent-with-arize-phoenix-tracing"></a>

# 集成 Arize Phoenix 追踪的 Mastra Agent

使用 Mastra 构建并由 Arize Phoenix 追踪的电影推荐 Agent。

<a id="setup"></a>

## 配置

<a id="1-setup-phoenix"></a>

### 1. 配置 Phoenix

Phoenix 入门指南： https://arize.com/docs/phoenix/get-started

若在本地运行，Phoenix 将在 `http://localhost:6006` 提供服务。

<a id="2-install-dependencies"></a>

### 2. 安装依赖

```bash
npm install
```

这会安装所有必需依赖，包括：

- `@ai-sdk/openai` - 供 AI SDK 使用的 OpenAI SDK
- `@mastra/core` - Mastra 核心框架
- `@mastra/arize` - Arize Phoenix 追踪集成
- `zod` - 模式验证
- `dotenv` - 环境变量管理
- `@arizeai/phoenix-evals` - Arize Phoenix Evals TS 库
- `@arizeai/phoenix-client/spans` - Arize Phoenix 客户端库

<a id="3-configure-environment"></a>

### 3. 配置环境

在根目录创建 `.env` 文件：

```bash
# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Phoenix Configuration — same Phoenix, one variable per concern
PHOENIX_ENDPOINT=http://localhost:6006
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=mastra-project
```

评估脚本通过服务器基础 URL `PHOENIX_ENDPOINT` 调用 Phoenix API。`PHOENIX_COLLECTOR_ENDPOINT` 是发送追踪的确切 URL；Mastra 的 `ArizeExporter` 会按原样向其发送 POST，因此该 URL 包含 OTLP `/v1/traces` 路径，并由 `src/mastra/index.ts` 直接传递。

若实例启用了身份验证，还需设置 `PHOENIX_API_KEY=your-api-key`，并将两个变量都指向该实例：`PHOENIX_ENDPOINT=https://phoenix.example.com` 和 `PHOENIX_COLLECTOR_ENDPOINT=https://phoenix.example.com/v1/traces`。

<a id="running-the-agent"></a>

## 运行 Agent

启动 Mastra 开发服务器：

```bash
npm run dev
```

进入 Mastra Playground，与电影推荐 Agent 交互。

<a id="viewing-traces"></a>

## 查看追踪

运行 Agent 后打开 Phoenix，即可看到所有 Agent 运行、工具调用和模型交互的追踪及可视化。

<a id="running-evals"></a>

## 运行评估

准备好运行评估后，在示例目录运行：

```bash
npm run eval
```

<a id="project-structure"></a>

## 项目结构

```
src/
  mastra/
    agents/
      movie-agent.ts           # Movie recommendation agent
    tools/
      movie-selector-tool.ts   # Finds movies by genre
      reviewer-tool.ts         # Reviews and rates movies
      preview-summarizer-tool.ts # Summarizes movies
    index.ts                   # Mastra configuration with Arize Phoenix tracing
  eval/
    evals.ts                   # Tool Correctness & Goal Completion evals
```

<a id="whats-included"></a>

## 包含的内容

- **电影推荐 Agent**：使用三个工具推荐电影的 Agent：
  - MovieSelector：按类型查找电影
  - Reviewer：评论电影并按评分排序
  - PreviewSummarizer：提供电影摘要
- **Arize Phoenix 追踪**：所有 Agent 交互都会被自动追踪并发送到 Phoenix
- **Arize Phoenix Evals**：使用 Phoenix Evals TS 运行工具正确性和 Agent 目标完成度评估
