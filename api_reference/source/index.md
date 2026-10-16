---
myst:
  html_meta:
    "description lang=zh-CN": |
      Phoenix 文档首页，
      提供站点其他内容的链接。
html_theme.sidebar_secondary.remove: true
---

<a id="arize-phoenix-python-reference"></a>

# Arize Phoenix Python 参考文档

欢迎阅读 Arize Phoenix 的 Python 参考文档。本文档详细介绍 Phoenix 的 Python API 及各项功能的使用方法。如需包含教程、快速入门和概念说明的完整使用指南，请参阅[完整文档](https://arize.com/docs/phoenix)。

<a id="sub-packages"></a>

## 子包

`arize-phoenix` 包包含完整的 Phoenix 平台。如果已经部署了 Phoenix 平台，也可以使用以下轻量级 Python 包与平台交互。

- **[arize-phoenix-otel](https://phoenix-otel.readthedocs.io/)**：对 OpenTelemetry 基础能力进行轻量封装，并提供适用于 Phoenix 的默认配置。
- **[arize-phoenix-client](https://phoenix-client.readthedocs.io/)**：通过 OpenAPI REST 接口与 Phoenix 服务端交互的轻量级客户端。

- **[arize-phoenix-evals](https://phoenix-evals.readthedocs.io/)**：用于评估大语言模型（LLM）应用的工具，支持 RAG 相关性、回答相关性等评估。
