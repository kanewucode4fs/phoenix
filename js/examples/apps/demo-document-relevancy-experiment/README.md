<a id="typescript-experiments-and-evals-with-arize-phoenix"></a>

# 使用 Arize Phoenix 进行 TypeScript 实验与评估

此演示应用展示如何通过 Arize Phoenix 在 TypeScript 中运行实验和评估，使用 Arize Phoenix 管理数据集、运行实验并评估 LLM 输出。

<a id="overview"></a>

## 概述

演示包含两个主要文件：

- `app.ts`: 包含一个太空知识应用，使用 OpenAI 从知识库检索相关上下文
- `experiment.ts`: 配置并运行实验，评估所检索上下文的相关性

<a id="required-packages"></a>

## 所需软件包

运行此演示需要安装以下包：

```bash
npm install dotenv openai @arizeai/openinference-instrumentation-openai @ai-sdk/openai @arizeai/phoenix-client @arizeai/phoenix-evals
```

<a id="setup"></a>

## 配置

1. 安装所需包（见上文）

2. 在根目录创建 `.env` 文件并填入 API 密钥：

```env
OPENAI_API_KEY=your-openai-api-key
PHOENIX_ENDPOINT=http://localhost:6006
# Only needed if auth is enabled on your Phoenix instance
PHOENIX_API_KEY=your-phoenix-api-key
```

<a id="running-the-demo"></a>

## 运行演示

运行实验：

```bash
npx tsx experiment.ts
```

<a id="how-it-works"></a>

## 工作原理

1. **app.ts**: 实现太空知识检索应用，功能包括：
   - 使用 OpenAI 的 GPT-4o-mini 模型从知识库检索相关上下文
   - 根据查询返回最相关的 1～3 条信息

2. **experiment.ts**:
   - 创建包含太空相关问题的数据集
   - 为数据集中的每个问题运行 `spaceKnowledgeApplication` 函数
   - 通过 Phoenix Evals 的检索相关性评估器评估检索到的上下文
   - 将实验结果发送到 Phoenix 进行分析

实验结果会展示在 Phoenix 中，可在其中分析应用性能并查看评估指标。
