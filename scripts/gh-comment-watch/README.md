<a id="gh-comment-watch"></a>

# GitHub 评论跟踪工具（GH Comment Watch）

一个面向值班工程师的小型 TypeScript + React 应用，用于发现 GitHub issue/PR 中**团队尚未回复的外部用户评论**，尤其是容易被忽略的旧讨论。

它将**一个或多个仓库**中**所有未关闭**的 issue、PR 和 discussion 扫描到本地 SQLite 缓存，判断每个讨论中“最后发言者”是谁，并在 React 仪表盘中展示等待回复的条目。另有 **My queue（我的队列）**标签，显示分配给你或等待你本人评审的 issue/PR。默认监控 `Arize-ai/phoenix` 和 `Arize-ai/openinference`，每个条目都有仓库标记，界面支持按仓库筛选。

> **状态在本地持久保存。** SQLite 数据库默认位于 `~/.phoenix/.gh-comment-watch/local.db`，在用户主目录中、仓库之外，因此不会被 `git clean` 删除，也可在多个检出目录间共享。启动时会先运行 Drizzle Kit 迁移，再启动服务；重启保留本地缓存，模式升级按幂等方式应用。

> **没有活跃时间窗口限制。** 所有未关闭讨论都被跟踪，不受创建时间影响；被忽略一年的讨论正是此工具要找出的内容，绝不能因时间久远而被剔除。已关闭或合并的讨论会移出列表。工具只读取 GitHub，绝不发帖、打标签或添加回应。

<a id="what-counts-as-needs-attention"></a>

## 哪些情况算“需要关注”

对每个未关闭讨论，遍历对话（首帖及全部评论；discussion 还包括嵌套回复），忽略机器人，检查**最后一条人工内容**：

| 最后一条人工内容 | 判定 |
| --- | --- |
| 由团队成员发布 | ✅ 已处理：_"Team posted last"_（团队最后发言） |
| 外部用户发布，之后没有团队回复 | ⚠️ **需要关注** |
| discussion 超过已获取的 GraphQL 分片范围 | ⚠️ **需要关注**：_"Long discussion; review manually"_（讨论过长，请人工检查） |

“团队”指 `.github/workflows/claude.yml` 中 @claude 工作流的允许名单。已关闭或合并讨论视为已处理，不再同步。

被标记评论的作者如果**属于组织但不在允许名单中**，会显示 "Arize-ai org" 徽标，提示其可能是不在值班名单上的同事，而非外部用户。成员资格通过 `GET /orgs/{org}/members/{login}` 检查，并在 `org_membership_cache` 中缓存一周。

**Hide team-authored（隐藏团队发起的讨论）**开关默认开启，会排除由团队成员创建的讨论，即我们自己的 issue 和 PR；否则，外部用户最后回复也会触发关注，即使这本来是团队自身工作。关闭开关可包含团队发起的讨论。此开关仅适用于 Needs reply / All tracked 视图，不影响 My queue。

> 范围说明：只跟踪对话评论，不跟踪 PR 代码评审评论。issue/PR 通过 REST API 获取；discussion 没有 REST API，因此通过 GraphQL 获取，包括嵌套回复。

<a id="my-queue"></a>

## 我的队列

**My queue** 标签跟踪监控仓库中**直接分配给你**或**明确请求你本人评审**的未关闭 issue/PR。“你”默认是 `gh` 令牌所属用户，可设置 `VIEWER` 查看其他人的队列。评审请求使用 GitHub 的 `user-review-requested` 限定符，因此通过你所属团队发起的请求不算，只计算直接面向你本人的请求。每行显示 _Assigned to me_（分配给我）或 _Review requested_（请求评审）徽标，同时保留团队处理状态（如 _Team posted last_），便于判断其他人是否已参与。

<a id="requirements"></a>

## 环境要求

- Node ≥ 22、`pnpm`
- 已登录的 `gh` CLI（`gh auth login`），应用会复用其令牌；也可以设置 `GITHUB_TOKEN`。

<a id="setup--run"></a>

## 配置与运行

```bash
make gh-comment-watch
```

也可以直接运行：

```bash
cd scripts/gh-comment-watch
pnpm start          # install deps, build UI, migrate DB, serve UI + API
```

打开 http://localhost:58736 ，点击 **Sync now（立即同步）**执行首次拉取。

<a id="development-hot-reload"></a>

### 开发（热重载）

```bash
pnpm dev            # migrate DB, then run the Hono API on :58736
pnpm dev:web        # Vite UI on :5173 (proxies /api → :58736)
```

<a id="database"></a>

### 数据库

模式位于 `src/schema.ts`，迁移位于 `drizzle/`。修改模式时使用 Drizzle Kit：

```bash
pnpm db:generate    # generate a migration after editing src/schema.ts
pnpm db:migrate     # apply pending migrations to the local SQLite file
```

`DB_FILE_NAME` 可指向其他 SQLite 文件，父目录会自动创建。

<a id="architecture"></a>

## 架构

- `src/server.ts` 使用 `@hono/node-server` 运行 Hono 服务，提供 `/api/status`、`/api/items`、`/api/sync`，并从 `web/dist` 提供构建后的 React 应用。
- `src/db.ts` 在 `better-sqlite3` 上使用 Drizzle ORM，进行带类型的读写。
- `src/sync.ts`、`src/github.ts` 和 `src/discussions.ts` 通过 REST 和 GraphQL 拉取 GitHub 数据，再经 Drizzle 数据访问层写入。
- `web/src/App.tsx` 是 React 仪表盘。标签和筛选条件由 URL 查询参数（`tab`、`mine`、`type`、`repo`、`q`、`sort`）驱动，刷新或收藏筛选视图都能保留当前状态。

<a id="syncing"></a>

## 同步

服务会自行维护本地 SQLite 缓存：启动时同步一次，此后每隔 `SYNC_INTERVAL_MINUTES` 分钟同步（默认 15）。也可随时点击界面中的 **Sync now**。

**首次**同步（启动时数据库为空，或调用 `POST /api/sync?full=1`）会对所有未关闭讨论执行**基线全量扫描**，不因时间久远而丢弃。之后执行**增量**同步，只向 GitHub 请求游标之后更新的讨论：issue/PR 使用 `?since=…&sort=updated`，discussion 按 `updatedAt` 从新到旧分页，超过截止点后停止；刚关闭的讨论也会获取，以便移除。没有变化的旧记录保留。因此常规同步开销很低，安静时段几乎不获取任何讨论，同时仍可跟踪全部积压讨论。

游标是**数据水位**，而非当前时钟时间：按仓库和类型记录已实际导入的最新 `updated_at`，请求从 `watermark − SYNC_OVERLAP_MINUTES` 开始更新的讨论。由于水位不会越过未见过的数据，暂时未进入 GitHub `since` 索引的更新不会落到游标之后而被遗漏，下次同步仍能获取；若使用时钟游标，它会跳到“现在”，使该更新直到下次全量扫描前都被搁置。重叠窗口只需覆盖 GitHub 索引重排的时间。为捕获始终未重新出现的关闭或转移事件，服务还会每隔 `FULL_SYNC_INTERVAL_HOURS` 小时执行全量基线扫描（默认 24，设为 `0` 禁用）。

<a id="configuration-env-vars"></a>

## 配置（环境变量）

| 变量 | 默认值 | 含义 |
| --- | --- | --- |
| `REPOS` | `Arize-ai/phoenix,Arize-ai/openinference` | 监控的 `owner/repo` 列表，以逗号或空格分隔；单仓库仍可使用 `REPO` |
| `PORT` | `58736` | 服务端口 |
| `DB_FILE_NAME` | `~/.phoenix/.gh-comment-watch/local.db` | 本地 SQLite 缓存文件，自动创建父目录 |
| `SEED_ORG` | 第一个仓库的所有者 | 检查成员徽标的组织，假定全部仓库均属于该组织 |
| `VIEWER` | `@me`（令牌用户） | My queue 标签跟踪的个人队列所属用户 |
| `GITHUB_TOKEN` | — | 设置后替代 `gh` CLI 的令牌 |
| `CONCURRENCY` | `8` | 同步期间并发获取 GitHub 数据的数量 |
| `SYNC_INTERVAL_MINUTES` | `15` | 后台自动同步间隔，`0` 禁用 |
| `FULL_SYNC_INTERVAL_HOURS` | `24` | 清理已关闭过期记录的定期全量扫描间隔，`0` 禁用 |
| `SYNC_OVERLAP_MINUTES` | `10` | 增量同步向数据水位之前回溯的分钟数，用于覆盖 GitHub `since` 索引重排 |
