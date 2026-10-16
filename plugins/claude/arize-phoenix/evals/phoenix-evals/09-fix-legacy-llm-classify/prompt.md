---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Write]
runs: 3
tags: [phoenix-evals]
---
我将 `arize-phoenix-evals` 升级到最新版后，这段相关性评估脚本就无法运行了，现在导入会失败。能帮我修好吗？我会对导出的数据帧 `df` 运行它，其中包含 `input` 和 `output` 列，并希望最终像以前一样输出各标签的计数。

```python
from phoenix.evals import OpenAIModel, llm_classify
from phoenix.evals.default_templates import RAG_RELEVANCY_PROMPT_TEMPLATE

model = OpenAIModel(model="gpt-4")

results = llm_classify(
    dataframe=df,
    template=RAG_RELEVANCY_PROMPT_TEMPLATE,
    model=model,
    rails=["relevant", "irrelevant"],
    provide_explanation=True,
)

print(results["label"].value_counts())
```

将修复后的版本保存为 `relevance_eval.py`。
