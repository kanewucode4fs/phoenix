<a id="llama-researcher"></a>

# Llama 研究助手

本教程将使用 LlamaIndex 工作流创建 LLama-Researcher，灵感来自 [GPT-Researcher](https://github.com/assafelovic/gpt-researcher)。

原始实现由 [rsrohan99](https://github.com/rsrohan99) 提供。

使用的技术栈：

- 使用 LlamaIndex 工作流进行编排
- 使用 Tavily API 作为搜索引擎 API
- 使用 Arize Phoenix 进行追踪和评估

<a id="how-to-use"></a>

## 使用方法

- 克隆仓库

```bash
git clone https://github.com/Arize-ai/phoenix
cd examples/llamaindex-workflows-research-agent
```

- 安装依赖

```bash
pip install -r requirements.txt
```

- 创建 `.env` 文件并添加 `OPENAI_API_KEY`、`TAVILY_API_KEY` 和 `PHOENIX_API_KEY`

```bash
cp .env.example .env
```

- 指定研究主题并运行工作流

```bash
 python run.py "topic to research"
```
