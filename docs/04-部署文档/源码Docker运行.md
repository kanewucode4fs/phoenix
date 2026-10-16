# 从当前源码构建并运行 Phoenix

目标：在本机运行当前仓库源码构建的 Phoenix，使用默认 `6006/4317`，连接 Mac 上已有的 PostgreSQL。当前数据库为 `127.0.0.1:5432/phoenix`，PostgreSQL 版本 `18.6`。

## 构建镜像

在仓库根目录执行：

```bash
docker build --progress=plain --tag phoenix-source:local .
```

使用仓库现有 `Dockerfile`，在容器内构建前端和 Python 主服务，本机无需安装前端工具或升级 uv。Python client／evals／otel 依赖按现有 Dockerfile 的 `--no-sources` 策略使用发布包，不能认为这些包的本地修改也会自动打入镜像。首次构建需要下载基础镜像及依赖；本次使用正常缓存构建，没有添加 `--no-cache`。

实测遇到 npm 元数据与包下载超时后，仅调整了 Dockerfile 的安装步骤：使用与 CI 一致的冻结锁文件、BuildKit pnpm store 缓存、4 路下载并发和 600 秒请求超时；保留原有供应链校验，不修改依赖版本或全局代理配置。

## 初始化工作目录并连接本机 PostgreSQL

Docker Desktop 容器中的 `127.0.0.1` 指向容器自身；连接 Mac 使用 `host.docker.internal`。本次已验证容器可访问 `host.docker.internal:5432`，并使用本机现有账号连接现成的 `phoenix` 数据库。没有启动 Compose 中的 PostgreSQL 16 容器，也没有新建或清空数据库。

下面是新环境的启动示例；当前容器已经运行，不需要重复执行。先在被 gitignore 忽略的 `.env.phoenix` 中设置连接串：

```dotenv
PHOENIX_SQL_DATABASE_URL=postgresql://<your-user>:<your-url-encoded-password>@host.docker.internal:5432/phoenix
```

真实凭证只保存在忽略文件或密钥管理工具中。示例中的密码须经过 URL 编码；本机账号若按现有 PostgreSQL 规则无需密码，可省略 `:<your-url-encoded-password>`。本次实际连接没有提供密码，未修改 PostgreSQL 认证规则。

仅为新建的 `phoenix-source-data` 卷设置容器用户权限：

```bash
docker volume create phoenix-source-data
docker run --rm --user 0:0 --entrypoint /usr/bin/python3 \
  --mount source=phoenix-source-data,target=/data \
  phoenix-source:local -c "import os; os.chown('/data', 65532, 65532)"
docker run --detach --name phoenix-source --restart unless-stopped \
  --publish 127.0.0.1:6006:6006 \
  --publish 127.0.0.1:4317:4317 \
  --env-file .env.phoenix \
  --env PHOENIX_WORKING_DIR=/data \
  --env PHOENIX_TELEMETRY_ENABLED=False \
  --mount source=phoenix-source-data,target=/data \
  phoenix-source:local
```

浏览器访问 [源码实例](http://localhost:6006)。HTTP／OTLP HTTP 基础地址为 `http://localhost:6006`，gRPC 为 `localhost:4317`。当前配置只监听本机，未开启 Phoenix 认证。追踪存储在 Mac 的 PostgreSQL，`/data` 卷作为工作目录保留，卷内旧 `phoenix.db` 不再作为当前数据库使用。

原 SQLite 容器保留为已停止的 `phoenix-source-sqlite-backup`，自动重启已关闭，数据卷未删除。没有把 SQLite 数据迁移到 PostgreSQL；现有 PostgreSQL 中的项目直接沿用。

## 验证与接入 demo

```bash
curl --fail http://localhost:6006/healthz
curl --fail http://localhost:6006/readyz
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006 \
  make -C examples/langgraph_phoenix_demo run
docker logs --tail 100 phoenix-source
```

也可按 [demo 的运行指南](../../examples/langgraph_phoenix_demo/README.md) 用 Python 启动，提供相同的 `PHOENIX_COLLECTOR_ENDPOINT`。在新实例中查看 `langgraph-phoenix-demo` 项目。测试 Agent 源码位于 `/Users/kanewu/Documents/TechSet/FirstAgent`，本次不修改该项目。

## 日常操作

```bash
docker stop phoenix-source
docker start phoenix-source
```

容器运行的是构建时打包的源码，不是源码目录挂载热更新；修改前后端后需要重新构建镜像并重新创建源码容器，保留 `phoenix-source-data` 卷。不要使用清理数据卷的命令来更新应用。

## 本次执行状态

代码基线：`59f7df412308ebb49ddff140902b1eaf1db58fd2`；源码版本 `20.23.0`；Docker Engine `29.8.1`，Linux arm64 构建。

验证时间：2026-10-16 20:45（北京时间）。镜像 `phoenix-source:local`，ID `sha256:2ae9c8f13dfdc3807c77d180613eb1414a99cd61268dcb9b51489d77498162ff`；运行 Python `3.13.5`，服务版本 `20.23.0`。镜像包含本次 Dockerfile 修改，不是未经修改的 HEAD 构建。

| 验证层／场景 | 总计／通过／失败／跳过 | 实测值与出处 |
|---|---|---|
| 源码镜像构建（最终一次） | 1／1／0／0 | 前端 TypeScript、Relay、Vite 和 Python wheel 构建完成；正常缓存，未使用 `--no-cache` |
| 容器连接本机 PG | 1／1／0／0 | `asyncpg` 连接 `host.docker.internal:5432/phoenix` 成功；数据库迁移版本与源码头均为 `4aad9107d196` |
| 健康／就绪 | 2／2／0／0 | `/healthz`、`/readyz` 均 200，版本头 `20.23.0` |
| 前端入口资源 | 1／1／0／0 | `/assets/index-Z0nLwEhx.js` 返回 200，5,217,345 字符 |
| 截图中的项目 GraphQL 查询 | 1／1／0／0 | 查询 `UHJvamVjdDoz` 返回 `FirstAgent`，无 GraphQL errors；未据此宣称修复了产品代码 |
| Demo 追踪入库 | 1／1／0／0 | 运行 [demo.py](../../examples/langgraph_phoenix_demo/demo.py)，直接 SQL 查询 PG：Trace `22638f7aa7bd41337e0af0d082c6ada4` 对应 8 个 Span |
| 重启后持久化与就绪 | 1／1／0／0 | `docker restart phoenix-source` 后 `/readyz` 200，按 Trace ID 查询 API 仍返回 8 个 Span |
| 上述检查合计 | 8／8／0／0 | 构建与运行检查，不是单元测试用例数 |

构建历史有两次失败：首次 GHCR 令牌请求 EOF，重试后通过；随后 npm 元数据超时，调整下载步骤后构建成功。第一次 PG 就绪检查发生在启动完成前，连接被重置；demo 的 exporter 自动重试后收到 200，且已直接在 PG 核实入库。最终构建仍有既有 `$PYTHONPATH` 未定义及 Vite chunk 大小警告，demo 有 LangChain `.text()` 弃用警告，未屏蔽。

未执行 Phoenix 全仓单元／集成测试、浏览器 E2E、真实模型调用或评测准确性验证。没有修改服务端代码来处理截图错误；切换前后该项目查询均已正常，原日志中的 `Project.name` 空值错误尚未建立稳定复现。
