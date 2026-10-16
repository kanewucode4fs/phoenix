# 可信评测平台开发指南

## 项目阶段

`iteration`

## 测试 Agent

用户的测试 Agent 项目位于 `/Users/kanewu/Documents/TechSet/FirstAgent`，后续 Phoenix 接入与评测测试参考该项目。

## Vault 工作流入口

本项目「可信评测平台」的 Vault 公共规则与工作流分工见 `/Users/kanewu/Documents/Obsidian/dev-vault/VAULT.md`。
Codex 开发工作流通过对应的 `dev-*` 独立技能执行；执行约定见 `/Users/kanewu/Documents/Obsidian/dev-vault/.codex/workflows/execution.md`，业务步骤见 `/Users/kanewu/Documents/Obsidian/dev-vault/.codex/skills/dev-*/SKILL.md`。

## 工程入口与目录职责

本工程沿用 Phoenix 的 Python/TypeScript 多包仓库结构。项目文档从 [文档总索引](docs/00-总索引.md) 进入；开发细节见 [DEVELOPMENT.md](DEVELOPMENT.md)。

| 要处理的内容 | 目录或入口 |
|---|---|
| 后端服务、API、Agent、MCP | `src/phoenix/server/` |
| 数据库模型与迁移 | `src/phoenix/db/` |
| 追踪解析与公共能力 | `src/phoenix/trace/`、`src/phoenix/core/`、`src/phoenix/utilities/` |
| React 前端 | `js/app/` |
| Python SDK、评估库和原生扩展 | `packages/` |
| TypeScript SDK、CLI、MCP 与共享库 | `js/packages/` |
| 接口契约与评估器生成输入 | `schemas/`、`js/app/schema.graphql`、`prompts/` |
| 测试与评测 | `tests/`、`js/app/tests/`、各包测试目录、`evals/` |
| 教学和接入示例 | `examples/`、`tutorials/`、`js/examples/`、`java/examples/` |
| 插件分发和共享技能 | `plugins/`、`.claude-plugin/`、`.cursor-plugin/`、`.agents/` |
| 项目文档、产品文档和内部设计 | `docs/00-总索引.md`、`docs/phoenix/`、`internal_docs/` |
| 镜像和 Compose 部署 | 根 `Dockerfile`、`docker-compose.yml` |
| 其他部署方案 | `helm/`、`kustomize/`、`render.yaml`、`azuredeploy.json`、`app.json` |
| 工程脚本与自动化 | `scripts/`、`.github/workflows/`、`Makefile` |

前端依赖本地 TypeScript workspace 包；Python 开发环境通过 uv workspace 引用 `packages/`。这些是实际依赖，不能仅因目录名称类似就合并或删除。核心目录调整需要同时核对包配置、生成脚本、测试与 Docker 构建路径。

## 开发、测试与部署

开发、测试、静态检查使用 Makefile 统一入口，完整目标见 `make help`。Python 使用 uv，TypeScript 使用 pnpm；版本以锁文件和项目配置为准。

| 场景 | 命令 |
|---|---|
| 准备开发环境 | `make setup` |
| 前后端联合开发 | `make dev`（需要 dekit） |
| 分别开发前后端 | `make dev-backend`、`make dev-frontend` |
| Python、前端、TS 包测试 | `make test-python`、`make test-frontend`、`make test-ts` |
| 静态检查 | `make lint`、`make typecheck` |
| 同步模型价格 | `make sync-models` |
| 核对 Compose 配置 | `docker compose config --quiet` |
| 构建并启动根 Compose | `docker compose up --detach --build` |

Dockerfile + Compose 是当前项目的主要部署入口；其他部署方案和 SDK/插件发布能力继续保留。根 Compose 为示例配置，生产配置及凭证要求见 [部署指南](docs/04-部署文档/部署指南.md)。`make dev-docker` 是独立的开发环境，不是根 Compose。

根 Dockerfile 构建当前前后端源码，但 Python client/evals/otel 通过 `--no-sources` 使用锁定的发布包。修改 `packages/` 后必须单独核实镜像内包版本与内容；不能仅凭本地 workspace 测试通过就认定生产镜像包含修改。详见部署指南的“镜像与本地 SDK 的边界”。

## 审计报告输出位置

安全检查、交付审计等报告统一生成到 `docs/06-交付审计/`。本约定覆盖技能中的默认报告目录（包括 `sec-skill` 的 `docs/security-audit/`），不再另建报告目录。此约定不自动迁移或删除历史报告。

## Python 依赖版本策略

生产依赖的 `pyproject.toml` 不得新增预发布版本（`aN`、`bN`、`rcN`、`.devN`，详见 [PEP 440](https://peps.python.org/pep-0440/)）。pip 默认排除预发布版本，生产依赖中的预发布约束可能导致解析失败或要求用户使用不稳定版本。开发和测试依赖组可在确有必要时使用预发布版本。
