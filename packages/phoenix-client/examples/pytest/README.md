<a id="phoenix-eval-ci-pytest"></a>

# Phoenix 评估 CI（pytest）

将 LLM 评估作为普通 pytest 套件运行，并根据结果控制 CI 是否通过。

- `test_evals.py`：使用 `@pytest.mark.phoenix` 和 `log_output` / `log_evaluation` 辅助函数的评估套件示例。
- `eval-ci.yml`：可直接复制的 GitHub Actions 工作流，用于安装插件、运行套件，并根据 pytest 退出码使作业失败。其中包含一个已注释的可选步骤，可用打印的摘要创建或更新一条 PR 评论。

<a id="quick-start"></a>

## 快速开始

```bash
pip install "arize-phoenix-client[pytest]" pytest
export PHOENIX_COLLECTOR_ENDPOINT=...   # your Phoenix endpoint
export PHOENIX_API_KEY=...              # if your deployment requires auth
pytest
```

安装 `pytest` 扩展依赖后，插件自动启用。完整的标记、环境变量及 CI 判定参考见[评估 CI 文档](https://arize.com/docs/phoenix/datasets-and-experiments/how-to-experiments/eval-ci-with-pytest)。
