<a id="typescript-experiments-quickstart"></a>

# TypeScript 实验快速开始

本教程展示如何使用 TypeScript 在 Phoenix 中运行实验，包括创建数据集、定义任务函数、使用代码评估器和 LLM 裁判评估器，以及比较 AI Agent 的不同版本。

<a id="overview"></a>

## 概述

本教程实现一个客服 Agent，功能包括：

- 将支持工单分类（账单、技术、账户、其他）
- 根据分类检索相关政策
- 为用户生成有帮助的回复

本教程运行三个实验：

1. **工具调用准确率**：使用代码评估器评估分类工具
2. **初始客服 Agent**：使用 LLM 裁判评估器评估完整 Agent
3. **改进客服 Agent**：比较采用增强指令的改进版 Agent，并用 LLM 裁判评估器进行评估

<a id="prerequisites"></a>

## 前置条件

- Phoenix Cloud 账户
- OpenAI API 密钥

<a id="setup"></a>

## 配置

<a id="1-install-all-dependencies"></a>

### 1. 安装全部依赖

在当前目录运行：

```bash
npm install
```

<a id="2-configure-environment-variables"></a>

### 2. 配置环境变量

在当前目录创建 `.env` 文件：

```env
PHOENIX_ENDPOINT=https://app.phoenix.arize.com/s/your-space
PHOENIX_API_KEY=your-phoenix-api-key
OPENAI_API_KEY=your-openai-api-key
```

<a id="3-run-the-tutorial"></a>

### 3. 运行教程

```bash
npm start
```

随后即可在 Phoenix 中查看实验结果和追踪！

<a id="documentation"></a>

## 文档

实验的详细文档见：

- [定义数据集](https://docs.phoenix.arize.com/docs/phoenix/datasets-and-experiments/tutorial/defining-the-dataset)
- [使用代码评估运行实验](https://docs.phoenix.arize.com/docs/phoenix/datasets-and-experiments/tutorial/run-experiments-with-code-evals)
- [使用 LLM 裁判运行实验](https://docs.phoenix.arize.com/docs/phoenix/datasets-and-experiments/tutorial/run-experiments-with-llm-judge)
- [通过实验迭代](https://docs.phoenix.arize.com/docs/phoenix/datasets-and-experiments/tutorial/iteration-workflow-experiments)
