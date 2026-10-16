<a id="phoenix-development-environment"></a>

# Phoenix 开发环境

完整的 Docker Compose 开发环境，包含 Phoenix、PostgreSQL、Grafana、Prometheus 和 OIDC 认证，使用 Traefik 反向代理。

<a id="quick-start-via-tox"></a>

## 快速开始（通过 Tox）

```bash
# Start all services (most common)
tox r -e docker_devops

# Stop all services  
tox r -e docker_devops -- down
```

<a id="access"></a>

## 访问地址

- **Phoenix**：http://localhost:18273/phoenix/
- **SMTP 邮件**：http://localhost:18273/mail/
- **数据库**：localhost:5433（postgres/postgres）

<a id="commands-via-tox"></a>

## 命令（通过 Tox）

```bash
tox r -e docker_devops           # Rebuild + start (DEFAULT - use for code changes)
tox r -e docker_devops -- rebuild # Full rebuild (slowest - when dependencies change)
tox r -e docker_devops -- down    # Stop all services
tox r -e docker_devops -- destroy # Nuclear option (wipes all data!)
```

<a id="which-command-to-use"></a>

## 应使用哪个命令

- **修改了代码** → `tox r -e docker_devops`
- **修改了依赖** → `tox r -e docker_devops -- rebuild`
- **需要重新开始** → `tox r -e docker_devops -- destroy`

<a id="alternative-direct-script-usage"></a>

## 另一种方式：直接使用脚本

也可以直接使用 dev.sh 脚本：

```bash
./dev.sh up          # Same as tox r -e docker_devops
./dev.sh rebuild     # Same as tox r -e docker_devops -- rebuild
./dev.sh down        # Same as tox r -e docker_devops -- down
./dev.sh destroy     # Same as tox r -e docker_devops -- destroy
```
