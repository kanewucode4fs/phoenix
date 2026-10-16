<a id="agentic-rag-examples"></a>

# Agentic RAG 示例

<a id="overview"></a>

## 概述

本目录包含使用 LangChain 库构建检索增强生成（RAG）Agent 的示例。

<a id="features"></a>

## 功能

* 使用 LangChain 构建 RAG Agent 工作流
* 集成 OpenAI 模型进行语言生成和检索
* 展示网页搜索、响应分析及创建 RAG 响应等工具的用法
* 使用 OpenInference 装饰器自动插桩，完整覆盖 Agent
* 使用 Phoenix 进行端到端追踪，跟踪 Agent 性能

<a id="requirements"></a>

## 环境要求

* LangChain 库
* OpenAI API 密钥
* Langgraph
* Python 3.x
* Gradio（用于 UI）

<a id="installation"></a>

## 安装

1. 运行 `pip install -r requirements.txt` 安装所需库
2. 运行 app.py 并输入所需密钥（OpenAI、Phoenix API 密钥）

<a id="usage"></a>

## 使用方法

1. 运行 `app.py` 脚本以启动 RAG Agent
2. 提供输入并接收响应，与 Agent 交互

<a id="files"></a>

## 文件

* `app.py`：启动应用的主脚本，使用默认端口（7860）运行 Web 服务器
* `agent.py`：RAG Agent 的主脚本
* `tools.py`：包含网页搜索、响应分析及创建 RAG 响应的工具
* `rag.py`：包含初始化和使用 RAG 向量存储的函数
* `requirements.txt`：列出项目所需的库

<a id="notes"></a>

## 注意事项

* 所有密钥都必须通过 UI 应用输入。
* UI 中会使用默认 URL 加载 RAG。你可以更新 URL，使用自己的数据源初始化项目。
* 此应用支持基于 HTML 的数据源。
