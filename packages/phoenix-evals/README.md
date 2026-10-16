# arize-phoenix-evals

<p align="center">
    <a href="https://pypi.org/project/arize-phoenix-evals/">
        <img src="https://img.shields.io/pypi/v/arize-phoenix-evals" alt="PyPI 版本">
    </a>
    <a href="https://arize-phoenix.readthedocs.io/projects/evals/">
        <img src="https://img.shields.io/badge/docs-blue?logo=readthedocs&logoColor=white" alt="文档">
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=packages/phoenix-evals/README.md" />
</p>

Phoenix Evals 提供**轻量、可组合的构建模块**，用于编写和运行 LLM 应用评估，包括相关性判断、毒性判断、幻觉检测等工具。

<a id="features"></a>

## 功能

- 通过适配器**兼容你偏好的模型 SDK**（OpenAI、LiteLLM、LangChain）
- **强大的输入映射与绑定**，支持复杂数据结构
- 为幻觉检测等常见评估任务提供**多种预置指标**
- **评估器原生插桩**，通过 OpenTelemetry 追踪实现可观测性和数据集整理
- **极高性能**：通过内置并发和批处理实现最高 20 倍加速
- **丰富的便捷功能**，改善开发体验！

<a id="installation"></a>

## 安装

通过 pip 安装 Phoenix Evals 2.0：

```shell
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

<a id="pre-built-evaluators"></a>

## 预置评估器

`phoenix.evals.metrics` 模块为常见任务提供开箱即用的评估器：

| 评估器 | 类 | 说明 |
| --------- | ----- | ----------- |
| 忠实度 | `FaithfulnessEvaluator` | 检测幻觉，检查输出是否基于上下文 |
| 完整性 | `CompletenessEvaluator` | 检查对话中每个有效用户请求是否确实完成 |
| 简洁性 | `ConcisenessEvaluator` | 评估响应是否适度简洁 |
| 正确性 | `CorrectnessEvaluator` | 检查输出是否符合事实 |
| 检索相关性 | `RetrievalRelevanceEvaluator` | 衡量检索信息与请求的相关程度 |
| 拒绝回答 | `RefusalEvaluator` | 检测模型是否拒绝回答 |
| 工具调用 | `ToolInvocationEvaluator` | 检查是否使用正确参数调用正确工具 |
| 工具选择 | `ToolSelectionEvaluator` | 评估是否为任务选择正确工具 |
| 工具响应处理 | `ToolResponseHandlingEvaluator` | 评估模型利用工具响应的效果 |
| 用户不满 | `UserFrictionEvaluator` | 检测表达出的纠正、重试、不满和质疑 |
| 个人身份信息检测 | `PiiDetectionEvaluator` | 筛查对话记录中的个人身份信息 |
| 精确匹配 | `exact_match` | 检查输出与预期的字符串是否完全相等 |
| 正则匹配 | `MatchesRegex` | 检查输出是否匹配正则表达式 |
| 精确率/召回率 | `PrecisionRecallFScore` | 计算分类任务的精确率、召回率和 F 分数 |

```python
from phoenix.evals.llm import LLM
from phoenix.evals.metrics import FaithfulnessEvaluator, exact_match, MatchesRegex

llm = LLM(provider="openai", model="gpt-4o")

# LLM-powered faithfulness evaluator
faithfulness = FaithfulnessEvaluator(llm=llm)
scores = faithfulness.evaluate(
    {
        "input": "What is the capital of France?",
        "context": "Paris is the capital of France.",
        "output": "The capital of France is Berlin.",
    }
)
scores[0].pretty_print()
# Score(name='faithfulness', score=0.0, label='unfaithful', explanation='...')

# Code-based exact match
match_result = exact_match({"output": "Paris", "expected": "Paris"})

# Regex match
regex_result = MatchesRegex(pattern=r"^\d{4}-\d{2}-\d{2}$").evaluate({"output": "2024-03-15"})
```

<a id="llm-providers"></a>

## LLM 提供商

`LLM` 类支持多种 AI 提供商：

```python
from phoenix.evals.llm import LLM

# OpenAI
llm = LLM(provider="openai", model="gpt-4o")

# Anthropic
llm = LLM(provider="anthropic", model="claude-3-5-sonnet-20241022")

# Google Gemini
llm = LLM(provider="google", model="gemini-1.5-pro")

# LiteLLM (unified interface for 100+ providers)
llm = LLM(provider="litellm", model="gpt-4o")
```

<a id="evaluating-dataframes"></a>

## 评估 DataFrame

```python
import pandas as pd
from phoenix.evals import create_classifier, evaluate_dataframe, async_evaluate_dataframe
from phoenix.evals.llm import LLM

# Create an LLM instance
llm = LLM(provider="openai", model="gpt-4o")

# Create multiple evaluators
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

# Synchronous evaluation
results_df = evaluate_dataframe(
    dataframe=df,
    evaluators=[relevance_evaluator, helpfulness_evaluator],
)
print(results_df.head())

# Async evaluation (up to 20x faster with large dataframes)
import asyncio

results_df = asyncio.run(
    async_evaluate_dataframe(
        dataframe=df,
        evaluators=[relevance_evaluator, helpfulness_evaluator],
    )
)
```

<a id="documentation"></a>

## 文档

- **[完整文档](https://arize-phoenix.readthedocs.io/projects/evals/)** - 完整 API 参考和指南
- **[Phoenix 文档](https://arize.com/docs/phoenix)** - 详细用例和示例
- **[OpenInference](https://github.com/Arize-ai/openinference)** - 面向框架的自动插桩库

<a id="community"></a>

## 社区

加入我们的社区，与数千名 AI 开发者交流：

- 🌍 加入我们的 [Slack 社区](https://join.slack.com/t/arize-ai/shared_invite/zt-3r07iavnk-ammtATWSlF0pSrd1DsMW7g).
- 📚 阅读 [Phoenix 文档](https://arize.com/docs/phoenix).
- 💡 在 _#phoenix-support_ 频道提问并反馈。
- 🌟 为我们的 [GitHub](https://github.com/Arize-ai/phoenix) 加星。
- 🐞 通过 [GitHub Issues](https://github.com/Arize-ai/phoenix/issues) 报告问题。
- 𝕏 在 [𝕏](https://twitter.com/ArizePhoenix) 关注我们。
- 💼 在 [LinkedIn](https://www.linkedin.com/showcase/113218220) 关注我们。
- 🗺️ 查看我们的[路线图](https://github.com/orgs/Arize-ai/projects/45)，了解未来方向。
