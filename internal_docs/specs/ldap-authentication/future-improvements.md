<a id="future-improvements-post-mvp"></a>

# 未来改进（MVP 之后）

本文列出将 LDAP 实现从生产可用（A-）提升至企业级（A+）的潜在增强。它们**不阻碍**当前发布，而是后续迭代的机会。

---

<a id="priority-matrix"></a>

## 优先级矩阵

| 功能 | 影响 | 复杂度 | 目标阶段 |
|---------|--------|------------|--------------|
| [密码策略处理](#1-password-policy-handling) | 高 | 中 | **阶段 2** |
| [重试逻辑](#2-retry-logic-for-transient-failures) | 中 | 低 | **阶段 2** |
| [指标与可观测性](#3-metricsobservability) | 中 | 低 | **阶段 2** |
| [嵌套组解析](#4-nested-group-resolution-for-active-directory) | 中 | 高 | 阶段 3 |
| [连接健康检查](#5-connection-health-checks) | 低 | 中 | 阶段 3 |
| [组搜索分页](#6-group-search-pagination) | 低 | 低 | 按需 |

**阶段 2 建议**：在下一次 LDAP 发布中合并第 1—3 项，以适度工作量显著改进用户体验和运维。

---

<a id="1-password-policy-handling"></a>

## 1. 密码策略处理

**影响**：高 | **复杂度**：中 | **目标**：阶段 2

<a id="current-behavior"></a>

### 当前行为

所有绑定失败均返回通用错误“Invalid credentials”。

<a id="problem"></a>

### 问题

Active Directory 和 OpenLDAP 对密码相关问题返回特定错误码，可用于改善用户体验：

| AD 错误码 | 含义 | 当前体验 | 理想体验 |
|---------------|---------|------------|----------|
| `data 532` | 密码已过期 | "Invalid credentials" | "Password expired, contact admin" |
| `data 533` | 账户已禁用 | "Invalid credentials" | "Account disabled" |
| `data 701` | 账户已过期 | "Invalid credentials" | "Account expired" |
| `data 773` | 必须修改密码 | "Invalid credentials" | "Password change required" |
| `data 775` | 账户已锁定 | "Invalid credentials" | "Account locked, try later" |

<a id="implementation-sketch"></a>

### 实现草案

```python
from enum import Enum


class LDAPAuthResult(Enum):
    """LDAP authentication result with account status details."""

    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    PASSWORD_EXPIRED = "password_expired"
    ACCOUNT_DISABLED = "account_disabled"
    ACCOUNT_LOCKED = "account_locked"
    MUST_CHANGE_PASSWORD = "must_change_password"


def _verify_user_password(self, server, user_dn, password) -> LDAPAuthResult:
    """Verify password and detect account status issues.

    Parses Active Directory extended error information from bind failures
    to provide actionable feedback to users.

    AD Error Format:
        "80090308: LdapErr: DSID-0C09044E, comment: AcceptSecurityContext error,
         data XXX, v23f0"

        Where XXX is the sub-status code (532, 533, 701, 773, 775, etc.)
    """
    try:
        # ... existing bind logic ...
        return LDAPAuthResult.SUCCESS
    except LDAPInvalidCredentialsResult as e:
        error_msg = str(e)

        # Parse AD sub-status codes
        if "data 532" in error_msg:
            return LDAPAuthResult.PASSWORD_EXPIRED
        elif "data 533" in error_msg:
            return LDAPAuthResult.ACCOUNT_DISABLED
        elif "data 701" in error_msg:
            # Account expired (different from password expired)
            return LDAPAuthResult.ACCOUNT_DISABLED
        elif "data 773" in error_msg:
            return LDAPAuthResult.MUST_CHANGE_PASSWORD
        elif "data 775" in error_msg:
            return LDAPAuthResult.ACCOUNT_LOCKED

        return LDAPAuthResult.INVALID_CREDENTIALS
```

<a id="api-response-updates"></a>

### API 响应更新

```python
# In /auth/ldap/login endpoint
match auth_result:
    case LDAPAuthResult.SUCCESS:
        return create_tokens(user)
    case LDAPAuthResult.PASSWORD_EXPIRED:
        raise HTTPException(401, detail="Password has expired. Please contact your administrator.")
    case LDAPAuthResult.ACCOUNT_LOCKED:
        raise HTTPException(401, detail="Account is locked. Please try again later.")
    case LDAPAuthResult.MUST_CHANGE_PASSWORD:
        raise HTTPException(
            401, detail="Password change required. Please contact your administrator."
        )
    case _:
        raise HTTPException(401, detail="Invalid username and/or password")
```

<a id="security-considerations"></a>

### 安全考虑

- **用户名枚举风险**：详细错误会确认用户存在。考虑仅在成功查找用户后显示详细错误，因为查找已确认其存在。
- **信息披露**：错误消息应足够通用，不帮助攻击者，同时也应足够具体，帮助合法用户。

<a id="references"></a>

### 参考资料

- [MS-ADTS §3.1.1.3.4.2](https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/) — AD LDAP 错误码
- [OpenLDAP ppolicy 叠加层](https://www.openldap.org/doc/admin24/overlays.html#Password%20Policies) — LDAP 密码策略控制

---

<a id="2-retry-logic-for-transient-failures"></a>

## 2. 瞬态失败重试逻辑

**影响**：中 | **复杂度**：低 | **目标**：阶段 2

<a id="current-behavior-1"></a>

### 当前行为

请求途中网络短暂抖动会使该服务器上的整个身份验证尝试失败，然后转至下一台服务器。

<a id="problem-1"></a>

### 问题

瞬态网络问题，例如短暂 DNS 异常或丢包，会导致不必要的失败并降低用户体验。

<a id="implementation-sketch-1"></a>

### 实现草案

```python
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception_type,
    wait_fixed,
    before_sleep_log,
)
from ldap3.core.exceptions import LDAPSocketOpenError, LDAPSocketReceiveError

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(2),  # Original attempt + 1 retry
    wait=wait_fixed(0.5),  # 500ms between attempts
    retry=retry_if_exception_type(
        (
            LDAPSocketOpenError,  # Connection refused, timeout
            LDAPSocketReceiveError,  # Connection reset mid-operation
        )
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _try_authenticate_on_server(
    self, server: Server, username: str, password: str
) -> LDAPUserInfo | None:
    """Single server auth attempt with retry for transient network errors.

    Retry Policy:
        - Max 1 retry (2 total attempts)
        - 500ms delay between attempts
        - Only retries on socket-level errors (network issues)

    Does NOT retry on:
        - LDAPInvalidCredentialsResult (wrong password)
        - LDAPNoSuchObjectResult (user not found)
        - Other LDAP protocol errors (server-side issues)
    """
    with self._establish_connection(server) as conn:
        # ... existing authentication logic ...
        pass
```

<a id="metrics-integration"></a>

### 指标集成

```python
# Track retry frequency for monitoring
ldap_retry_total = Counter(
    "phoenix_ldap_retry_total", "LDAP authentication retry attempts", ["server", "error_type"]
)


# In retry callback
def on_retry(retry_state):
    ldap_retry_total.labels(
        server=retry_state.args[1].host,  # server argument
        error_type=type(retry_state.outcome.exception()).__name__,
    ).inc()
```

<a id="configuration-option-optional"></a>

### 配置选项（可选）

```bash
# Environment variable to disable retries if needed
PHOENIX_LDAP_RETRY_ENABLED=true  # default
PHOENIX_LDAP_RETRY_MAX_ATTEMPTS=2
PHOENIX_LDAP_RETRY_DELAY_MS=500
```

---

<a id="3-metricsobservability"></a>

## 3. 指标与可观测性

**影响**：中 | **复杂度**：低 | **目标**：阶段 2

<a id="current-behavior-2"></a>

### 当前行为

无法了解 LDAP 身份验证性能或失败模式。

<a id="problem-2"></a>

### 问题

运维团队无法：
- 跟踪 LDAP 身份验证延迟趋势
- 主动识别故障服务器
- 不深入日志便调试身份验证问题
- 为 LDAP 性能下降配置告警

<a id="implementation-sketch-2"></a>

### 实现草案

```python
from prometheus_client import Counter, Histogram, Gauge

# === Counters ===

ldap_auth_total = Counter(
    "phoenix_ldap_auth_total", "Total LDAP authentication attempts", ["result", "server"]
)
# Labels:
#   result: success, invalid_credentials, user_not_found, server_error, timeout, all_failed
#   server: hostname or "all" for aggregate failures

ldap_bind_total = Counter(
    "phoenix_ldap_bind_total",
    "Total LDAP bind operations (service account + user)",
    ["type", "server", "result"],
)
# Labels:
#   type: service_account, user_verification, anonymous
#   result: success, failure

# === Histograms ===

ldap_auth_duration_seconds = Histogram(
    "phoenix_ldap_auth_duration_seconds",
    "LDAP authentication end-to-end latency",
    ["server"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

ldap_operation_duration_seconds = Histogram(
    "phoenix_ldap_operation_duration_seconds",
    "Individual LDAP operation latency",
    ["operation", "server"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)
# Labels:
#   operation: connect, bind, search_user, search_groups, verify_password

# === Gauges ===

ldap_server_healthy = Gauge(
    "phoenix_ldap_server_healthy", "LDAP server health status (1=healthy, 0=unhealthy)", ["server"]
)

ldap_servers_configured = Gauge(
    "phoenix_ldap_servers_configured", "Number of configured LDAP servers"
)
```

<a id="usage-in-code"></a>

### 代码用法

```python
async def authenticate(self, username: str, password: str) -> LDAPUserInfo | None:
    """Authenticate with metrics instrumentation."""
    for server in self.servers:
        with ldap_auth_duration_seconds.labels(server=server.host).time():
            try:
                result = await self._authenticate_on_server(server, username, password)
                if result:
                    ldap_auth_total.labels(result="success", server=server.host).inc()
                    return result
                else:
                    ldap_auth_total.labels(result="invalid_credentials", server=server.host).inc()
                    return None
            except LDAPException as e:
                ldap_auth_total.labels(result="server_error", server=server.host).inc()
                continue

    ldap_auth_total.labels(result="all_failed", server="all").inc()
    return None
```

<a id="grafana-dashboard-future"></a>

### Grafana 仪表盘（未来）

考虑提供用于 LDAP 监控的预构建 Grafana 仪表盘 JSON：
- 身份验证成功率和失败率
- 延迟分位数（P50、P95、P99）
- 服务器健康状态
- 错误类型分布

---

<a id="4-nested-group-resolution-for-active-directory"></a>

## 4. Active Directory 嵌套组解析

**影响**：中 | **复杂度**：高 | **目标**：阶段 3，由客户需求驱动

<a id="current-behavior-3"></a>

### 当前行为

目前仅通过 `memberOf` 属性解析直接组成员关系。

<a id="problem-3"></a>

### 问题

许多 AD 部署使用嵌套组：
```
Phoenix Admins (group)
  └── IT Admins (group)        ← Nested group
        └── alice (user)       ← Indirect member of "Phoenix Admins"
```

当前实现不会将 Alice 识别为“Phoenix Admins”的成员。

<a id="option-a-ldap_matching_rule_in_chain-recommended"></a>

### 方案 A：LDAP_MATCHING_RULE_IN_CHAIN（推荐）

```python
def _get_nested_groups_ad(self, conn: Connection, user_dn: str) -> list[str]:
    """Resolve nested AD groups using recursive membership filter.

    Uses Microsoft's LDAP_MATCHING_RULE_IN_CHAIN (OID 1.2.840.113556.1.4.1941)
    which recursively expands group membership server-side.

    Performance: Single LDAP query, server does recursion
    Compatibility: AD-only (not OpenLDAP)

    Args:
        conn: Active LDAP connection
        user_dn: User's distinguished name

    Returns:
        List of all group DNs (direct + transitive)
    """
    # OID 1.2.840.113556.1.4.1941 = LDAP_MATCHING_RULE_IN_CHAIN
    # Finds all groups where user_dn is a member (directly or transitively)
    nested_filter = f"(member:1.2.840.113556.1.4.1941:={escape_filter_chars(user_dn)})"

    conn.search(
        search_base=self.config.group_search_base_dns[0],
        search_filter=nested_filter,
        search_scope=SUBTREE,
        attributes=["distinguishedName"],
    )

    return [entry.entry_dn for entry in conn.entries]
```

<a id="option-b-tokengroups-attribute"></a>

### 方案 B：tokenGroups 属性

```python
def _get_nested_groups_via_token_groups(self, conn: Connection, user_dn: str) -> list[str]:
    """Resolve nested groups via AD's tokenGroups attribute.

    tokenGroups contains binary SIDs of all groups (including nested).
    Requires additional lookup to convert SIDs to DNs.

    Performance: Two queries (get SIDs, resolve to DNs)
    Compatibility: AD-only

    Pros:
        - Returns security groups only (no distribution lists)
        - Includes domain-local groups from trusts

    Cons:
        - Binary SID handling complexity
        - Requires SID-to-DN resolution query
    """
    # Step 1: Get tokenGroups (binary SIDs)
    conn.search(
        search_base=user_dn,
        search_filter="(objectClass=*)",
        search_scope=BASE,
        attributes=["tokenGroups"],
    )

    if not conn.entries:
        return []

    sids = conn.entries[0].tokenGroups.raw_values

    # Step 2: Resolve SIDs to DNs
    groups = []
    for sid in sids:
        sid_string = self._binary_sid_to_string(sid)
        conn.search(
            search_base=self.config.user_search_base_dns[0],
            search_filter=f"(objectSid={sid_string})",
            search_scope=SUBTREE,
            attributes=["distinguishedName"],
        )
        if conn.entries:
            groups.append(conn.entries[0].entry_dn)

    return groups
```

<a id="configuration"></a>

### 配置

```bash
# Enable nested group resolution (default: false for backward compatibility)
PHOENIX_LDAP_NESTED_GROUPS=true

# Method selection (if multiple supported in future)
PHOENIX_LDAP_NESTED_GROUPS_METHOD=chain  # or "tokengroups"
```

<a id="references-1"></a>

### 参考资料

- [MS-ADTS LDAP_MATCHING_RULE_IN_CHAIN](https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/)
- [tokenGroups 属性](https://docs.microsoft.com/en-us/windows/win32/adschema/a-tokengroups)
- [SID 结构（MS-DTYP）](https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-dtyp/)

---

<a id="5-connection-health-checks"></a>

## 5. 连接健康检查

**影响**：低 | **复杂度**：中 | **目标**：阶段 3

<a id="current-behavior-4"></a>

### 当前行为

仅在身份验证时发现服务器故障。

<a id="problem-4"></a>

### 问题

首位访问故障服务器的用户会在故障转移期间遭遇延迟。没有针对服务器问题的主动告警。

<a id="implementation-sketch-3"></a>

### 实现草案

```python
import asyncio
from typing import Optional


class LDAPAuthenticator:
    def __init__(self, config: LDAPConfig):
        self.servers = self._create_servers()
        self._healthy_servers: list[Server] = list(self.servers)
        self._health_check_task: Optional[asyncio.Task] = None

    async def start_health_checks(self, interval: float = 30.0) -> None:
        """Background task to check server health.

        Performs lightweight anonymous bind or rootDSE query to verify connectivity.
        Updates _healthy_servers list for prioritized failover.

        Args:
            interval: Seconds between health check cycles
        """
        logger.info(f"Starting LDAP health checks (interval={interval}s)")

        while True:
            await asyncio.sleep(interval)

            for server in self.servers:
                healthy = await self._check_server_health(server)

                if healthy and server not in self._healthy_servers:
                    self._healthy_servers.append(server)
                    logger.info(f"LDAP server {server.host} recovered")
                    ldap_server_healthy.labels(server=server.host).set(1)

                elif not healthy and server in self._healthy_servers:
                    self._healthy_servers.remove(server)
                    logger.warning(f"LDAP server {server.host} is unhealthy")
                    ldap_server_healthy.labels(server=server.host).set(0)

    async def _check_server_health(self, server: Server) -> bool:
        """Quick connectivity check via rootDSE query.

        RootDSE is always accessible without authentication and returns
        server capabilities. Faster than bind operations.
        """
        try:
            conn = Connection(
                server,
                auto_bind=False,
                receive_timeout=5,  # Short timeout for health checks
            )
            conn.open()

            # Query rootDSE (always accessible)
            conn.search(
                search_base="",
                search_filter="(objectClass=*)",
                search_scope=BASE,
                attributes=["namingContexts"],
            )

            conn.unbind()
            return True

        except LDAPException:
            return False

    async def stop_health_checks(self) -> None:
        """Stop background health check task."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None

    async def authenticate(self, username: str, password: str) -> LDAPUserInfo | None:
        """Authenticate with health-aware server selection."""
        # Prioritize healthy servers, fall back to all servers if none healthy
        servers_to_try = self._healthy_servers if self._healthy_servers else self.servers

        for server in servers_to_try:
            try:
                result = await self._authenticate_on_server(server, username, password)
                if result:
                    return result
            except LDAPException:
                continue

        return None
```

<a id="fastapi-lifespan-integration"></a>

### FastAPI 生命周期集成

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if ldap_config := get_ldap_config():
        authenticator = LDAPAuthenticator(ldap_config)
        authenticator._health_check_task = asyncio.create_task(authenticator.start_health_checks())
        app.state.ldap_authenticator = authenticator

    yield

    # Shutdown
    if hasattr(app.state, "ldap_authenticator"):
        await app.state.ldap_authenticator.stop_health_checks()
```

---

<a id="6-group-search-pagination"></a>

## 6. 组搜索分页

**影响**：低 | **复杂度**：低 | **目标**：按需

<a id="current-behavior-5"></a>

### 当前行为

POSIX 模式组搜索使用单次不分页查询。

<a id="problem-5"></a>

### 问题

LDAP 服务器通常将结果限制为 1000 个条目，可配置。搜索基准中具有超过 1000 个组的组织可能获得截断结果。

<a id="implementation-sketch-4"></a>

### 实现草案

```python
from ldap3.extend.standard import paged_search


def _search_groups_paged(
    self, conn: Connection, search_base: str, search_filter: str, page_size: int = 500
) -> list[str]:
    """Search groups with pagination for large directories.

    Uses LDAP Simple Paged Results Control (RFC 2696) to handle
    directories with more than 1000 groups.

    Args:
        conn: Active LDAP connection
        search_base: Base DN for group search
        search_filter: LDAP filter for group membership
        page_size: Results per page (default 500)

    Returns:
        List of all matching group DNs
    """
    groups = []

    generator = paged_search.paged_search_generator(
        conn,
        search_base=search_base,
        search_filter=search_filter,
        search_scope=SUBTREE,
        attributes=["distinguishedName"],
        paged_size=page_size,
    )

    for entry in generator:
        if entry["type"] == "searchResEntry":
            groups.append(entry["dn"])

    logger.debug(f"Paged search returned {len(groups)} groups from {search_base}")
    return groups
```

<a id="when-to-implement"></a>

### 实现时机

仅在客户报告截断问题时实现。问题信号包括：
- 用户未获得预期角色分配
- 日志提示结果不完整
- 大型企业拥有超过 1000 个 LDAP 组

<a id="references-2"></a>

### 参考资料

- [RFC 2696](https://www.rfc-editor.org/rfc/rfc2696) — LDAP 简单分页结果控制

---

<a id="implementation-recommendations"></a>

## 实现建议

<a id="phase-2-next-ldap-release"></a>

### 阶段 2（下一次 LDAP 发布）

合并以下三项改进，以获得显著运维价值：

1. ✅ **指标与可观测性** — 工作量低，生产运维必需
2. ✅ **重试逻辑** — 工作量低，提高可靠性
3. ⚠️ **密码策略处理** — 工作量中等，显著改善体验

**预计工作量**：合计 2—3 天

<a id="phase-3-future"></a>

### 阶段 3（未来）

根据客户需求实现：

4. ⏳ **嵌套组解析** — 仅在客户报告 AD 嵌套组问题时实现
5. ⏳ **连接健康检查** — 仅用于大型多服务器部署
6. ⏳ **组搜索分页** — 仅在报告截断时实现

<a id="not-recommended"></a>

### 不推荐

- **连接池**：对典型 Phoenix 工作负载（每秒少于 100 次身份验证），复杂度与收益的取舍不利。每次身份验证耗时少于 500ms，连接池管理开销可能超过建立连接的成本。

---

<a id="related-documentation"></a>

## 相关文档

- [LDAP 主规范](../ldap-authentication.md) — 实现概览
- [安全详解](./security.md) — 当前安全措施
- [配置参考](./configuration.md) — 环境变量
- [协议合规性](./protocol-compliance.md) — RFC 合规详情
