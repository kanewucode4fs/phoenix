<a id="vite-dev-server---technical-notes"></a>

# Vite 开发服务技术说明

<a id="problems--solutions"></a>

## 问题与解决方案

<a id="1-port-conflict-avoidance"></a>

### 1. 避免端口冲突

**问题：** 不希望将 Vite 的 5173 端口暴露到宿主机，以避免冲突和安全问题。
**解决方案：** 所有流量通过 Traefik 的 18273 端口路由。

- Vite 容器：`expose: ["5173"]`（仅内部可见，不设置 `ports:` 映射）
- Traefik 标签：`traefik.http.services.vite-dev.loadbalancer.server.port=5173`
- 客户端连接地址：`http://localhost:18273/phoenix/vite/...`

<a id="2-path-prefixing"></a>

### 2. 路径前缀

**问题：** Vite 默认从 `/` 提供服务，但这里需要 `/phoenix/vite/`。
**解决方案：**

- **Vite CLI：** 在 Dockerfile CMD 中使用 `vite --base /phoenix/vite/`
- **Phoenix 模板转换：** `scripts/docker/devops/Dockerfile.vite:34`
  ```dockerfile
  RUN sed -i "s|http://localhost:5173|/phoenix/vite|g" \
      /phoenix/env/phoenix/server/templates/index.html
  ```
  将以下内容：
  ```html
  <script src="http://localhost:5173/@vite/client"></script>
  ```
  转换为：
  ```html
  <script src="/phoenix/vite/@vite/client"></script>
  ```

<a id="3-hmr-websocket-routing"></a>

### 3. HMR WebSocket 路由

**问题：** HMR WebSocket 连接 18273 端口，而 Vite 监听 5173。
**解决方案：** 通过环境变量配置客户端端口。

- **docker-compose.yml：** `VITE_HMR_CLIENT_PORT=18273`
- **vite.config.mts：**
  ```ts
  server: {
    hmr: process.env.VITE_HMR_CLIENT_PORT
      ? { clientPort: parseInt(process.env.VITE_HMR_CLIENT_PORT) }
      : true  // Default behavior for local dev
  }
  ```
- 浏览器连接：`ws://localhost:18273/phoenix/vite/@vite/hmr`
- Traefik 路由到：`vite-dev:5173` 容器

<a id="4-vite-host-validation"></a>

### 4. Vite 主机验证

**问题：** Vite 阻止来自 Docker 主机名的请求。
错误：`Blocked request. This host ("vite-dev") is not allowed.`

**解决方案：** 在配置中禁用主机检查。

- **vite.config.mts：**
  ```ts
  server: {
    allowedHosts: "all"
  }
  ```
- **Vite CLI：** `--host 0.0.0.0`（监听所有网络接口）

<a id="5-traefik-routing"></a>

### 5. Traefik 路由

**问题：** 路由 Vite 资源时不能影响 Phoenix API/GraphQL 路由。
**解决方案：** 分隔命名空间，并使用路由优先级。

- **Vite 路由（优先级 100）：**
  ```yaml
  traefik.http.routers.vite-dev.rule: Host(`localhost`) && PathPrefix(`/phoenix/vite`)
  traefik.http.routers.vite-dev.priority: 100
  ```
- **Phoenix 路由（默认优先级）：**
  ```yaml
  traefik.http.routers.phoenix.rule: Host(`localhost`) && PathPrefix(`/phoenix`)
  ```
- 结果：
  - `/phoenix/vite/*` → Vite（优先级较高，先匹配）
  - `/phoenix/openapi.json` → Phoenix
  - `/phoenix/graphql` → Phoenix

<a id="6-source-code-isolation"></a>

### 6. 源码隔离

**问题：** 不希望 Docker 专用配置混入版本控制。
**解决方案：** 通过环境变量提供可选覆盖。

**js/app/vite.config.mts**（保持简洁，同时适用于本地和 Docker）：

```ts
server: {
  allowedHosts: "all",
  hmr: process.env.VITE_HMR_CLIENT_PORT
    ? { clientPort: parseInt(process.env.VITE_HMR_CLIENT_PORT) }
    : true,
  open: "http://localhost:6006"
}
```

**行为：**

- **本地开发：** 未设置环境变量 → `hmr: true`（默认端口 5173）
- **Docker：** `VITE_HMR_CLIENT_PORT=18273` → `hmr: { clientPort: 18273 }`

<a id="7-volume-mount-conflicts"></a>

### 7. 卷挂载冲突

**问题：** 宿主机的 `node_modules` 与容器内的依赖冲突。
**解决方案：** 使用匿名卷覆盖。

```yaml
volumes:
  - ../../../js/app:/phoenix/js/app:cached  # Mount source code
  - /phoenix/js/app/node_modules            # Prevent host from overwriting
```

容器的 `node_modules` 优先于宿主机目录。

<a id="architecture"></a>

## 架构

```
Browser (localhost:18273)
    ↓
Traefik (reverse proxy)
    ├─ /phoenix/vite/*  [priority:100] → vite-dev:5173
    │                                     ├─ Vite dev server
    │                                     ├─ HMR WebSocket
    │                                     └─ ESM transformation
    │
    └─ /phoenix/*       [default]      → phoenix:6006
                                          ├─ FastAPI backend
                                          ├─ GraphQL API
                                          └─ Serves index.html (--dev mode)
```

**请求流程示例：**

1. `GET /phoenix/` → Phoenix → 返回包含 `<script src="/phoenix/vite/@vite/client">` 的 HTML
2. `GET /phoenix/vite/@vite/client` → Traefik → Vite → JS 包
3. `GET /phoenix/vite/src/index.tsx` → Traefik → Vite → 转换后的模块
4. `WS /phoenix/vite/@vite/hmr` → Traefik → Vite → HMR 更新

<a id="usage"></a>

## 用法

**默认（启用 Vite）：**

```bash
cd scripts/docker/devops
./dev.sh up
```

**禁用 Vite（生产模式）：**

```bash
./dev.sh up --profile no-vite
```

**访问地址：** http://localhost:18273/phoenix/

<a id="performance-tuning"></a>

## 性能调整

**当前资源限制（docker-compose.yml）：**

```yaml
vite-dev:
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: "8.0"
```

根据宿主机性能调整。增加 CPU 可以加快：

- 首次依赖预打包
- 并发模块转换
- HMR 更新

<a id="debugging"></a>

## 调试

**检查 Vite 是否运行：**

```bash
docker-compose logs vite-dev | tail -20
# Should see: "VITE v6.x.x ready in XXX ms"
```

**直接测试 Vite：**

```bash
curl http://localhost:18273/phoenix/vite/@vite/client | head -5
# Should return JavaScript (not HTML/404)
```

**检查 Traefik 路由：**

```bash
docker-compose logs traefik | grep vite-dev
# Look for: RouterName":"vite-dev@docker"
```

**验证 HMR WebSocket：**

- 浏览器开发者工具 → Network → WS 标签
- 应看到状态码为 101 的连接：`ws://localhost:18273/phoenix/vite/@vite/hmr`
