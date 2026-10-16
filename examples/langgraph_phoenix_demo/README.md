# LangChain + LangGraph 接入 Phoenix

这个最小 Python 示例用于观察一条工作流如何进入 Phoenix：LangGraph 编排两个节点，LangChain 组织 Prompt、模拟聊天模型和输出解析，OpenInference 自动生成父子 Span，Phoenix 接收并展示追踪。

示例默认使用 `FakeListChatModel`，固定返回检索内容，不调用真实模型，也不需要模型 API Key。它演示框架接入与追踪，不用于衡量模型回答质量。本示例只发送追踪，不创建评测数据集或实验。

示例会在终端与 Phoenix Trace 中记录问题、参考资料和回答，请使用非敏感演示数据。

## 1. 准备环境

- 安装 `uv`；示例使用 uv 管理的 Python 3.12。`make` 仅是快捷入口。
- 准备一个可访问的 Phoenix 服务，默认 `http://localhost:6006`。当前仓库后端的启动入口是根目录的 `make dev-backend`，需先按仓库开发要求完成环境安装；已有服务时直接使用。
- 示例独立解析 `requirements.txt`，不会安装整个 Phoenix 主服务，也不修改主仓库的依赖或锁文件。`--no-config --no-project` 用于隔离主仓库的 uv 版本和 workspace 约束。

新增依赖的用途：`langchain-core` 提供 Prompt／模拟模型／输出解析，`langgraph` 提供图编排，`arize-phoenix-otel` 配置导出，`openinference-instrumentation-langchain` 捕获 LangChain／LangGraph 调用。测试时额外使用 pytest。

## 2. 运行 demo

直接用 Python 运行：

```bash
cd examples/langgraph_phoenix_demo
uv --no-config venv --python 3.12 .venv
source .venv/bin/activate
uv --no-config pip install -r requirements.txt
python demo.py
python demo.py "LangGraph 是什么？"
```

也可以在仓库根目录使用快捷入口：

```bash
make -C examples/langgraph_phoenix_demo run
```

第一次运行会解析并下载依赖。默认问题为“Phoenix 可以做什么？”，终端打印回答、Phoenix 项目名和本次 Trace ID。

另试两个问题：

```bash
make -C examples/langgraph_phoenix_demo run ARGS='LangGraph是什么？'
make -C examples/langgraph_phoenix_demo run ARGS='月球上有多少只猫？'
```

第二个问题没有对应知识，将返回“演示知识库中没有相关信息。”。需要包含空格的问题时，可用 `ARGS='"你的完整问题"'`。

连接其他 Phoenix 实例时使用环境变量：

```bash
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006 \
PHOENIX_PROJECT=langgraph-phoenix-demo \
make -C examples/langgraph_phoenix_demo run
```

如果 Phoenix 启用认证，通过进程环境提供 `PHOENIX_API_KEY`；真实密钥不要写入示例代码、README 或版本库。连接其他实例时，把上面的 endpoint 替换为其基础 URL，HTTP exporter 会处理 `/v1/traces` 路径。

## 3. 在 Phoenix 中查看

打开 Phoenix，进入 **Projects → langgraph-phoenix-demo → Traces**。使用终端打印的 Trace ID 找到本次调用；摄入异步完成时可稍后刷新。

展开父子轨迹，可以查看以下调用的输入、输出、耗时和状态：

```text
qa_demo                         整体问答，入口位于 main()
└─ LangGraph                    状态图
   ├─ retrieve                  本地关键词检索
   └─ answer                    回答节点
      └─ RunnableSequence       LangChain 调用链
         ├─ ChatPromptTemplate  问题与参考资料
         ├─ FakeListChatModel   模拟聊天模型
         └─ StrOutputParser     转换为字符串
```

这里的模型输出是预设内容，没有真实模型用量，不能把界面中的模型 Span 当成真实推理、Token 统计或费用测量。若没有收到追踪，检查服务地址、认证配置及终端的 exporter 错误；导出队列排空不等于服务端已经持久化。

## 4. 看懂接入代码

完整代码见 [demo.py](./demo.py)：

1. `register(...)` 创建 Phoenix OTel provider，读取服务地址及认证环境变量。
2. `LangChainInstrumentor().instrument(tracer_provider=provider)` 为两个框架接入自动追踪。
3. `StateGraph` 连接 `START → retrieve → answer → END`，节点通过 `DemoState` 传递数据。
4. `prompt | model | StrOutputParser()` 构成 LangChain 调用链。
5. 进程退出前 `force_flush()`／`shutdown()` 等待追踪导出。

接入自己的应用时，保留 provider 与 instrumentor 初始化，把 `build_graph()` 中的示例节点替换为业务逻辑即可。真实模型可使用对应的 LangChain 模型适配包，替换 `FakeListChatModel`；本示例没有预装供应商 SDK 或替你配置真实模型凭证。

## 5. 运行测试

```bash
make -C examples/langgraph_phoenix_demo test
```

测试在内存中接收真实埋点，无需运行 Phoenix：检查两类已知问题、未命中问题，以及节点／模型 Span 是否属于同一条连通追踪、模型输入是否包含问题和检索内容。它不替代真实服务入库验证。

官方参考：[LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)、[LangChain 模拟聊天模型](https://reference.langchain.com/python/langchain-core/language_models/fake_chat_models/FakeListChatModel)、[Phoenix 追踪](https://arize.com/docs/phoenix/tracing/concepts-tracing/how-does-tracing-work)。

## 6. 验证记录

源码 Docker 实例 `20.23.0` 及本机 PostgreSQL 的验证见 [统一部署指南](../../docs/04-部署文档/部署指南.md#source-docker-verification)。下文是切换前对旧 `20.22.0` 发布镜像的历史验证，旧 Trace 不保证在当前数据库中存在。

提交前于 2026-10-16 20:48（北京时间）重新运行 `make test`：本文件所列同一组 4 项测试全部通过，失败 0、跳过 0，耗时 0.32 秒，仍有 3 条依赖弃用警告。测试文件为 [test_demo.py](./test_demo.py)，Python `3.12.13`、pytest `8.4.2`；测试时 HEAD 仍为下述代码基线，新增代码尚未提交。

验证时间：2026-10-16 19:35（北京时间）；代码基线 `59f7df412308ebb49ddff140902b1eaf1db58fd2`。环境为 macOS arm64、uv `0.11.16`、uv 管理的 Python `3.12.13`、pytest `8.4.2`。四项直接运行依赖已固定为 `requirements.txt` 中的实测版本；OTel SDK 实际解析为 `1.45.1`。

实际连接的本地 Phoenix HTTP 响应版本是 **20.22.0**，与当前源码版本 **20.23.0** 不同。以下入库结果证明此 demo 对运行中的 20.22.0 服务可用，不代表已运行或验收当前源码构建。本轮没有重建或重启容器，因此没有 `--no-cache` 构建。

| 验证层 | 总计／通过／失败／跳过 | 出处 |
|---|---|---|
| Demo 自动测试 | 4／4／0／0 | [test_demo.py](./test_demo.py)，`make test`，无需 Phoenix |
| 真实服务接入 | 3／3／0／0 | `make run` 运行三个问题后，按 Trace ID 请求 `/v1/projects/langgraph-phoenix-demo/spans` 检查入库 |
| 上述两层合计 | 7／7／0／0 | 按验证层计数，三个问答场景在两层分别验证，不表示七种不同业务场景 |

自动测试逐项结果：

- `test_answer_uses_retrieved_knowledge[phoenix_question]`：回答和上下文均包含“追踪”“评测”，通过。
- `test_answer_uses_retrieved_knowledge[langgraph_question]`：回答和上下文均包含“节点”“状态”，通过。
- `test_unknown_question_has_no_fabricated_answer`：实际回答为“演示知识库中没有相关信息。”，通过。
- `test_graph_exports_connected_trace_with_model_input`：两个节点存在，全部 Span 归属一个 Trace、父 Span 可解析，恰好一个模型 Span，其输入含问题和检索内容，通过。

先运行未实现的 `build_graph()` 时，上述 4 项均因 `NotImplementedError` 失败；实现后转为 4 项通过。此次没有修复既有产品 bug，未做修复撤回变异测试。

实际入库的三个场景如下，每条均为 HTTP 200、**8 个 Span、1 个根 Span、1 个模型 Span**；父子关系连通，根输出与终端回答一致。每条的状态统计为 7 个 OK、1 个 UNSET（手动创建的根 Span），没有 ERROR；合计 24 个 Span。

| 场景 | 实测输出 | Trace |
|---|---|---|
| Phoenix 问题 | Phoenix 可以采集应用追踪、查看节点输入输出，并管理数据集、离线评测和实验对比。 | [d1ff909e67486891755036cb3f948dac](http://localhost:6006/redirects/traces/d1ff909e67486891755036cb3f948dac) |
| LangGraph 问题 | LangGraph 用共享状态、节点和边组织工作流，适合编排包含多个步骤的应用。 | [78a9c9611146d6984485b4ac41e0537d](http://localhost:6006/redirects/traces/78a9c9611146d6984485b4ac41e0537d) |
| 知识未命中 | 演示知识库中没有相关信息。 | [883adf1b0adcea1557182f67762496dc](http://localhost:6006/redirects/traces/883adf1b0adcea1557182f67762496dc) |

最终自动测试仍有 **3 条依赖弃用警告**：OpenInference 读取 LangChain 消息时调用 `.text()`，LangChain 推荐改为 `.text` 属性；每次独立运行 demo 也出现同类警告。本示例没有屏蔽警告或修改依赖代码。本次未执行 Phoenix 主工程测试、浏览器 E2E、真实模型调用或评测准确性验证。
