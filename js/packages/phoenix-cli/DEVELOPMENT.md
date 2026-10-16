<a id="development-guide"></a>

# 开发指南

本文档提供面向 Phoenix CLI 包开发者的信息。

<a id="setup"></a>

## 配置

在仓库根目录：

```bash
pnpm install
```

<a id="building"></a>

## 构建

```bash
pnpm build
```

<a id="testing"></a>

## 测试

```bash
pnpm test
```

<a id="cli-design-principles"></a>

## CLI 设计原则

CLI 应遵循以下原则：

1. **轻量**：尽量减少依赖，快速启动
2. **直观**：命令应易于发现和使用
3. **一致**：遵循成熟的 CLI 模式和约定
4. **可扩展**：易于添加新命令和功能

<a id="architecture"></a>

## 架构

CLI 使用现有 `@arizeai/phoenix-client` 库进行所有 Phoenix API 交互。

<a id="directory-structure"></a>

### 目录结构

```
src/
├── cli.ts          # Main CLI entry point
├── commands/       # Command implementations
├── utils/          # Utility functions
└── index.ts        # Library exports
```

<a id="adding-commands"></a>

## 添加命令

> **待办：** 命令框架实现后，补充添加新命令的文档。
