<a id="cli-agent-starter-kit"></a>

# CLI Agent 入门套件

集成 AI SDK、Anthropic Claude 和 Phoenix 可观测性的 TypeScript CLI Agent，展示采用声明式工具架构的 Phoenix 文档助手。

<a id="quick-start"></a>

## 快速开始

```bash
# Install and setup
pnpm install
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run (auto-starts Phoenix)
pnpm dev
```

**环境要求：** Node.js 22+ （见 `.nvmrc`）, pnpm, Docker Desktop, Anthropic API 密钥

**命令：** `/help`, `/exit`

**Phoenix UI:** http://localhost:6006

<a id="project-structure"></a>

## 项目结构

```
src/
├── cli.ts              # Entry point
├── agent/              # Agent factory
├── tools/              # Tool definitions
│   ├── index.ts        # Tool exports
│   ├── datetime.ts     # Utility tool
│   └── mcp.ts          # Phoenix docs MCP
├── prompts/            # System instructions
└── ui/                 # CLI interface
```

<a id="adding-tools"></a>

## 添加工具

**1. 创建工具文件** (`src/tools/mytool.ts`):

```typescript
import { tool } from "ai";
import { z } from "zod";

export const myTool = tool({
  description: "What the tool does",
  inputSchema: z.object({/* params */}),
  execute: async (params) => {
    /* logic */
  },
});
```

**2. 导出** (`src/tools/index.ts`):

```typescript
export { myTool } from "./mytool.js";
```

**3. 注册** (`src/cli.ts`):

```typescript
const tools = { my: myTool };
```

<a id="naming-convention"></a>

## 命名约定

| 类型      | 模式         | 示例        |
| --------- | --------------- | -------------- |
| 导出    | `camelCaseTool` | `dateTimeTool` |
| 文件      | `camelcase.ts`  | `datetime.ts`  |
| Agent 键 | `camelCase`     | `dateTime`     |

<a id="tool-types"></a>

## 工具类型

- **工具函数**：简单辅助工具（datetime.ts）
- **MCP**：通过模型上下文协议集成外部服务（mcp.ts）

<a id="scripts"></a>

## 脚本

```bash
pnpm dev              # Run in development
pnpm build            # Compile TypeScript
pnpm start            # Run production build
pnpm phoenix:logs     # View Phoenix logs
pnpm eval             # Run all evaluations
```

<a id="evaluations"></a>

## 评估

内置评测框架用于测试 Agent 质量。在 `evals/` 中创建评估器、数据集和实验：

```bash
pnpm eval                      # Run all evaluations
pnpm eval:terminal-format      # Run specific eval
```

创建自定义评估器和实验的方法见 `evals/README.md`。

<a id="troubleshooting"></a>

## 故障排查

**没有追踪？** 检查 Phoenix： `pnpm phoenix:logs`

**Phoenix 无法启动？** 确保 Docker 正在运行，且端口 6006 可用

<a id="resources"></a>

## 资源

- [AI SDK 文档](https://sdk.vercel.ai/docs)
- [Phoenix 文档](https://arize.com/docs/phoenix)
