<a id="k8s-test-setup-for-role_attribute_path"></a>

# ROLE_ATTRIBUTE_PATH 的 Kubernetes 测试环境

此配置测试在 Kubernetes 环境中，`ROLE_ATTRIBUTE_PATH` 能否使用常量值（如 `'MEMBER'`），而无需设置 `ROLE_MAPPING`。

<a id="prerequisites"></a>

## 前置条件

- 已启用 Kubernetes 的 Docker Desktop
- 已配置可访问集群的 kubectl
- Helm 3.x

<a id="setup"></a>

## 配置步骤

<a id="1-verify-youre-using-docker-desktop-not-production"></a>

### 1. 确认正在使用 Docker Desktop（不能是生产环境）

```bash
# Check current context - MUST be "docker-desktop"
kubectl config current-context

# If not docker-desktop, switch to it:
kubectl config use-context docker-desktop

# Double-check you're on the right cluster before proceeding
kubectl cluster-info
```

> **⚠️ 警告**：如果当前上下文指向生产集群，请勿继续！

<a id="2-build-the-oidc-dev-image"></a>

### 2. 构建 OIDC 开发镜像

```bash
cd scripts/docker/devops

# Build the image (Docker Desktop K8s uses the same Docker daemon, so no need to load)
docker build -t oidc-dev:local ./oidc-server
```

<a id="3-deploy-postgres"></a>

### 3. 部署 PostgreSQL

```bash
kubectl apply -f k8s/postgres.yml

# Wait for Postgres to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=60s
```

<a id="4-deploy-phoenix-with-oidc-sidecar"></a>

### 4. 部署带 OIDC 边车的 Phoenix

```bash
# Apply the OAuth secret (contains ROLE_ATTRIBUTE_PATH='MEMBER' with NO ROLE_MAPPING)
kubectl apply -f k8s/test-secret.yml

# Install Phoenix via Helm (path is relative to scripts/docker/devops)
helm install phoenix ../../../helm -f k8s/test-values.yml

# Add OIDC dev server as sidecar to Phoenix pod
kubectl patch deployment phoenix --patch-file k8s/phoenix-oidc-sidecar-patch.yml

# Wait for Phoenix to be ready (may take a moment after patch)
kubectl wait --for=condition=ready pod -l app=phoenix --timeout=120s
```

<a id="5-verify-the-environment-variable"></a>

### 5. 验证环境变量

```bash
# Check that the secret value is correctly set
kubectl get secret phoenix-oauth-test -o jsonpath='{.data.PHOENIX_OAUTH2_DEV_ROLE_ATTRIBUTE_PATH}' | base64 -d && echo

# Expected output: 'MEMBER' (with single quotes)
```

<a id="6-test-the-oidc-login"></a>

### 6. 测试 OIDC 登录

```bash
# Port-forward both Phoenix (6006) and OIDC sidecar (9000) from the same pod
kubectl port-forward deploy/phoenix 6006:6006 9000:9000
```

然后：

1. 在浏览器中打开 http://localhost:6006
2. 点击 "Login with OIDC Dev"
3. 系统会自动以测试用户身份登录
4. 查询数据库，验证用户角色：

```bash
kubectl exec deploy/postgres -- psql -U postgres -d postgres -c \
  "SELECT u.username, u.email, r.name as role FROM users u JOIN user_roles r ON u.user_role_id = r.id WHERE u.oauth2_client_id IS NOT NULL;"
```

5. **预期结果**：用户角色应为 MEMBER，而非 VIEWER

<a id="what-were-testing"></a>

## 测试目标

关键问题：`ROLE_ATTRIBUTE_PATH='MEMBER'`（JMESPath 常量表达式）能否在无需 `ROLE_MAPPING` 的情况下正确分配 MEMBER 角色？

<a id="cleanup"></a>

## 清理

```bash
helm uninstall phoenix
kubectl delete -f k8s/test-secret.yml
kubectl delete -f k8s/postgres.yml
```
