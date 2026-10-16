# 工程结构整理实施记录

> 执行方式：在现有 `feature/streamline-platform-support` 分支直接实施，沿用用户已确认的整理方案。

**目标**：让平台、SDK、插件、示例、文档和部署入口容易查找，保留完整产品范围与既有源码路径。

**方案**：补齐现有导航和部署说明，不迁移源码、不引入依赖。主要部署方式为 Dockerfile + Compose，保留其他部署资产。

**约束**：真实凭证不进入文档；不推送、不提交；不重启现有服务、不改数据库；不以运行旧镜像证明当前代码已重新构建。

## 文件与任务

- [x] 恢复 `.claude-plugin/`、`.cursor-plugin/` 产品分发入口；开发配置 `.claude/`、`.cursor/` 继续保持删除。
- [x] 更新根 `AGENTS.md`、`DEVELOPMENT.md`，明确目录与命令入口；保留上游产品 `README.md` 原样。
- [x] 更新 `docs/00-总索引.md`，区分本项目五视图、产品文档站、SDK API 文档与内部设计。
- [x] 更新部署指南，解释云部署、Compose 与 SDK 镜像边界。
- [x] 更新 `.dockerignore`，排除不参与生产构建的根开发配置与缓存。
- [x] 核对文档路径、插件引用、Compose、workflow 与镜像构建配置。
- [x] 对现有容器做只读健康、就绪、前端资源与包版本检查，记录本次验证范围。
- [x] 从当前工作区构建独立验证镜像，核对构建和隔离运行结果。

## 完成标准

入口链接和 Make 目标可定位；平台、SDK、插件、示例、文档站、云部署资产保留；没有源码搬迁或业务代码修改。验证记录列出数量、环境与未执行项目，不能把静态检查当成完整业务验收。

## 实施取舍

- Python SDK 的本地源码与 Docker 发布包差异先明确记录，不擅自更改既有打包策略。
- 不把不熟悉的部署方案当作无用文件删除；云服务器上也可以使用 Compose。
- 本轮文档和构建上下文整理使用现有检查，不新增与文档内容一一对应的永久测试。
- 根 README 的纯导航修改会使现有 Dockerfile 的依赖安装层失去缓存。因此撤回该导航改动，导航集中到 AGENTS、DEVELOPMENT 和文档总索引，不为此次整理修改 Dockerfile。

## 验证结果

环境：2026-10-16 21:22—21:31（北京时间）；HEAD `3d5bf056492bd7de0f10d66a35af77d305924e2b`，分支 `feature/streamline-platform-support` 的未提交工作区。Docker Engine `29.8.1`、Compose `v5.5.1`，Ruby `2.6.10` / Psych `3.1.0`。

| 检查层 | 总计 / 通过 / 失败 | 场景与实测结果 |
|---|---|---|
| 文档本地链接 | 67 / 67 / 0 | 检查根 AGENTS、DEVELOPMENT、文档总索引、部署指南、技能源目录 README 和本实施记录的本地链接；撤回根 README 修改后重新核对 |
| YAML 语法 | 36 / 36 / 0 | `.github/workflows/` 33 份、`.github/actions/` 3 份；保留 workflow 的本地 action/workflow 引用均存在 |
| 插件入口 | 8 / 8 / 0 | 5 份分发 JSON 有效；`plugins/` 中 3 个软链接均可解析 |
| Compose 配置 | 1 / 1 / 0 | 根 `docker compose config --quiet` 退出 0；没有启动 Compose 数据库 |
| Make 目标预演 | 8 / 8 / 0 | `dev-backend`、`dev-frontend`、`test-python`、`test-frontend`、`test-ts`、`lint`、`typecheck`、`sync-models`；仅 dry-run，不计为应用测试通过 |
| 保留范围 | 13 / 13 / 0 | 平台、SDK、插件、教学、产品文档、Helm/Kustomize 和两个恢复的插件根入口均存在；核心源码、部署与依赖清单无内容修改，无源码重命名 |
| 现有容器运行检查 | 15 / 15 / 0 | 健康、就绪、版本、首页、9 份 JS 资源、项目 GraphQL 查询、4 个已安装 Python 包的版本读取 |
| 最终工作区镜像构建 | 1 / 1 / 0 | `docker build --progress=plain --tag phoenix-structure-check:local .` 退出 0；使用正常缓存，没有 `--no-cache` |
| 新镜像隔离运行 | 15 / 15 / 0 | 4 个 HTTP 入口、9 份首页 JS、1 个只读 GraphQL、1 次包版本检查；`--network none`，使用内存 SQLite，没有持久化卷或宿主端口映射 |

最终检查合计 **164 / 164 / 0**（静态/配置 133 项、运行检查 30 项、最终镜像构建 1 项；不是单元测试用例数）。`git diff --check` 另行通过。下文记录的先前构建失败与取消不包含在最终检查合计内。

现有容器为 `phoenix-source`，使用原镜像 `sha256:2ae9c8f13dfdc3807c77d180613eb1414a99cd61268dcb9b51489d77498162ff`。健康、就绪、版本、首页均为 HTTP 200；版本 `20.23.0`。9 份 JS 资源均为 200，主入口 `index-Z0nLwEhx.js` 为 5,218,002 bytes；只读 GraphQL 项目查询为 200，返回 1 个节点、无 errors。镜像内 Python `3.13.5`，client `3.5.0`、evals `3.9.2`、otel `0.17.2`。没有重启现有服务或写业务数据；这些结果不证明新工作区镜像已构建成功。

未执行全仓后端/前端单元测试、浏览器 E2E、真实 LLM 评测、SDK 发布、插件安装、文档站部署或云资源部署。本轮未改业务代码，未安装本地全量开发依赖；这些范围不能标为通过。

独立镜像共有三次构建尝试：首次在拉取 GHCR 认证令牌时遇到 TLS handshake timeout；第二次进入依赖下载后，因撤回根 README 的纯导航修改而主动取消；第三次使用最终工作区，前后端与依赖层命中缓存，构建成功。保留原有 `$PYTHONPATH` 未定义的 Dockerfile 警告，没有将警告屏蔽或标为已修复。

最终镜像为 `phoenix-structure-check:local`，ID `sha256:7ed94787ba5d15703eea73e3d78059c5aec62f8af17631bf8d7b1fd28c43dd1f`，Linux arm64。临时容器内启动当前镜像的 Phoenix：`/healthz`、`/readyz`、`/arize_phoenix_version`、`/` 均返回 200，版本 `20.23.0`；9 份 JS 资源均可读取，GraphQL 查询无 errors；Python 及三个 SDK 包版本与现有容器一致。验证后终止临时服务，`--rm` 自动移除临时容器，未替换现有服务。

本轮没有提交、推送或发布。SDK/插件分发与云部署资产存在不等于已实际执行发布、安装或云端验收。

最终工作区核对另发现根 `CLAUDE.md`（原指向 `AGENTS.md` 的软链接）被删除，该变化未包含在本轮执行的删除命令中；保留工作区现状，未自动恢复或归入本次导航整理。
