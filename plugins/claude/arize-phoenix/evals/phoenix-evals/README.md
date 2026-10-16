<a id="phoenix-evals-plugin-evals"></a>

# phoenix-evals 插件评测

`phoenix-evals` 技能的行为测试，通过 `claude plugin eval` 运行。测试检查：用户需要构建、运行或验证评估器时技能是否触发；请求属于其他 Phoenix 技能时是否保持静默；生成的评估器或方案是否遵循技能原则（使用 `phoenix.evals` / `@arizeai/phoenix-evals`，确定性检查优先使用代码，使用离散标签而非李克特量表，对照标注数据验证裁判，并给出可运行的实验和 CI 指导）。

这些用例放在独立分组目录中，便于与同级平铺目录中的 `phoenix-cli` 用例分别选择。每个输入都会在启用和未启用插件时各运行一次，因此主要指标是 Δ（启用插件减去未启用插件的得分），而非原始通过率。

<a id="baseline"></a>

## 基线

2026 年 10 月在 CI 中测得（每用例运行 3 次，`--ablation with-without`，智能体 `claude-opus-4-8`，`--judge-model claude-sonnet-5`）：应触发技能的用例（排除 `-neg-`）平均 Δ 为 **+0.44**。完整运行费用为 18.93 美元，耗时 27 分钟。

| 用例 | 启用插件 | 未启用插件 | Δ |
| --- | --- | --- | --- |
| `01-rag-groundedness-judge` | 0.97 | 0.50 | +0.47 |
| `02-json-schema-code-eval` | 1.00 | 1.00 | 0.00 |
| `03-run-evaluator-experiment` | 0.89 | 0.44 | +0.44 |
| `04-validate-judge-labels` | 0.94 | 0.56 | +0.39 |
| `05-faithfulness-ci-gate` | 0.93 | 0.44 | +0.48 |
| `06-ts-relevance-judge` | 1.00 | 0.29 | +0.71 |
| `09-fix-legacy-llm-classify` | 1.00 | 0.83 | +0.17 |
| `10-fix-hallucination-threshold` | 1.00 | 0.13 | +0.87 |
| `07-neg-elixir-exunit` | 1.00 | 1.00 | 0.00 |
| `08-neg-generic-metric-q` | 1.00 | 1.00 | 0.00 |
| `11-neg-export-traces-dataframe` | 0.67 | 1.00 | −0.33 |

`02` 仅用于防止回归（两个对照组都通过）。`11` 得分为 0.67 仅因为其答案正则只接受 `get_spans_dataframe`；目前也接受 `query_spans`，而且两个对照组都从未触发技能。`.github/workflows/plugin-evals.yml` 中的 CI 门禁为 `min_delta: 0.30`、`gate: block`；由于这只是一次测量，预留空间比 phoenix-cli 的 0.10 更宽。用例或技能发生实质变化后，应重新测量。

<a id="cases"></a>

## 用例

| 用例 | 是否触发 | 语言 | 检查内容 |
| --- | --- | --- | --- |
| `01-rag-groundedness-judge` | 是 | Python | 构建使用离散标签的 `ClassificationEvaluator` LLM 裁判，并建议验证 |
| `02-json-schema-code-eval` | 是 | Python | 通过 `@create_evaluator` 创建代码评估器：封闭模式（额外键失败）、拒绝布尔 `age`，并绑定 `output` |
| `03-run-evaluator-experiment` | 是 | Python | 使用 `create_dataset` 上传示例，绑定 `output`/`expected`，使用带 `repetitions` 和 `experiment_name` 的 `run_experiment` |
| `04-validate-judge-labels` | 是 | Python | 按门槛检查 TPR/TNR，以人工之间的一致性为上限，检查类别平衡、80 < 100 的示例数，以及假阳性/假阴性 |
| `05-faithfulness-ci-gate` | 是 | Python | pytest 插件（`phoenix.client.pytest`，稳定 `ids`）：模型选择对不变量作断言，并逐例记录忠实性 |
| `06-ts-relevance-judge` | 是 | TypeScript | 使用 `@arizeai/phoenix-evals` 中的 `createClassificationEvaluator`，采用离散选项 |
| `07-neg-elixir-exunit` | 否 | — | 名称冲突：Elixir Phoenix + ExUnit 的“评估”问题，不应触发评估技能 |
| `08-neg-generic-metric-q` | 否 | — | 对 500 条翻译计算语料库 BLEU：批量指标问题，但仍不需要 Phoenix 评估器 |
| `09-fix-legacy-llm-classify` | 是 | Python | 将粘贴的旧版 `llm_classify`/`OpenAIModel` 代码迁移到 2.0 `ClassificationEvaluator` + `evaluate_dataframe` API |
| `10-fix-hallucination-threshold` | 是 | Python | 修复粘贴的 2.0 检查：`metrics` 导入、在 `.mean()` 前读取 `_score` 字典、`HallucinationEvaluator` 忽略 `context`，以及阈值方向颠倒 |
| `11-neg-export-traces-dataframe` | 否 | — | 仅拉取跨度到数据帧查看：`get_spans_dataframe`，不使用评估器，不应触发评估技能 |

<a id="run"></a>

## 运行

在插件目录（`plugins/claude/arize-phoenix`）中运行：

```bash
claude plugin eval . \
  --tag phoenix-evals \
  --ablation with-without \
  --judge-model claude-sonnet-5 \
  --allow-tools Write "Read(//$(pwd)/**)" "Read(//$(git rev-parse --show-toplevel)/.agents/skills/**)"
```

使用 `--case 06-ts-relevance-judge --runs 1` 迭代单个用例。应触发技能的用例会写文件（`--allow-tools Write`），评分器再通过 `target: {source: file, path: ...}` 读取；没有用例会运行文件或访问真实 Phoenix，因此不需要模拟服务。

<a id="grader-conventions"></a>

## 评分器约定

先运行确定性评分器（对写入文件和最终消息执行 `regex`；不使用 `file_exists`，因为提示词已指定文件名，它在两个对照组中都会通过），然后为**每条判断条件**配置一个 `llm` 评分器，权重为 `weight: 0.5`。运行器裁判无法正确处理组合规则，因此各条件独立评分。`skill-fired` 在消融对比中报告，但不计分。负例使用 `skill-not-used`（`tool: Skill`、`input_match: phoenix-evals`、`min: 0`、`max: 0`、`arm: both`）；精确匹配 `phoenix-evals`，因为该套件要求的是 `phoenix-evals` 技能保持静默，而非任何 Phoenix 技能都不触发。

<a id="record-to-phoenix"></a>

## 记录到 Phoenix

一个小型后处理脚本会将运行 JSON 回放到 Phoenix，记录为实验（每套测试一个数据集，每个用例一个示例，各评分器的 pass/fail 在对应用例上可见）。将其指向正在运行的 Phoenix：

```bash
cd plugins/claude/arize-phoenix
claude plugin eval . --tag phoenix-evals --ablation with-without \
  --judge-model claude-sonnet-5 --trust-plugin --no-publish \
  --json /tmp/pe.json \
  --allow-tools Write "Read(//$(pwd)/**)" "Read(//$(git rev-parse --show-toplevel)/.agents/skills/**)"
# run with the project's Python (needs arize-phoenix-client): uv run, or the venv directly
uv run python evals/record_to_phoenix.py /tmp/pe.json   # or: ../../../.venv/bin/python …
```

`--endpoint` 默认先读取 `$PHOENIX_ENDPOINT`，再读取 `$PHOENIX_COLLECTOR_ENDPOINT`，否则使用 `http://localhost:6006`。

再次运行会更新或插入数据集（稳定示例 ID 为用例名称），并新增实验，因此可以持续积累运行结果用于比较。该脚本通用，可传入 `--dataset-name` 记录其他测试套件。目前尚未接入 CI 自动记录（需要持久化 Phoenix 和密钥，类似 `pxi-evals.yml`）。
