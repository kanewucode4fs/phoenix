<a id="postgresql-with-tls-setup"></a>

# PostgreSQL TLS 设置

本示例展示如何设置启用 TLS 加密的 PostgreSQL。

<a id="quick-start"></a>

## 快速开始

1. 生成证书：
   ```bash
   python generate_pg_certs.py
   ```

2. 启动 PostgreSQL：
   ```bash
   docker compose up -d
   ```

3. 查看日志：
   ```bash
   docker compose logs postgres
   ```

4. 测试连接：
   ```bash
   python test_connection.py
   ```

<a id="prerequisites"></a>

## 前置条件

- 已安装 Docker 和 Docker Compose
- 已安装 Python 3.x
- OpenSSL，用于生成证书

<a id="configuration-details"></a>

## 配置详情

配置包括：
- 启用 TLS 加密的 PostgreSQL 服务器
- 用于安全通信的服务器证书
- 自定义 PostgreSQL 配置文件
- 通过 Docker 卷持久化存储数据

<a id="tips"></a>

## 提示

- **证书生成**：`generate_pg_certs.py` 脚本创建自签名 CA，并生成服务器和客户端证书。生成的证书位于 `certs` 目录。

- **连接测试**：`test_connection.py` 脚本使用 `psycopg`、`asyncpg` 驱动和 SQLAlchemy 测试连接，验证 TLS 设置能与不同 PostgreSQL 客户端配合。

- **安全配置**：
  - `pg_hba.conf` 要求远程连接使用 SSL
  - 本地连接（127.0.0.1）使用 MD5 身份验证
  - 本地 Unix socket 连接使用 trust 身份验证

- **证书文件**：
  - `server.crt` 和 `server.key`：服务器证书和私钥
  - `client.crt` 和 `client.key`：客户端证书和私钥
  - `root.crt`：用于校验服务器证书的根 CA 证书

- **Docker 卷**：
  - PostgreSQL 数据持久化至名为 `postgres-data` 的 Docker 卷
  - 容器重启后数据仍保留
  - 如需重新开始，可通过 `docker compose down -v` 删除卷

- **连接字符串**：连接数据库时需要指定：
  - 服务器主机名，localhost
  - 端口，5432
  - 数据库名称，postgres
  - 用户名，postgres
  - 密码，phoenix
  - SSL 参数，证书和校验模式

<a id="troubleshooting"></a>

## 排障

遇到问题时：
1. 检查证书是否成功生成
2. 确认 PostgreSQL 容器正在运行
3. 确保证书权限正确
4. 查看容器日志中的错误消息
