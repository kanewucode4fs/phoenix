<a id="plugin-evals"></a>

# 插件评测

`phoenix-cli` 技能的行为测试，通过 `claude plugin eval` 运行。用例包括智能体故障排查提示词（粘贴的 `px trace get` 输出、症状描述和一个脚本编写任务），以及两个不应触发技能的负例。每个输入都会分别在启用和未启用插件时运行，因此主要指标是 Δ（启用插件的得分减去未启用插件的得分），而非原始通过率。

<a id="run"></a>

## 运行

在本插件目录中运行：

```bash
claude plugin eval . \
  --ablation with-without \
  --judge-model sonnet \
  --allow-tools Write "Read(//$(pwd)/**)" "Read(//$(git rev-parse --show-toplevel)/.agents/skills/**)"
```

每个选项都很重要：

- `--ablation with-without` 用于产生 Δ 对比。
- `--judge-model sonnet`：默认裁判是 haiku，容易漏掉长篇诊断中的细微差异。
- `--allow-tools Write`：用例 `prompt.md` 中的 `allowed_tools` 只是声明，不代表授权。缺少此选项，`06-tool-audit-script` 无法创建文件，两个对照组都会得 0 分。
- `--allow-tools "Read(//<plugin dir>/**)"`：沙箱默认只允许 `Read` 访问工作目录。技能链接到 `references/filter-expressions.md`；如果没有此授权，模型读取会被拒绝，并会在回答中说明。第二个 `Read(...)` 用于覆盖符号链接的目标。

添加 `--no-publish` 可将 HTML 报告保留在本地。结果写入 `evals/results/<timestamp>/`（已被 Git 忽略），包括 `aggregate-result.json` 和 `report.html`，后者包含所有提示词、答案及逐条件裁判结论。

使用 `--case 05-skill-never-loaded --runs 1` 可迭代单个用例（费用约一美元）。`--case` 接收单个 glob；`0[125]-*` 这样的方括号模式不会匹配任何内容。

<a id="reading-results"></a>

## 解读结果

- **Δ 较高**：技能教会了 Claude 原本不会自行完成的事情。
- **两个对照组都高、Δ 接近零**：Claude 已经具备该能力，此用例只用于防止回归。
- **启用插件组得分低**：可能是技能缺口，也可能是评分器缺陷，应先阅读答案再判断。

基线（2026 年 9 月、技能 3.5.0、运行 3 次）：六个应触发技能的用例平均 Δ 为 +0.25，负例为 0.00，启用插件组所有用例均达到或接近 1.0。完整运行费用约 17 美元。该基线早于从用例提示词中移除粘贴的 `px …` 命令，以及改写 `phoenix-cli` 技能描述，因此可能已经过时；依赖此结果前，应重新运行 3 次并更新基线及 `.github/workflows/plugin-evals.yml` 中的 `min_delta`。

<a id="grader-conventions"></a>

## 评分器约定

- 先运行正则评分器（`uses-px-cli`、`no-invented-flags`、`no-invented-commands`），然后为**每条判断条件**配置一个 `llm` 评分器，权重为 `weight: 0.5`。运行器的裁判只返回结论、不提供推理，并会在“所有条件均须满足”的组合规则下误判正确答案；逐条件评分解决了这一问题，也能指出具体失败条件。
- `skill-fired` 使用 `tool_used: Skill` 和 `input_match: phoenix-cli`，在消融对比中报告，但不计分。负例使用 `min: 0`、`max: 0`、`arm: both`、`input_match: phoenix`，避免将宿主中泄漏到沙箱的操作层技能计入。
- 提示词内嵌的追踪测试数据必须内部一致（令牌计数应与可见消息对应，重试消息应可区分）。Claude 会注意到不一致，将其称为插桩缺口，进而影响裁判判断。

<a id="adding-a-case"></a>

## 添加用例

复制现有目录为 `NN-<slug>/`，编写 `prompt.md` 和 `graders/`。技能已触发但答案错误的真实会话记录是最好的输入；只有这类输入才能让当前处于得分上限的启用插件组出现区分度。

`mocks/phoenix/` 中的智能体模拟服务覆盖插件的 MCP 服务，因此所有用例都无法访问真实 Phoenix。目前没有用例调用它。
