---
name: phoenix-otel-development
description: >
  phoenix-otel TypeScript 包指南：OTel 注册、基于栈的全局提供程序管理以及提供程序生命周期。
license: Apache-2.0
metadata:
  author: oss@arize.com
  version: "1.0.0"
  languages: TypeScript
  internal: true
---

<a id="phoenix-otel-development"></a>

# Phoenix OTel 开发

Phoenix 的 OpenTelemetry 注册及提供程序生命周期层，是 OTel 配置的唯一事实来源；其他 Phoenix 包委托此处处理，而非直接导入 OTel 包。

编写新代码前，先阅读当前工作目录中的现有代码。

<a id="rule-files"></a>

## 规则文件

| 规则文件                            | 阅读时机                                                          |
| ------------------------------------ | --------------------------------------------------------------------- |
| `rules/global-provider-lifecycle.md` | 全局提供程序的挂载、分离、快照/恢复、挂载栈 |
| `rules/register-api.md`              | `register()`、Span 处理器配置、公共 API 接口                |
| `rules/testing.md`                   | 提供程序生命周期、注册和 Span 导出测试               |

<a id="build-and-test"></a>

## 构建与测试

```bash
cd js/
pnpm --filter phoenix-otel test
```

双模块输出（CJS + ESM）。测试使用 **vitest**。
