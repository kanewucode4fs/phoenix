<a id="running-evals-with-cron"></a>

# 使用 Cron 定时运行评估

本示例展示如何使用 `cron` 定时计算并上传评估结果。

<a id="setup"></a>

## 配置

安装项目依赖：

```
pip install -r requirements.txt
```

运行以下命令，基于 Arize 文档构建并持久化 LangChain Qdrant 向量存储：

```
python build_vector_store.py
```

该脚本会将向量存储持久化到 `vector-store` 目录。

运行 Phoenix：

```
python -m phoenix.server.main serve
```

在新终端中定义 LangChain `RetrievalQA` 链、接入追踪并运行，以基于新建的向量存储回答问题。

```
python run_chain.py
```

该脚本会持续循环运行，并向正在运行的 Phoenix 实例发送追踪记录。此时应确认 Phoenix 应用中能够看到这些记录。

打开新终端，使用 `crontab -e` 将以下内容添加到 crontab，并按实际情况替换 API 密钥和路径。

```
* * * * * OPENAI_API_KEY=sk-your-openai-api-key /path/to/python /path/to/phoenix/examples/cron-evals/run_evals.py > /path/to/evals.log 2>&1
```

脚本每分钟运行一次，查询过去一分钟内的相关跨度（span），计算评估结果并记录到 Phoenix。应确认 Phoenix 应用中的跨度每隔一分钟出现相应的评估标注。

ℹ️ 如果使用虚拟环境，可以在激活环境后运行 `which python`，找到 Python 解释器的路径。

ℹ️ 使用 `tail -f /path/to/evals.log` 查看评估运行日志。

ℹ️ 如果不希望将 OpenAI API 密钥直接存放在 crontab 中，可根据操作系统选择[其他方式](https://stackoverflow.com/questions/2229825/where-can-i-set-environment-variables-that-crontab-will-use)，让 cron 任务能够读取该密钥。

ℹ️ `run_evals.py` 脚本固定选择过去一分钟内的相关跨度。如果需要以其他频率运行评估，应同时调整脚本中的时间窗口和 cron 调度配置。

ℹ️ `run_evals.py` 中的评估适用于 `run_chain.py` 定义的链。如果要为自己的大语言模型（LLM）应用运行定时评估，应确认 `run_evals.py` 中的评估适合该应用。
