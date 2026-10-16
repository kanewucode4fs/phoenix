<a id="ldap-search-result-handling--openldap-protocol-compliance"></a>

# LDAP 搜索结果处理与 OpenLDAP 协议合规性

<a id="overview"></a>

### 概述

根据 RFC 4511，LDAP 搜索可返回零个、一个或多个条目。本附录记录多搜索结果的安全影响、参考实现 OpenLDAP 的行为，以及 Phoenix 的处理策略。

**涵盖主题**：
- 歧义搜索结果的安全考虑
- 基于 OpenLDAP 行为的 DN 校验要求
- 测试用模拟服务器实现的准确性
- 匿名绑定防护机制
- 日志中的个人身份信息保护
- Docker 开发和测试环境

**实现状态**：✅ 所有要求均已实现并验证，14/14 项自动测试通过。

---

<a id="1-ambiguous-search-results-security-considerations"></a>

### 1. 歧义搜索结果：安全考虑

<a id="protocol-behavior-rfc-4511"></a>

#### 协议行为（RFC 4511）

单个搜索过滤器的 LDAP 搜索操作可能返回多个条目，协议不保证结果顺序。

**示例场景**：
```ldap
Search filter: (uid=admin)
Possible results:
  - uid=admin,ou=IT,dc=example,dc=com
  - uid=admin,ou=HR,dc=example,dc=com
```

**安全风险**：若客户端未验证唯一性，直接选择 `entries[0]`，身份验证就会变得不确定：LDAP 服务器返回顺序不同时，可能验证不同用户。

<a id="openldap-reference-behavior"></a>

#### OpenLDAP 参考行为

**来源**：`servers/slapd/search.c`

OpenLDAP 返回所有匹配条目。协议规范未定义结果顺序语义，客户端应用必须适当处理歧义结果。

<a id="phoenix-implementation-strategy"></a>

#### Phoenix 实现策略

**设计决策**：多个条目匹配时拒绝身份验证。

**实现**（`src/phoenix/server/ldap.py:_search_user()`）：

```python
if len(conn.entries) == 0:
    logger.info("LDAP user search returned no results")
    return None
elif len(conn.entries) > 1:
    # Multiple matches - reject for security (non-deterministic behavior)
    logger.error(
        f"Ambiguous LDAP search: found {len(conn.entries)} matching entries. "
        f"Rejecting authentication for safety. "
        f"Fix: Use more specific user_search_filter or user_search_base to "
        f"ensure unique results."
    )
    return None

return conn.entries[0]  # Exactly one match
```

**依据**：
1. **安全**：防止非确定性身份验证
2. **运维**：尽早暴露过宽搜索过滤器等配置问题
3. **诊断**：记录所有冲突 DN，便于排查

**已考虑的替代方案**：
- **按 DN 长度选择**，更长表示更具体：否决，长度相同时仍不确定
- **允许配置标志**：否决，安全不应可选
- **使用首个结果**：否决，易受结果顺序变化影响

**测试覆盖**：`tests/integration/auth/test_ldap.py::TestLDAPDNValidation::test_duplicate_username_in_different_ous`

---

<a id="2-mock-ldap-server-protocol-compliance"></a>

### 2. 模拟 LDAP 服务器协议合规性

为准确进行集成测试，模拟 LDAP 服务器（`tests/integration/_mock_ldap_server.py`）实现与 OpenLDAP 一致的协议行为。

<a id="dn-validation-error-codes"></a>

#### DN 校验错误码

**OpenLDAP 行为** (`servers/slapd/search.c:113-118`):
```c
rs->sr_err = dnPrettyNormal(...);
if( rs->sr_err != LDAP_SUCCESS ) {
    send_ldap_error( op, rs, LDAP_INVALID_DN_SYNTAX, "invalid DN" );
}
```

DN 格式错误时返回错误码 **34**（`LDAP_INVALID_DN_SYNTAX`）。

**模拟服务器实现**：
```python
def _validate_dn(self, dn: str) -> bool:
    """Validate DN syntax using ldap3's parse_dn."""
    try:
        parse_dn(dn)
        return True
    except LDAPInvalidDnError:
        return False


# In search handler:
if not self._validate_dn(search_base):
    self._send_search_done(message_id, result_code=34, matched_count=0)
```

<a id="empty-dn-handling"></a>

#### 空 DN 处理

**协议要求**：根据 RFC 4511，空 DN 有效，表示根 DSE。

**模拟服务器实现**：
```python
def _validate_dn(self, dn: str) -> bool:
    if not dn:
        return True  # Empty DN is valid
    # ... validate non-empty DN
```

<a id="multiple-result-support"></a>

#### 多结果支持

**实现变更**：按 DN 而非用户名存储用户，以支持不同 OU 中的重复用户名。

```python
# Storage keyed by DN
self._users: dict[str, LDAPUser] = {}  # DN -> user

# Search returns all matching users
def _handle_user_search(...):
    matching_users = [
        user for user in self.ldap_server._users.values()
        if user.username == username
    ]
    for user in matching_users:
        # Send each matching entry
        self.request.sendall(encoder.encode(entry))
```

这样即可测试歧义搜索场景。

---

<a id="3-anonymous-bind-prevention"></a>

### 3. 防止匿名绑定

<a id="openldap-protocol-behavior"></a>

#### OpenLDAP 协议行为

**来源**：`servers/slapd/bind.c:300-334`

```c
/* accept "anonymous" binds */
if ( BER_BVISEMPTY( &op->orb_cred ) || BER_BVISEMPTY( &op->o_req_ndn ) ) {
    rs->sr_err = LDAP_SUCCESS;  // Anonymous bind succeeds by default
}
```

除非通过 `SLAP_DISALLOW_BIND_ANON` 显式禁用，OpenLDAP 会将空凭证接受为匿名绑定。

<a id="security-consideration"></a>

#### 安全考虑

**潜在攻击**：若未在 LDAP 操作前校验凭证：
1. 客户端发送空密码
2. 应用搜索 LDAP，通过服务账户成功
3. 应用尝试使用空密码执行用户绑定
4. LDAP 将其接受为匿名绑定
5. 身份验证错误地成功

<a id="phoenix-implementation"></a>

#### Phoenix 实现

**校验**（`src/phoenix/server/api/routers/auth.py`）：

```python
# /auth/ldap/login endpoint
username = data.get("username")
password = data.get("password")

if not username or not password:
    raise HTTPException(status_code=401, detail="Username and password required")
```

空凭证在任何 LDAP 操作前，已在 API 层被拒绝。

---

<a id="4-configuration-recommendations"></a>

### 4. 配置建议

<a id="search-filter-specificity"></a>

#### 搜索过滤器精确性

配置具体搜索过滤器，以尽量减少歧义结果：

**推荐**：
```bash
PHOENIX_LDAP_USER_SEARCH_FILTER="(uid=%s)"                        # OpenLDAP
PHOENIX_LDAP_USER_SEARCH_FILTER="(sAMAccountName=%s)"            # Active Directory
PHOENIX_LDAP_USER_SEARCH_FILTER="(&(objectClass=person)(uid=%s))" # More specific
```

**避免**：
```bash
PHOENIX_LDAP_USER_SEARCH_FILTER="(objectClass=person)"  # Too broad, returns all users
```

<a id="search-base-scoping"></a>

#### 搜索基准范围

缩小搜索范围，减少歧义：

```bash
PHOENIX_LDAP_USER_SEARCH_BASE_DNS='["ou=employees,dc=example,dc=com"]'  # Specific OU
```

对比：

```bash
PHOENIX_LDAP_USER_SEARCH_BASE_DNS='["dc=example,dc=com"]'  # Entire directory
```

---

<a id="5-optional-enhancements"></a>

### 5. 可选增强

以下增强并非正确运行的必要条件，但可能改善运维特性：

<a id="explicit-search-limits"></a>

#### 显式搜索限制

```python
conn.search(
    search_base=self.config.user_search_base,
    search_filter=user_filter,
    search_scope=SUBTREE,
    size_limit=10,  # Max results
    time_limit=10,  # Timeout (seconds)
    attributes=[...],
)
```

**收益**：配置错误时更快失败，并保护资源。

<a id="enhanced-error-diagnostics"></a>

#### 增强错误诊断

将具体 LDAP 错误码映射为可操作消息：
- 错误 53（`UNWILLING_TO_PERFORM`）："LDAP server may require SASL authentication"
- 错误 12（`UNAVAILABLE_CRITICAL_EXTENSION`）："Required LDAP extension not available"

**收益**：减少管理员排障时间。

---

<a id="6-docker-development--testing-environment"></a>

### 6. Docker 开发与测试环境

Phoenix 提供完整的 Docker Compose 配置，用于 LDAP 开发和测试，超出规范要求。

<a id="quick-start"></a>

#### 快速开始

```bash
./dev.sh up --profile ldap    # Start full LDAP environment + automated tests
docker logs devops-ldap-test  # View test results (14/14 PASSED ✅)
```

<a id="components"></a>

#### 组件

**Docker 服务**（`scripts/docker/devops/overrides/ldap.yml`）：

| 服务 | 镜像 | 用途 | 访问 |
|---------|-------|---------|--------|
| `ldap` | osixia/openldap:1.5.0 | 真实 LDAP 服务器 | ldap://localhost:389 |
| `ldap-admin` | osixia/phpldapadmin | Web UI | http://localhost:6443 |
| `ldap-seed` | osixia/openldap | 自动填充目录 | 运行一次 |
| `ldap-test` | python:3.10-slim | 自动测试运行器 | 启动时运行 |

<a id="enhanced-seed-data"></a>

#### 增强种子数据

**文件**：`scripts/docker/devops/ldap-seed.ldif`，245 行、11 名用户

**规范**：4 名基础用户 → **实现**：11 名全面覆盖用户，增加 175%

| 用户 | 测试边界情况 |
|------|------------------|
| `admin`、`alice`、`bob`、`charlie` | 正常流程，ADMIN、MEMBER、VIEWER 角色 |
| **`nogroups`** | 通配符“*”回退 → VIEWER |
| **`multigroup`** | 多组 → 角色优先级，首次匹配优先 |
| **`nodisplay`** | 缺少 displayName → 回退至邮箱前缀 |
| **`special(user)`** | LDAP 注入防护，特殊字符 |
| **`josé`** | UTF-8/Unicode 支持 |
| **`duplicate`**（IT 和 HR） | **拒绝歧义搜索，安全测试** |

<a id="automated-test-suite"></a>

#### 自动测试套件

**文件**：`scripts/docker/devops/scripts/test_ldap_integration.py`，438 行

**14 项测试用例**覆盖所有成功标准：

| 测试 | 类别 |
|-------|----------|
| 1—3 | 正常流程，admin/member/viewer 登录 |
| 4—5 | 错误处理，无效密码、不存在的用户 |
| 6—8 | 防止匿名绑定，空凭证 |
| **9** | **安全：拒绝重复用户名** |
| 10—14 | 边界情况，无组、多组、特殊字符、Unicode、缺少属性 |

**结果**：✅ **14/14 通过**，真实 OpenLDAP 与 Phoenix 集成

<a id="benefits-vs-specification"></a>

#### 相比规范的收益

| 方面 | 规范 | 已实现 | 差异 |
|--------|-----------|-------------|-------|
| 测试用户 | 4 名基础用户 | 11 名全面覆盖用户 | +175% |
| 边界情况 | 仅基础 | 规范全部场景加安全场景 | 增强 |
| LDAP 服务器 | 仅模拟 | 模拟及真实 OpenLDAP | 两者兼有 |
| 测试 | 手动 | 自动化，14 项测试 | 无需干预 |
| 歧义结果 | 未覆盖 | 已测试，测试 9 | 安全修复 |
| 个人身份信息保护 | 未覆盖 | 已验证 | 合规 |

---

<a id="7-starttls-implementation--security"></a>

### 7. STARTTLS 实现与安全

LDAP 支持两种 TLS 连接模式：LDAPS 从端口 636 连接开始即使用 TLS；STARTTLS 在端口 389 上将明文连接升级为 TLS。本节记录 Phoenix 实现要求和 STARTTLS 的关键安全考虑。

<a id="protocol-overview"></a>

#### 协议概览

**LDAPS**（RFC 4513 第 3 节）：
- 交换任何 LDAP 数据前先建立 TLS
- 默认端口 636
- 类似 HTTPS

**STARTTLS**（RFC 4511 第 4.14.1 节）：
- 在端口 389 上建立明文连接
- 客户端发送扩展请求，OID 为 1.3.6.1.4.1.1466.20037，升级至 TLS
- 所有后续数据，包括绑定凭证，均经 TLS 传输
- 类似 SMTP STARTTLS

<a id="security-requirement"></a>

#### 安全要求

**关键要求**：STARTTLS 模式必须在传输任何身份验证凭证前完成 TLS 升级。升级顺序不正确时，即使配置“启用”了 TLS，仍会明文传输密码。

<a id="ldap3-library-behavior"></a>

#### ldap3 库行为

`ldap3` Python 库不会根据 TLS 配置自动推断 STARTTLS，必须显式安排执行顺序：

**错误**，明文传输密码：
```python
conn = Connection(server, user=dn, password=pwd, auto_bind=True)
# auto_bind=True means AUTO_BIND_NO_TLS - bind happens immediately
# TLS upgrade never occurs despite tls parameter on Server object
```

**正确**，通过 STARTTLS 加密密码：
```python
# Method 1: Use AUTO_BIND_TLS_BEFORE_BIND constant
from ldap3 import AUTO_BIND_TLS_BEFORE_BIND

conn = Connection(server, user=dn, password=pwd, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
# Calls start_tls() before sending bind credentials

# Method 2: Manual sequencing
conn = Connection(server, user=dn, password=pwd, auto_bind=False)
conn.open()
conn.start_tls()  # MUST occur before bind()
conn.bind()
```

**参考**：`ldap3/core/connection.py::_do_auto_bind()` 显式检查 `AUTO_BIND_TLS_BEFORE_BIND` 模式，以调用 `start_tls()`。

<a id="phoenix-implementation-1"></a>

#### Phoenix 实现

**文件**：`src/phoenix/server/ldap.py`

**服务账户绑定** (`_establish_connection()`):
```python
def _establish_connection(self, server: Server) -> Connection:
    # Determine auto_bind mode based on TLS configuration
    if self.config.tls_mode == "starttls":
        auto_bind_mode = AUTO_BIND_TLS_BEFORE_BIND
    else:
        auto_bind_mode = True  # AUTO_BIND_NO_TLS for LDAPS or plaintext

    if self.config.bind_dn and self.config.bind_password:
        return Connection(
            server,
            user=self.config.bind_dn,
            password=self.config.bind_password,
            auto_bind=auto_bind_mode,
            raise_exceptions=True,
        )

    # Anonymous bind case
    conn = Connection(server, auto_bind=False, raise_exceptions=True)
    conn.open()
    if self.config.tls_mode == "starttls":
        conn.start_tls()
    return conn
```

**用户密码验证** (`_verify_user_password()`):
```python
def _verify_user_password(self, server: Server, user_dn: str, password: str) -> bool:
    user_conn = Connection(
        server, user=user_dn, password=password, auto_bind=False, raise_exceptions=True
    )
    try:
        user_conn.open()
        # CRITICAL: Upgrade to TLS BEFORE sending password
        if self.config.tls_mode == "starttls":
            user_conn.start_tls()
        user_conn.bind()
        return user_conn.bound
    finally:
        if user_conn.bound:
            user_conn.unbind()
```

**实现要点**：
1. 服务账户绑定使用 `AUTO_BIND_TLS_BEFORE_BIND` 自动升级 TLS
2. 用户密码验证在 `bind()` 前显式调用 `start_tls()`
3. TLS 模式检查（`tls_mode == "starttls"`）确保 LDAPS 不受影响
4. 服务账户和用户绑定两条身份验证路径均实现 TLS 升级

<a id="validation-strategy"></a>

#### 验证策略

**Docker 测试环境**：`scripts/docker/devops/overrides/ldap-test.yml`

带对抗验证的自动安全测试基础设施：
- **OpenLDAP 服务器**：端口 389（STARTTLS）和 636（LDAPS），使用自签名证书
- **中间人代理**：端口 3389，对抗性凭证提取代理
- **Phoenix STARTTLS**：端口 6007，通过中间人代理验证
- **Phoenix LDAPS**：端口 6008，直连端口 636
- **Grafana**：端口 3000，比较基准，经中间人代理
- **测试运行器**：启动时执行完整测试套件

**测试脚本**：`scripts/docker/devops/scripts/test_ldap_tls.py`

三阶段自动安全验证：

**阶段 1 — 基线 LDAP 连通性**：
1. 直接明文 LDAP，端口 389，无 TLS
2. 使用 `AUTO_BIND_TLS_BEFORE_BIND` 的直接 STARTTLS，正确实现
3. 直接 LDAPS，端口 636，从开始即使用 TLS

**阶段 2 — 应用安全测试**：
4. Phoenix STARTTLS 经中间人代理身份验证
5. Phoenix LDAPS 身份验证，直接连接
6. Grafana STARTTLS 经中间人代理身份验证，用于比较

**阶段 3 — 对抗分析**：
7. 解析中间人代理日志，检查提取的凭证
8. 使用 LDAP 服务器验证提取凭证
9. 生成安全判定

**中间人代理**：`scripts/docker/devops/scripts/ldap_mitm_proxy.py`

作为网络攻击者验证 TLS 安全：
- 拦截应用与服务器之间的 LDAP 流量
- 解析 LDAP ASN.1/BER 协议结构
- 尝试从简单绑定请求提取 DN 和密码
- 检测 StartTLS 请求和 TLS 握手
- 通过反向 DNS 识别连接的应用
- 输出结构化 JSON 日志供自动解析

**安全模型**：
- 若代理成功提取有效凭证 → **TLS 漏洞**，明文传输
- 若代理无法提取凭证 → **TLS 正常工作**，仅有加密数据

此方法模拟真实网络攻击者尝试窃取凭证，为 TLS 安全提供明确证据。协议级解析确保检测适用于任意密码，而非仅已知测试值。

<a id="validation-results"></a>

#### 验证结果

对抗性中间人代理测试确认：

**Phoenix**（修复后）：
- 检测到 StartTLS 请求：是
- 检测到 TLS 握手：是
- 攻击者提取的凭证：0
- **判定**：✅ 安全，网络攻击者无法窃取凭证

**Grafana v11.4**（用于对比测试）：
- 检测到 StartTLS 请求：否
- 检测到 TLS 握手：否
- 攻击者提取的凭证：2，服务账户和用户密码
- **判定**：🚨 存在漏洞，尽管配置中已设置 `start_tls = true`

**发现**：测试表明，`ldap3`（Python）和 `go-ldap/ldap`（Go）均要求显式关注 STARTTLS 执行顺序：

- **`ldap3`**：要求 `AUTO_BIND_TLS_BEFORE_BIND` 或手动调用 `start_tls()`
- **`go-ldap/ldap`**：要求在 `Bind()` 前显式调用 `StartTLS()`
- **共同问题**：仅有配置标志不足，未实现正确顺序时，两种库均明文传输凭证

Grafana v11.4 即使配置 `start_tls = true`，仍存在相同漏洞。对抗性中间人代理从 Grafana LDAP 流量中成功提取了服务账户和用户凭证。

**根因**：LDAP 库提供 TLS 升级机制，但不自动强制正确顺序。应用代码必须明确确保在传输凭证前完成 TLS 升级。

<a id="configuration-reference"></a>

#### 配置参考

**STARTTLS 模式**，端口 389，升级至 TLS：
```bash
PHOENIX_LDAP_TLS_MODE=starttls
PHOENIX_LDAP_PORT=389
```

**LDAPS 模式**，端口 636，从开始即使用 TLS：
```bash
PHOENIX_LDAP_TLS_MODE=ldaps
PHOENIX_LDAP_PORT=636
```

**无 TLS**，明文，仅用于测试：
```bash
PHOENIX_LDAP_TLS_MODE=none
PHOENIX_LDAP_PORT=389
```

<a id="advanced-tls-configuration-examples"></a>

### 高级 TLS 配置示例

**私有 CA 证书**，用于内部 LDAP 服务器：
```bash
PHOENIX_LDAP_TLS_MODE=ldaps
PHOENIX_LDAP_TLS_CA_CERT_FILE=/etc/ssl/certs/internal-ca.pem
```

**双向 TLS（客户端证书）**，用于高安全环境：
```bash
PHOENIX_LDAP_TLS_MODE=ldaps
PHOENIX_LDAP_TLS_CLIENT_CERT_FILE=/etc/ssl/certs/phoenix-client.crt
PHOENIX_LDAP_TLS_CLIENT_KEY_FILE=/etc/ssl/private/phoenix-client.key
```

**组合企业配置**：
```bash
# Server connection
PHOENIX_LDAP_HOST=ldaps.corp.example.com
PHOENIX_LDAP_PORT=636
PHOENIX_LDAP_TLS_MODE=ldaps

# TLS security (private CA + mutual TLS)
# Note: Python defaults to TLS 1.2+ automatically via ssl.create_default_context()
PHOENIX_LDAP_TLS_CA_CERT_FILE=/etc/ssl/certs/corp-ca-bundle.pem
PHOENIX_LDAP_TLS_CLIENT_CERT_FILE=/etc/ssl/certs/phoenix-ldap.crt
PHOENIX_LDAP_TLS_CLIENT_KEY_FILE=/etc/ssl/private/phoenix-ldap.key

# Authentication (rest of config...)
PHOENIX_LDAP_BIND_DN=cn=phoenix-svc,ou=service-accounts,dc=corp,dc=example,dc=com
PHOENIX_LDAP_BIND_PASSWORD=${LDAP_SERVICE_PASSWORD}
# ...
```

<a id="adversarial-testing-methodology"></a>

#### 对抗测试方法

**方法**：通过协议解析主动提取凭证。

中间人代理（`ldap_mitm_proxy.py`）实现以下攻击：

1. **拦截**：位于应用与 LDAP 服务器之间
2. **解析**：解码绑定请求中的 LDAP ASN.1/BER 结构
3. **提取**：尝试读取简单身份验证（RFC 4513 §5.1.1）中的 DN 和密码
4. **验证**：使用提取凭证向 LDAP 服务器身份验证

**协议解析**：
```
BindRequest ::= [APPLICATION 0] SEQUENCE {
    version        INTEGER (1..127),
    name           LDAPDN,              -- Extract this
    authentication CHOICE {
        simple     [0] OCTET STRING,   -- Extract this (password)
        ...
    }
}
```

**安全验证**：
- 加密数据 → 解析失败 → 提取返回 `None` → ✅ 安全
- 明文数据 → 解析成功 → 提取凭证通过验证 → 🚨 存在漏洞

此方法提供明确安全验证，无需仅依赖功能测试。若凭证可被提取并通过验证，就说明 TLS 确实失效。

**结构化日志**：

所有安全事件均以 JSON 输出，供自动分析：
```json
{
  "timestamp": 1764371725.425,
  "event": "credentials_stolen",
  "connection_id": 3,
  "application": "grafana-ldap",
  "bind_dn": "cn=readonly,dc=example,dc=com",
  "password": "readonly_password",
  "direction": "client→server"
}
```

事件：`connection_established`、`starttls_requested`、`tls_handshake_detected`、`credentials_stolen`、`connection_closed`

<a id="testing-recommendation"></a>

#### 测试建议

验证生产部署时：
1. **首选**：LDAPS，端口 636，隐式 TLS，无需安排升级顺序
2. **必须使用 STARTTLS 时**：通过对抗性中间人代理或抓包验证凭证已加密
3. **避免**：在生产环境使用无 TLS 的明文 LDAP

**自动测试**：
```bash
# Start test environment (includes MITM proxy)
cd scripts/docker/devops
COMPOSE_PROFILES=ldap-test docker compose \
    -f docker-compose.yml \
    -f overrides/ldap-test.yml \
    up -d --build

# View test results (7 tests: baseline + application + adversarial)
docker logs devops-ldap-test

# View MITM proxy analysis (structured JSON logs)
docker logs devops-ldap-mitm-proxy
docker logs devops-ldap-mitm-proxy 2>&1 | grep "^{" | jq
```

**手动验证**：
```bash
# Test Phoenix STARTTLS
curl -X POST http://localhost:6007/auth/ldap/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"password123"}'

# Check if MITM proxy extracted credentials
docker logs devops-ldap-mitm-proxy 2>&1 | grep "CREDENTIALS STOLEN"
# Expected: No output (Phoenix is secure)
```

测试基础设施完整文档参见：`scripts/docker/devops/LDAP-TLS-TESTING.md`

预期：HTTP 204，`set-cookie` 请求头包含访问和刷新 token。

---

<a id="8-dn-canonicalization--rfc-4514-compliance"></a>

### 8. DN 规范化与 RFC 4514 合规性

<a id="problem-statement"></a>

#### 问题说明

RFC 4514 第 2.4 节规定 LDAP 专有名称不区分大小写，语义等价的 DN 可能有不同字符串表示。LDAP 服务器，尤其是多 DC 环境的 Active Directory，可能在不同身份验证中为同一逻辑 DN 返回不同格式：

**大小写差异**：
```
Login 1 (DC1): uid=alice,ou=users,dc=example,dc=com
Login 2 (DC2): uid=Alice,ou=Users,dc=Example,dc=Com
```

**空白差异**：
```
Login 1: cn=John Smith,ou=users,dc=example,dc=com
Login 2: cn = John Smith , ou = users , dc = example , dc = com
```

**多值 RDN 顺序**：
```
Login 1: cn=John Smith+email=john@corp.com,ou=users,dc=example,dc=com
Login 2: email=john@corp.com+cn=John Smith,ou=users,dc=example,dc=com
```

**安全影响**：缺少正确规范化时，用户可能遇到：
- 账户无法登录，DN 格式不匹配导致找不到已有用户
- 创建重复账户，若 `allow_sign_up=true`
- 非确定性身份验证行为

<a id="phoenix-implementation-2"></a>

#### Phoenix 实现

**符合 RFC 4514 的规范化**：

Phoenix 使用 `ldap3.utils.dn.parse_dn()` 实现完整 DN 规范化，确保语义等价 DN 映射至同一数据库记录。

**文件**：`src/phoenix/server/ldap.py`

```python
def canonicalize_dn(dn: str) -> str:
    """Canonicalize a Distinguished Name per RFC 4514.
    
    Handles:
    - Case normalization (attribute types and values lowercased)
    - Whitespace normalization (stripped around = and ,)
    - Multi-valued RDN ordering (sorted alphabetically)
    - Escaped character preservation (maintains \\, \\+ etc.)
    - Hex encoding normalization (decoded to canonical form)
    """
    components = parse_dn(dn, escape=True, strip=True)
    
    # Build canonical DN with sorted multi-valued RDNs
    canonical_parts = []
    current_rdn_components = []
    
    for attr_type, attr_value, separator in components:
        normalized_component = (attr_type.lower(), attr_value.lower())
        current_rdn_components.append(normalized_component)
        
        if separator == "," or separator == "":
            # Sort multi-valued RDN components alphabetically
            current_rdn_components.sort(key=lambda x: x[0])
            rdn_str = "+".join(f"{attr}={value}" for attr, value in current_rdn_components)
            canonical_parts.append(rdn_str)
            current_rdn_components = []
    
    return ",".join(canonical_parts)
```

**DN 使用说明**：

Phoenix 不再使用 DN 匹配用户身份，因为企业环境 DN 变化过于频繁。改为：
- **简单模式**：使用邮箱标识符
- **企业模式**：通过 `PHOENIX_LDAP_ATTR_UNIQUE_ID` 使用不可变唯一 ID，objectGUID/entryUUID

详情参见[用户识别策略](./user-identification-strategy.md)。

DN 规范化仍用于：
- 审计日志，保持日志中的 DN 格式一致
- 角色映射中的组 DN 匹配
- 调试输出一致性

**关键设计点**：
- **解析**：使用 `ldap3.utils.dn.parse_dn()`，符合 RFC
- **规范化**：属性类型和值转为小写
- **空白**：去除 `=` 和 `,` 分隔符周围空格
- **多值 RDN**：按字母排序组成部分，保证确定性输出
- **转义字符**：保留特殊字符转义，例如 `\,`、`\+`、`\\`
- **回退**：无效 DN 回退至简单小写，实现平滑降级
- **幂等性**：规范化已规范的 DN 产生相同输出

<a id="canonicalization-examples"></a>

#### 规范化示例

| 输入 DN | 规范 DN | 处理问题 |
|----------|-------------|---------------|
| `CN=John,OU=Users,DC=Example,DC=com` | `cn=john,ou=users,dc=example,dc=com` | 大小写规范化 |
| `cn = John , ou = Users , dc = Example , dc = com` | `cn=john,ou=users,dc=example,dc=com` | 去除空白 |
| `email=john@corp.com+cn=John Smith,ou=users,dc=example,dc=com` | `cn=john smith+email=john@corp.com,ou=users,dc=example,dc=com` | 多值 RDN 排序 |
| `cn=Smith\\, John,ou=Users,dc=Example,dc=com` | `cn=smith\\, john,ou=users,dc=example,dc=com` | 保留转义字符 |

<a id="mock-server-implementation"></a>

#### 模拟服务器实现

**文件**：`tests/integration/_mock_ldap_server.py`

模拟 LDAP 服务器使用相同规范化函数：

```python
from phoenix.server.ldap import canonicalize_dn

def add_user(self, username: str, ..., custom_dn: Optional[str] = None) -> str:
    user = LDAPUser(...)
    # Store by canonical DN per RFC 4514
    dn_canonical = canonicalize_dn(user.dn)
    self._users[dn_canonical] = user

def matches_credentials(self, dn: str, password: str) -> bool:
    """Check credentials using RFC 4514 canonical comparison."""
    return canonicalize_dn(self.dn) == canonicalize_dn(dn) and self.password == password
```

**行为**：相同逻辑 DN 以不同格式添加时，会替换原有条目，因为规范键相同。这模拟真实 LDAP 服务器行为。

<a id="test-coverage"></a>

#### 测试覆盖

**单元测试**：`tests/unit/server/test_ldap.py::TestDNCanonicalization`，16 项

验证：
- 属性类型和值的大小写规范化
- 空白规范化，紧凑、带空格和混合形式
- 多值 RDN 顺序，2 个及 3 个以上组成部分
- 保留转义字符，逗号、等号和反斜杠
- Unicode 字符转小写，例如 José → josé
- 边界情况，空 DN、单 RDN、无效 DN 回退
- 真实 Active Directory 和 POSIX LDAP 格式
- 幂等性，规范化已规范 DN
- 防止重复场景

**集成测试**：`tests/integration/auth/test_ldap.py::TestLDAPPosixGroupSearch::test_dn_case_insensitivity`

验证：
1. 用户以小写 DN 登录 → Phoenix 创建账户
2. LDAP 服务器为相同用户返回混合大小写 DN
3. 用户再次登录 → Phoenix 找到已有账户，不重复创建
4. 即使 DN 格式不同，各次登录返回相同用户 ID

**结果**：✅ 16 项单元测试全部通过，43/43 项集成测试通过

<a id="alternative-approaches-considered"></a>

#### 已考虑的替代方案

| 方案 | 决策 | 原因 |
|----------|----------|-----------|
| 简单 `.lower()` | ❌ 否决 | 无法处理空白差异和多值 RDN 顺序 |
| 原样存储 DN，通过 `func.lower()` 比较 | ❌ 否决 | 仅处理大小写，无法处理空白或 RDN 顺序 |
| 完整 RFC 4514 规范化 | ✅ **选用** | 处理全部边界情况，符合 RFC，无需迁移 |
| 使用 ldap3 的 parse_dn() 进行语义比较 | ❌ 否决 | 成本高、不必要，小写已足够 |
| DN 不匹配时回退邮箱 | ❌ 否决 | 安全风险，LDAP 邮箱不唯一 |

<a id="comparison-to-grafana"></a>

#### 与 Grafana 对比

Grafana 在 `user_auth.auth_id` 中原样保存 DN，但通过 Go 的 `strings.EqualFold()` 不区分大小写查找。Phoenix 通过小写规范化实现相同语义。

**两种实现均符合 RFC 4514 的大小写不敏感要求。**

---

<a id="9-tls-port-defaulting--ldaps-configuration"></a>

### 9. 默认 TLS 端口与 LDAPS 配置

<a id="problem-statement-1"></a>

#### 问题说明

配置文档和文档字符串承诺按模式设置默认端口：
- **STARTTLS**：默认端口 389，明文后升级
- **LDAPS**：默认端口 636，从开始即使用 TLS

但 `LDAPConfig.from_env()` 实现始终默认端口 389，不考虑 `PHOENIX_LDAP_TLS_MODE`。因此，仅设置 `PHOENIX_LDAP_TLS_MODE=ldaps`、未显式覆盖 `PHOENIX_LDAP_PORT` 的部署会出现 **LDAPS 静默失败**。

**失败场景**：
```bash
# User configuration
PHOENIX_LDAP_TLS_MODE=ldaps
# (PHOENIX_LDAP_PORT not set)

# Actual behavior: Phoenix tries TLS handshake on port 389
# → Connection refused or TLS handshake failure
```

<a id="root-cause-analysis"></a>

#### 根因分析

**文件**：`src/phoenix/config.py`

**修复前**，第 1602—1604 行：
```python
return cls(
    host=host,
    port=int(getenv(ENV_PHOENIX_LDAP_PORT, "389")),  # ❌ Always 389
    tls_mode=tls_mode,
```

**问题**：硬编码 `"389"` 默认值，没有检查 `tls_mode` 的逻辑。

<a id="phoenix-implementation-3"></a>

#### Phoenix 实现

**修复后**，第 1596—1610 行：
```python
# Determine default port based on TLS mode (if not explicitly set)
# STARTTLS: port 389 (plaintext, then upgrade)
# LDAPS: port 636 (TLS from start)
default_port = "636" if tls_mode == "ldaps" else "389"
port = int(getenv(ENV_PHOENIX_LDAP_PORT, default_port))

return cls(
    host=host,
    port=port,
    tls_mode=tls_mode,
```

**关键设计点**：
- **模式感知默认值**：端口选择遵循 `tls_mode`
- **显式覆盖**：设置 `PHOENIX_LDAP_PORT` 时仍优先采用
- **符合 IANA**：使用标准 LDAP 端口 389、LDAPS 端口 636（RFC 4516）
- **无不兼容变更**：显式指定 `PHOENIX_LDAP_PORT` 的现有配置不受影响

<a id="test-coverage-1"></a>

#### 测试覆盖

**文件**：`tests/unit/test_config.py`

**测试 1**： `TestLDAPConfigFromEnv::test_valid_inputs[starttls_defaults_to_port_389]`
```python
{
    "PHOENIX_LDAP_TLS_MODE": "starttls",
    # PHOENIX_LDAP_PORT not set
}
# Expected: port=389
```

**测试 2**： `TestLDAPConfigFromEnv::test_valid_inputs[ldaps_defaults_to_port_636]`
```python
{
    "PHOENIX_LDAP_TLS_MODE": "ldaps",
    # PHOENIX_LDAP_PORT not set
}
# Expected: port=636
```

**结果**：✅ 两项测试均通过，27/27 项 LDAP 配置测试通过

<a id="docker-validation"></a>

#### Docker 验证

**文件**：
- `scripts/docker/devops/overrides/ldap.yml`
- `scripts/docker/devops/overrides/ldap-test.yml`

所有 Docker LDAP 配置均**省略** `PHOENIX_LDAP_PORT`，在真实场景验证默认端口：

| 配置 | TLS 模式 | 是否省略端口？ | 预期默认值 | 验证方式 |
|--------------|----------|---------------|------------------|--------------|
| `ldap.yml` | 无（`tls_mode=none`） | ✅ 是 | 389 | LDAP 集成测试 |
| `ldap-test.yml`（`phoenix-starttls`） | STARTTLS | ✅ 是 | 389 | TLS 测试脚本 |
| `ldap-test.yml`（`phoenix`） | LDAPS | ✅ 是 | 636 | TLS 测试脚本 |

**验证策略**：
- Phoenix 容器不显式设置 `PHOENIX_LDAP_PORT` 即可成功启动
- LDAP 身份验证在无 TLS、STARTTLS 和 LDAPS 三种模式均可工作
- 确认默认端口符合 IANA 标准（RFC 4516）

**结果**：✅ Docker 测试确认所有 TLS 模式的默认端口正确

<a id="impact-analysis"></a>

#### 影响分析

**修复前**：
| 配置 | 预期端口 | 实际端口 | 结果 |
|--------|--------------|-------------|--------|
| `tls_mode=starttls`，未指定端口 | 389 | 389 | ✅ 可用 |
| `tls_mode=ldaps`，未指定端口 | 636 | 389 ❌ | 🚨 TLS 握手失败 |
| `tls_mode=ldaps`、`port=636` | 636 | 636 | ✅ 可用，显式指定 |

**修复后**：
| 配置 | 预期端口 | 实际端口 | 结果 |
|--------|--------------|-------------|--------|
| `tls_mode=starttls`，未指定端口 | 389 | 389 | ✅ 可用 |
| `tls_mode=ldaps`，未指定端口 | 636 | 636 | ✅ 可用 |
| `tls_mode=ldaps`、`port=636` | 636 | 636 | ✅ 可用，显式指定 |

<a id="comparison-to-grafana-1"></a>

#### 与 Grafana 对比

Grafana 基于 TOML 的 LDAP 配置要求显式指定 `port`：
```toml
[servers]
host = "ldap.example.com"
port = 636  # Must be explicit
use_ssl = true
```

Phoenix 基于环境变量的配置现提供**智能默认值**，改善用户体验，同时仍允许显式覆盖非标准端口。

<a id="migration-notes"></a>

#### 迁移说明

**无需迁移**。现有部署分为两类：

1. **STARTTLS 用户**，未设置 `PHOENIX_LDAP_PORT`：
   - 之前：port=389 ✅
   - 之后：port=389 ✅
   - **影响**：无

2. **LDAPS 用户**：
   - **显式指定端口**（`PHOENIX_LDAP_PORT=636`）：
     - 之前：port=636 ✅
     - 之后：port=636 ✅
     - **影响**：无
   - **未显式指定端口**，修复前不可用：
     - 之前：port=389 🚨，不可用
     - 之后：port=636 ✅，已修复
     - **影响**：功能现已正常工作

---

<a id="10-references"></a>

### 10. 参考资料

**LDAP 协议**：
- RFC 4511 — 轻量目录访问协议（LDAP）：协议
- RFC 4514 — LDAP：专有名称的字符串表示

**OpenLDAP 源码**：
- `servers/slapd/search.c` — 搜索操作处理、DN 校验
- `servers/slapd/bind.c` — 绑定操作处理、匿名绑定逻辑
- `include/ldap.h` — 错误码定义

**ldap3 库**：
- `ldap3/utils/dn.py` — DN 解析和校验实现

**Phoenix 实现**：
- `src/phoenix/server/ldap.py` — LDAP 身份验证逻辑
- `tests/integration/_mock_ldap_server.py` — 测试用模拟 LDAP 服务器
- `tests/integration/auth/test_ldap.py` — 集成测试套件

