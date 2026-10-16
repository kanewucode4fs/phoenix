<a id="phoenix-evals-reference"></a>

# Phoenix Evals 参考文档

欢迎阅读 Phoenix Evals 参考文档。此包提供面向 LLM 应用的评估工具，包括相关性判断、毒性判断、幻觉检测等。

<a id="features"></a>

## 功能

Phoenix Evals 提供**轻量、可组合的构建模块**，用于编写和运行评估：

- 通过适配器**兼容你偏好的模型 SDK**（OpenAI、LiteLLM、LangChain）
- **强大的输入映射与绑定**，支持复杂数据结构
- 为幻觉检测等常见评估任务提供**多种预置指标**
- **评估器原生插桩**，通过 OpenTelemetry 追踪实现可观测性和数据集整理
- **极高性能**：通过内置并发和批处理实现最高 20 倍加速
- **丰富的便捷功能**，改善开发体验！

<a id="installation"></a>

## 安装

通过 pip 安装 Phoenix Evals 包：

```bash
pip install 'arize-phoenix-evals>=2.0.0' openai
```

<a id="quick-start"></a>

## 快速开始

```python
from phoenix.evals import create_classifier
from phoenix.evals.llm import LLM

# Create an LLM instance
llm = LLM(provider="openai", model="gpt-4o")

# Create an evaluator
evaluator = create_classifier(
    name="helpfulness",
    prompt_template="Rate the response to the user query as helpful or not:\n\nQuery: {input}\nResponse: {output}",
    llm=llm,
    choices={"helpful": 1.0, "not_helpful": 0.0},
)

# Simple evaluation
scores = evaluator.evaluate({"input": "How do I reset?", "output": "Go to settings > reset."})
scores[0].pretty_print()

# With input mapping for nested data
scores = evaluator.evaluate(
    {"data": {"query": "How do I reset?", "response": "Go to settings > reset."}},
    input_mapping={"input": "data.query", "output": "data.response"},
)
scores[0].pretty_print()
```

<a id="core-functions"></a>

## 核心函数

此包的主要评估函数：

- **`create_classifier`**: 创建基于 LLM 的分类评估器
- **`create_evaluator`**: 从函数创建自定义评估器
- **`bind_evaluator`**: 通过输入映射绑定评估器
- **`evaluate_dataframe`**: 使用多个评估器评估 DataFrame

<a id="usage-examples"></a>

## 使用示例

```python
import pandas as pd
from phoenix.evals import create_classifier, evaluate_dataframe
from phoenix.evals.llm import LLM

# Create an LLM instance
llm = LLM(provider="openai", model="gpt-4o")

# Create evaluators
relevance_evaluator = create_classifier(
    name="relevance",
    prompt_template="Is the response relevant to the query?\n\nQuery: {input}\nResponse: {output}",
    llm=llm,
    choices={"relevant": 1.0, "irrelevant": 0.0},
)

helpfulness_evaluator = create_classifier(
    name="helpfulness",
    prompt_template="Is the response helpful?\n\nQuery: {input}\nResponse: {output}",
    llm=llm,
    choices={"helpful": 1.0, "not_helpful": 0.0},
)

# Prepare your dataframe
df = pd.DataFrame(
    [
        {
            "input": "How do I reset my password?",
            "output": "Go to settings > account > reset password.",
        },
        {"input": "What's the weather like?", "output": "I can help you with password resets."},
    ]
)

# Evaluate the dataframe
results_df = evaluate_dataframe(
    dataframe=df,
    evaluators=[relevance_evaluator, helpfulness_evaluator],
)

print(results_df.head())
```

<a id="external-links"></a>

## 外部链接

- [Phoenix 主文档](https://arize.com/docs/phoenix)
- [Python 参考文档](https://arize-phoenix.readthedocs.io/)
- [GitHub 仓库](https://github.com/Arize-ai/phoenix)

<a id="api-reference"></a>

## API 参考

```{toctree}
:maxdepth: 2
:caption: API Reference

api/evals
```

<a id="indices-and-tables"></a>

## 索引与表格

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
