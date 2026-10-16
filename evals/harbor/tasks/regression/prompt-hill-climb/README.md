<a id="prompt-hill-climb"></a>

# 提示词爬山优化（prompt-hill-climb）

创建数据集评估器，迭代提示词，直到提示词任务在整个数据集上通过。

<a id="fixture"></a>

## 测试数据

Phoenix 数据集 `banking_saas_dataset_clean`，仅包含 28 个示例，没有其他内容。这是面向银行助手的文本转 SQL 安全数据集：每个示例是一条客户用自然语言提出的问题，参考答案要么是仅针对该客户自身 `user_id` 的 SQL 查询，要么是预设的拒绝回复。约一半问题是查询余额、交易和付款的合法请求；其余问题尝试读取其他用户的数据、注入 SQL、写入数据库或提升权限，必须拒绝。

- `input`：`{"messages": [{"role": "user", "content": <question>}]}`
- `output`：`{"reference": <SQL or refusal>}`
- `metadata`：`{"id": 1..28, "user_id": "usr_..."}`

<a id="steps-and-verifiers"></a>

## 步骤与验证器

检查通过 `arize-phoenix-client` 和类型化 GraphQL 客户端读取 Phoenix；后者由 `make codegen-harbor-graphql` 根据 `evals/harbor/verifiers/harbor_verifiers/graphql/operations/*.graphql`，针对 `js/app/schema.graphql` 编译生成。镜像中安装了共享包 `harbor_verifiers`。

1. `step_01_create_evaluator`
   - 指令：为数据集关联一个精确匹配评估器（忽略代码围栏和空白字符）。
   - 验证器：
     - `one_evaluator_attached`：数据集恰好绑定一个评估器。
     - `evaluator_is_exact_match`：对每个示例，参考答案原文、包裹代码围栏的版本及填充空白字符的版本都必须通过，得分恰好为 1；修改一个 Token 的版本及空输出必须失败，得分恰好为 0。候选输出通过 Phoenix 的 `evaluatorPreviews` 变更在评估器自身的沙箱中运行。LLM 评估器直接判定失败。
     - `no_experiments_yet`：不存在实验，且数据集仍有 28 个示例。
2. `step_02_hill_climb`
   - 指令：先用空提示词建立基线，然后每个提示词运行一次实验，直到全部 28 个示例通过。
   - 验证器：
     - `first_experiment_imperfect`：至少有两个实验，且第一次实验的得分低于 1.0。
     - `all_experiments_fully_scored`：每次实验有 28 次运行，每次运行均由评估器评分。
     - `last_experiment_passes_all`：最后一次实验没有出错的运行，且有 28 次通过。
     - 另外写入 `first_score`、`last_score` 和 `best_score`。
3. `step_03_compare`
   - 指令：比较第一次和最后一次实验，展示结果发生变化的示例，并在最后一次实验中记录经验。
   - 验证器：
     - `no_new_experiments_or_scores`：步骤开始后未创建任何实验或标注，开始时间取该步骤 ATIF 轨迹中的第一个时间戳。
     - `reply_names_both_experiments`：最终回复中提及第一次和最后一次实验的名称。
     - `reply_links_comparison_view`：回复包含 `/datasets/<id>/compare?experimentId=...` 链接，且比较对象恰好为这两个实验。
     - `learning_recorded_on_last_experiment`：最后一次实验的元数据中包含一个不早于步骤开始时间的日期。
     - `judge_accepts_comparison`：LLM 裁判（由 `PHOENIX_EVAL_JUDGE_PROVIDER` 和 `PHOENIX_EVAL_JUDGE_MODEL` 配置，默认使用 OpenAI `gpt-5-nano`）确认回复中的得分与实际一致，比较了延迟和成本，引用了结果确实发生变化的示例，并给出了结论。
