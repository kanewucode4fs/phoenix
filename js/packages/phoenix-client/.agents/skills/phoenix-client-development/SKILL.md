---
name: phoenix-client-development
description: "@arizeai/phoenix-client TypeScript SDK 开发指南：运行和恢复实验，通过基于栈的挂载/分离管理 OpenTelemetry 追踪提供程序，编写 vitest 单元测试和集成测试。用于为 phoenix-client 新增功能、调试实验生命周期或提供程序清理、修改数据集/提示词/会话/Span API，或为 js/packages/phoenix-client/ 目录编写测试时。"
license: Apache-2.0
metadata:
  author: oss@arize.com
  version: "1.0.0"
  languages: TypeScript
  internal: true
---

<a id="phoenix-client-development"></a>

# Phoenix Client 开发

Phoenix AI 可观测性的 TypeScript SDK：数据集、实验、提示词、会话、Span 和追踪。

编写新代码前，先阅读当前工作目录中的现有代码。

<a id="rule-files"></a>

## 规则文件

| 规则文件              | 阅读时机                                              |
| ---------------------- | --------------------------------------------------------- |
| `rules/experiments.md` | 实验执行、任务运行器、评估器连接      |
| `rules/prompts.md`     | 提示词辅助函数、选择器结构、服务器版本限制    |
| `rules/tracing.md`     | OpenTelemetry 追踪提供程序、Span 导出、全局状态 |
| `rules/testing.md`     | 单元测试、集成测试、测试数据              |

<a id="build-and-test"></a>

## 构建与测试

```bash
cd js/
pnpm --filter phoenix-client test
```

测试使用 **vitest**。测试文件位于 `test/`，命名为 `*.test.ts`。
