<a id="postgresql-json-vs-jsonb-demo"></a>

# PostgreSQL JSON 与 JSONB 演示

本项目展示 PostgreSQL JSON 和 JSONB 数据类型的主要区别，最明显的是键顺序处理：

```
Original input: { "z": 26, "a": 1, "m": 13 }

JSON output:    { "z": 26, "a": 1, "m": 13 }     | JSONB output:    { "a": 1, "m": 13, "z": 26 }
(preserves original order)                        | (sorts keys alphabetically)
```

以下是测试数据中的真实示例：

```
Original input order: ['QVZZCJFR', 'DAUFW', 'DXRMYF', 'SEETRJBUU', ...]

JSON output: {                | JSONB output: {
  "QVZZCJFR": 8,              |   "B": 1,
  "DAUFW": 5,                 |   "XT": 2,
  "DXRMYF": 6,                |   "RHD": 3,
  "SEETRJBUU": 9,             |   "YPSE": 4,
  "YPSE": 4,                  |   "DAUFW": 5,
  "DEGAZFI": 7,               |   "DXRMYF": 6,
  "XT": 2,                    |   "DEGAZFI": 7,
  "RHD": 3,                   |   "QVZZCJFR": 8,
  "B": 1,                     |   "SEETRJBUU": 9,
  "JCXSRJOEXE": 10            |   "JCXSRJOEXE": 10
}                             | }
```

JSON 精确保留输入格式，而 JSONB 按字典序重排键以优化查询。本项目提供实际示例和性能比较，帮助开发者理解两种类型的使用时机。

<a id="features"></a>

## 功能

- **键顺序比较**：展示 JSON 如何保留键顺序，以及 JSONB 如何按字典序排序
- **性能基准**：比较 JSON 与 JSONB 的插入和查询性能
- **查询能力**：展示两种类型可用的查询操作和运算符
- **索引影响**：展示 GIN 索引对 JSONB 查询的影响
- **TypeScript 支持**：完整类型化代码库，具有适当类型定义

<a id="prerequisites"></a>

## 前置条件

- Node.js，v18 或更高
- pnpm，v10.2.0 或更高
- PostgreSQL，v12 或更高，可选，演示默认可使用 PGlite

<a id="installation"></a>

## 安装

1. 克隆仓库
2. 安装依赖：
   ```bash
   pnpm install
   ```

<a id="configuration"></a>

## 配置

项目可使用 PGlite（内存 PostgreSQL）或真实 PostgreSQL 数据库。在 `src/config/db-config.ts` 中配置：

```typescript
// Set to true to use PGlite, false to use PostgreSQL
export const USE_PGLITE: boolean = true;
```

使用 PostgreSQL 时，设置以下环境变量，或更新 `src/services/db-service.ts` 中的默认值：
- `DB_USER`，默认 "postgres"
- `DB_HOST`，默认 "localhost"
- `DB_NAME`，默认 "json_demo"
- `DB_PASSWORD`，默认 "postgres"
- `DB_PORT`，默认 "5432"

<a id="usage"></a>

## 使用方法

运行以下命令，了解 JSON 与 JSONB 的不同方面：

```bash
# Run the main demo (key order comparison)
pnpm start

# Run performance benchmarks
pnpm run performance

# Run query examples
pnpm run query

# Run key order comparison
pnpm run compare
```

<a id="demo-scripts"></a>

## 演示脚本

1. **compare.ts**：展示键顺序保留差异
   - 展示 JSON 如何保留输入键顺序
   - 展示 JSONB 如何按字典序重排键
   - 比较存储大小

2. **performance.ts**：对性能特性进行基准测试
   - 插入性能比较
   - 查询性能比较
   - 索引对查询的影响
   - JSONB 专有运算符性能

3. **query-examples.ts**：展示查询能力
   - 基本键访问
   - 嵌套键访问
   - 数组访问
   - 过滤
   - JSONB 专有运算符

<a id="key-findings"></a>

## 主要发现

<a id="when-to-use-json"></a>

### 适合使用 JSON 的情况
- 需要精确保留文档格式，包括空白和键顺序
- 写入较多、查询较少
- 输入校验比查询性能更重要

<a id="when-to-use-jsonb"></a>

### 适合使用 JSONB 的情况
- 需要频繁查询 JSON 数据
- 需要索引能力
- 查询性能至关重要
- 关注存储空间
- 不需要保留键顺序

<a id="development"></a>

## 开发

- `pnpm run format`：使用 Prettier 格式化代码
- `pnpm run lint`：运行 ESLint
- `pnpm run typecheck`：运行 TypeScript 类型检查

<a id="project-structure"></a>

## 项目结构

```
src/
├── config/
│   └── db-config.ts       # Database configuration
├── services/
│   └── db-service.ts      # Database service with PG/PGlite support
├── types/
│   └── db.types.ts        # TypeScript type definitions
├── compare.ts             # Key order comparison demo
├── performance.ts         # Performance benchmarks
├── query-examples.ts      # Query capabilities demo
└── index.ts              # Main entry point
```

<a id="license"></a>

## 许可证

MIT
