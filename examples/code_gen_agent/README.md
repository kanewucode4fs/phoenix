<a id="code-generation-agent-example"></a>

# 代码生成 Agent 示例

<a id="overview"></a>

## 概述

本目录包含使用 LangChain 库构建代码生成（Code-Gen）Agent 的示例。
该 Agent 使用 OpenAI 模型生成、改进并验证代码。

<a id="features"></a>

## 功能

* 使用 LangChain 构建 Code-Gen Agent 工作流
* 集成 OpenAI 模型以生成和改进代码
* 展示代码分析、执行和生成等工具的用法
* 使用 OpenInference 装饰器自动插桩，完整覆盖 Agent
* 使用 Phoenix 进行端到端追踪，跟踪 Agent 性能

<a id="requirements"></a>

## 环境要求

* LangChain 库
* OpenAI API 密钥
* Langgraph（用于管理 Agent 逻辑和工作流）
* Python 3.x
* Gradio（用于 UI）

<a id="installation"></a>

## 安装

如果从 `phoenix` 仓库内部运行此代码，建议使用 `uv` 运行，以避免依赖问题。

1. 安装 `uv`
2. 运行 `uv run --isolated --with-requirements requirements.txt python app.py`

<a id="usage"></a>

## 使用方法

1. 运行 `app.py` 脚本以启动 RAG Agent。
2. 点击输出中提供的本地主机链接。
3. 输入提示词并接收生成的代码响应，与 Agent 交互。

<a id="files"></a>

## 文件

* `app.py`：启动应用的主脚本，使用默认端口（7860）运行 Web 服务器
* `agent.py`：代码生成 Agent 的主脚本
* `tools.py`：包含代码分析、生成、执行和合并工具
* `requirements.txt`：列出项目所需的库

<a id="notes"></a>

## 注意事项

* 所有密钥都必须通过 UI 应用输入。
* 此应用支持基于 HTML 的数据源。
