# 工程目录规范对齐设计

日期：2026-10-16。状态：**用户已选择方案 B；具体目标路径与实施计划待审阅，尚未实施。**

## 1. 需求与依据

用户要求：按照全局 AGENTS.md 中的工程目录约定评估 Phoenix 如何调整，并采用 SDD 推进。结合本会话，平台、Python/TypeScript SDK、CLI、MCP、插件、教程和分发能力均应保留；主要运行环境为源码 Docker 镜像连接 Mac PostgreSQL。

已读取的规则：

- `/Users/kanewu/.codex/AGENTS.md`：项目目录结构由项目根 AGENTS.md 说明；已有项目沿用技术栈；避免过度设计和无关重构。
- `/Users/kanewu/.codex/instructions/frontend.md`：明确“沿用项目已有目录”；无既定结构时才使用 Vue 的 views/stores/router 约定；不能因参考规则提到 FSD 自动调整架构。
- Python/FastAPI、React、TypeScript 补充模式：约束模块职责及代码组织，没有规定整个仓库必须采用 backend/frontend 目录。
- [项目 AGENTS.md](../../../AGENTS.md)：沿用 Python/TypeScript 多包仓库；核心目录调整须同步核对包配置、代码生成、测试和 Docker 路径。

**已读规则没有给出统一的 backend/frontend 根目录模板。**用户随后明确选择方案 B，并要求先输出可分阶段独立验证的迁移计划。第 9 节为本次提出的目标结构，属于项目设计选择，不宣称来自全局规则。

## 2. 问题与目标

当前容易混淆的是目录职责与交付边界：服务端和前端属于平台，Python/TS SDK 可以独立发布，插件与 CLI 面向不同宿主，教程和产品文档并非运行时模块。

目标：

1. 能从根入口找到平台、SDK、CLI、插件、测试、示例、文档和部署资产。
2. 保持 Python 导入名、npm 包名、HTTP API、CLI 命令及插件入口兼容。
3. 保持源码构建、代码生成和独立分发路径有效。
4. 目录规范由项目 AGENTS.md 维护，需求、设计、计划和实现按 SDD 分阶段确认。

## 3. 方案比较

| 方案 | 做法 | 代价与结论 |
|---|---|---|
| A：保留多包结构，修正具体入口 | 保留 src、js、packages 等核心路径 | 原建议，用户未采用。 |
| B：物理迁移为新的根目录结构 | 迁移服务端、前端、SDK、部署资产，并同步真实消费者 | **用户已选择。**具体映射见第 9 节；先审阅计划，再实施。 |

不建立第二套空的 backend/frontend 目录、兼容软链接或脚本代理层来掩盖旧结构。保留的上游文件按实际用途管理，不因英文名称或目录数量直接删除。

## 4. 迁移前目录与职责

下列为现有目录的职责约定，不代表创建新的目录或移动现有文件。

```text
phoenix/
├── AGENTS.md                    项目规则、目录职责与命令入口
├── README.md                    产品入口及包元数据引用
├── DEVELOPMENT.md               本地开发说明
├── Makefile                     开发、测试、生成与构建入口
├── pyproject.toml / uv.lock      Python 主包和 workspace 配置
├── Dockerfile / docker-compose.yml
├── src/phoenix/                 Python 主服务及随包发布的资源
│   ├── server/                  API、Agent、MCP、静态 UI 与后台任务
│   ├── db/                      数据模型、迁移和 DDL
│   └── trace/、core/、utilities/ 追踪与公共能力
├── js/                          TypeScript pnpm workspace
│   ├── app/                     React 前端
│   ├── packages/                TS SDK、CLI、MCP 与内部测试工具
│   └── examples/、benchmarks/    TS 示例与基准
├── packages/                    Python client、evals、otel 和 sqlean
├── plugins/                     Codex、Claude Code 等插件分发
├── .claude-plugin/              Claude 插件市场入口
├── .cursor-plugin/              Cursor 插件分发入口
├── .agents/                     共享技能及插件资源
├── schemas/                     OpenAPI 等接口契约
├── prompts/                     评估器配置和模板输入
├── tests/                       平台测试；包测试仍随包存放
├── evals/                       Phoenix 自用评测和 Harbor 工程
├── examples/、tutorials/、java/  接入示例与教程
├── docs/                        项目文档、产品文档和 SDD 设计/计划
├── api_reference/               SDK API 文档构建
├── internal_docs/               内部设计及实验资料
├── scripts/、requirements/      工程工具及分层依赖输入
├── helm/、kustomize/            Kubernetes 部署
└── .github/                     保留的 CI、发布和自动化流程
```

根目录的托管平台配置、文档站配置和许可文件继续按实际消费者保留。源码结构与依赖保持独立：文档位置整合不代表要把 SDK 或插件并入平台运行包。

## 5. 原方案 A 的范围（不作为当前实施方案）

此前已经完成的导航整理、教程中文化、部署指南整合及用户明确要求的删除属于现有工作区。本次不重做、不覆盖，也不将其全部归为新的结构迁移。

设计确认后，仅处理仍存在的具体问题：

- `.pre-commit-config.yaml` 中两个前端专项钩子的命令目录与文件匹配规则，从旧 `app/` 对齐到 `js/app/`。
- 核对根 AGENTS.md、DEVELOPMENT.md 和文档索引中的职责表、命令与部署章节引用，修复真实失效项；已正确的内容保持原样。
- 为本次 SDD 建立设计到后续实施计划的关联，计划须明确每项改动、验证和回退方式。

不借此调整 Notebook 清理策略。当前钩子会清空部分 Notebook 输出和元数据，这是与目录迁移不同的行为变化，需要独立确定需求。

## 6. 物理迁移需要覆盖的依赖

若用户确认方案 B，后续计划至少覆盖下列链路，不能只移动目录：

| 路径 | 已确认的消费者 |
|---|---|
| `src/phoenix/` | Hatch wheel/sdist 配置、版本文件、Alembic、测试、Docker COPY、UI 静态产物输出 |
| `js/app/` | Makefile 的 APP_DIR、pnpm workspace、Vite/Relay、TS 配置、GraphQL 生成、E2E、Python 辅助脚本、CI |
| `packages/` | uv workspace、SDK 源码引用、tox changedir、发布版本 manifest、Python 发布 workflow |
| `js/packages/` | pnpm workspace、前端本地依赖、Changesets、代码生成和 npm 发布 |
| `schemas/` | Python/TS 客户端和前端类型生成、Docker 前端阶段、OpenAPI 检查 |
| `plugins/` 及共享技能 | 宿主清单、市场入口、脚本路径、技能软链接及安装后的资源完整性 |

参考：[pyproject.toml](../../../pyproject.toml)、[Makefile](../../../Makefile)、[Dockerfile](../../../Dockerfile)、[pnpm workspace](../../../js/pnpm-workspace.yaml)、[tox.ini](../../../tox.ini)。

当前 Docker 使用已发布 Python SDK，本地 uv workspace 使用源码 SDK。目录迁移不得顺带改变这一策略；需要验证镜像内实际安装的版本和行为。

## 7. 验收与回退要求

方案 A 的完成标准：

- 配置中的前端路径与实际目录一致，相关匹配规则覆盖 `js/app/` 文件。
- 修改后的配置与文档引用可解析，Make 入口仍有效。
- 核心源码、包名、生成物位置、发布和插件路径没有额外变化。
- 结果提供实际检查数量和失败项；未运行的应用测试明确说明。

若采用方案 B，计划中另行加入 Python/TS 构建与测试、OpenAPI/Relay 等生成检查、Docker 新镜像验收、PG 追踪写入及重启持久化、SDK 产物安装、CLI 和插件资源检查。分发流程可做本地构建/打包验证，不以实际发布 PyPI/npm 或推送镜像作为默认验收动作。

实施时逐项保留可独立回退的变更；不能通过删除数据库、数据卷、改密钥或改写已有未提交工作区恢复结构。当前运行容器不替换，除非后续实施范围明确包含重建部署。

## 8. SDD 当前进度

| 阶段 | 状态 |
|---|---|
| 读取全局、项目与适用补充规则 | 已完成 |
| 核对现有目录、构建及分发依赖 | 已完成静态核对 |
| 提出目标与设计方案 | 用户已选择 B；具体目标路径见第 9 节，待随计划审阅 |
| 编写实施计划与任务拆分 | 已输出关联计划，待审阅 |
| 实现、测试、交付 | 尚未开始 |

本阶段没有移动源码、修改业务代码、安装依赖、提交、推送或触发发布；没有执行新的构建或应用测试。现有 `streamline-platform-support` 记录属于此前工作，不当作本次目录迁移验收结果。

## 9. 方案 B 的目标与验收约束

实施计划：[工程目录物理迁移计划](../plans/2026-10-16-project-structure-migration.md)。

迁移理由、产物清单与依赖关系已合并到上述实施计划。

| 当前路径 | 目标路径 |
|---|---|
| `src/phoenix/` | `backend/src/phoenix/` |
| `tests/` | `backend/tests/` |
| `js/app/` | `frontend/` |
| `packages/` | `sdk/python/` |
| `js/packages/` | `sdk/typescript/` |
| `js/examples/` | `examples/typescript/` |
| `js/benchmarks/` | `benchmarks/typescript/` |
| `js/scripts/` | `scripts/typescript/` |
| `helm/`、`kustomize/` | `deploy/helm/`、`deploy/kustomize/` |

JavaScript 工作区配置移至根目录，使 frontend 和 TypeScript 包共享同一工作区；Python 主包配置仍在根目录，描述 backend 源码与 SDK 工作区。根 Makefile 直接执行新路径，保留命令名，不增加代理层。Dockerfile、Compose 和托管平台入口继续按实际消费者保留，不为清空根目录而搬迁。

`plugins/`、宿主要求的隐藏入口、共享技能、`schemas/`、`prompts/`、`evals/`、现有 Python 示例、`tutorials/`、`java/`、`docs/`、`api_reference/`、`internal_docs/`、`scripts/` 和 `requirements/` 保留现有职责。已有插件资源软链接可以按真实路径更新；禁止新增用于模拟旧源码布局的兼容软链接。

每阶段须独立提交审阅、独立执行验证，并在该阶段的提交上保持仓库可用；独立验证不等于所有迁移阶段可以并行实施。源码移动与全部路径消费者修改必须在同一阶段完成。阶段失败则停在当前阶段，不留到最后集中修复。

验收覆盖：源码与安装产物、wheel/sdist、npm tarball、生成物、CI 触发路径、插件安装资源、前端静态资源、数据库与追踪持久化。既有包名、Python 导入名、CLI 命令、API、数据库结构和版本保持不变；不新增依赖，不实际向注册表发布。每阶段记录实际测试数量、场景、环境、失败和跳过；缺少必要运行环境时标记该验收未完成，不能用静态检查替代。
