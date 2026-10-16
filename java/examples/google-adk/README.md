<a id="trace-google-adk-for-java-with-phoenix"></a>

# 使用 Phoenix 追踪 Java 版 Google ADK

本示例运行一个带函数工具的 Google ADK 智能体，并将其 OpenTelemetry 追踪数据发送到本地 Phoenix 实例。OpenInference Java 代理在 JVM 启动时为 ADK 跨度补充信息，应用本身无需调用插桩器。

<a id="run-the-example"></a>

## 运行示例

需要准备 Java、Gradle、Docker、[Gemini API 密钥](https://aistudio.google.com/app/apikey)，以及已打包依赖的 OpenInference ADK Java 代理 JAR。

```bash
docker run --rm -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
```

在另一个终端中运行：

```bash
export GOOGLE_API_KEY="your-key"
export OPENINFERENCE_ADK_AGENT_JAR="/path/to/adk-agent.jar"
cd /path/to/phoenix/java/examples/google-adk
gradle -PagentJar="$OPENINFERENCE_ADK_AGENT_JAR" run
```

打开 [http://localhost:6006](http://localhost:6006)，选择 `google-adk-java` 项目。可通过 `GEMINI_MODEL`、`PHOENIX_PROJECT_NAME` 和 `OTEL_EXPORTER_OTLP_ENDPOINT` 覆盖默认设置。

`run` 任务通过 `-javaagent` 将 `agentJar` 指定的 JAR 传入 JVM。完整应用及 OpenTelemetry 配置见 [`WeatherAgent.java`](src/main/java/com/arize/phoenix/examples/adk/WeatherAgent.java)。
