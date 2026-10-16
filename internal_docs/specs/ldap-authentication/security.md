<a id="security-deep-dive"></a>

# 安全详解

<a id="threat-model"></a>

## 威胁模型

| 威胁 | 攻击途径 | 影响 | 可能性 | 防护 |
|--------|---------------|--------|-----------|------------|
| **LDAP 注入** | 用户名字段中的恶意输入 | 未授权访问、数据泄漏 | 中 | 输入转义、参数化过滤器 |
| **凭证暴露** | 日志、网络嗅探 | 账户失陷 | 中 | TLS 加密、凭证清理 |
| **时序攻击** | 测量响应时间 | 用户名枚举 | 低 | 用户不存在时执行虚拟绑定，使用通用错误 |
| **暴力破解** | 自动登录尝试 | 账户失陷 | 高 | 限流、账户锁定 |
| **中间人攻击** | 网络拦截 | 凭证窃取 | 中 | TLS 与证书校验 |
| **事件循环 DoS** | 缓慢 LDAP 连接 | 服务不可用 | 中 | 线程池隔离、超时 |
| **正则表达式 DoS** | python-ldap 中的 CVE-2024-47764 | 服务性能下降 | 极低 | 使用 ldap3，不使用 python-ldap |
| **配置错误** | 错误组映射 | 权限提升 | 中 | 启动时校验、试运行模式 |
| **转介凭证泄漏** | 恶意转介至攻击者服务器 | 服务账户失陷 | 中 | 禁止跟随转介 |
| **邮箱回收攻击** | 回收邮箱劫持旧账户 | 数据泄漏、权限提升 | 中 | 唯一 ID 冲突检测 |
| **UUID 大小写不匹配** | 区分大小写查找未命中用户 | 账户锁定、重复账户 | 低 | 不区分大小写查找、小写规范化 |

---

<a id="ldap-injection-prevention"></a>

## LDAP 注入防护

**攻击示例**：
```python
# Vulnerable code (DON'T DO THIS):
username = request.username  # User input: "admin)(uid=*"
filter_str = f"(&(objectClass=user)(uid={username}))"
# Result: (&(objectClass=user)(uid=admin)(uid=*))
# Attacker bypasses authentication!
```

**防护**：
```python
from ldap3.utils.conv import escape_filter_chars

# Safe usage (Phoenix implementation):
username = escape_filter_chars(request.username)
filter_str = f"(&(objectClass=user)(uid={username}))"
```

**转义规则（RFC 4515）**：
- `\` → `\5c`
- `*` → `\2a`
- `(` → `\28`
- `)` → `\29`
- `\x00` → `\00`

**测试用例**：
```python
from ldap3.utils.conv import escape_filter_chars


def test_ldap_injection_prevention():
    # Test special characters
    assert escape_filter_chars("admin)(uid=*") == "admin\\29\\28uid=\\2a"
    assert escape_filter_chars("user\\admin") == "user\\5cadmin"

    # Test null byte
    assert escape_filter_chars("user\x00admin") == "user\\00admin"
```

**实现**：Phoenix 直接使用 `ldap3.utils.conv.escape_filter_chars()` 进行符合 RFC 4515 的转义。参见 `src/phoenix/server/ldap.py`。

---

<a id="timing-attack-prevention"></a>

## 时序攻击防护

**攻击**：攻击者通过测量响应时间判断用户名是否存在。

**攻击场景**：
1. 攻击者使用“admin”/“wrongpass”发送登录请求
2. 若“admin”存在：搜索成功 → 尝试绑定 → 响应约 150ms
3. 若“admin”不存在：搜索失败 → 立即返回 → 响应约 50ms
4. 攻击者测量响应时间以枚举有效用户名

**有漏洞的代码**：
```python
# DON'T DO THIS:
user_dn = search_user(username)
if not user_dn:
    return {"error": "User not found"}  # Fast response (no bind attempt)
    
if not authenticate(user_dn, password):
    return {"error": "Invalid password"}  # Slow response (LDAP bind attempt)
```

**防护**（Phoenix 实现）：
```python
# Phoenix performs a dummy bind when user is not found to equalize timing
def _dummy_bind_for_timing(self, server: Server, password: str) -> None:
    """Perform a dummy bind to equalize response timing when user is not found."""
    # Randomized DN prevents LDAP server caching/optimization
    dummy_dn = f"cn=dummy-{token_hex(8)},dc=invalid,dc=local"
    try:
        self._verify_user_password(server, dummy_dn, password)
    except Exception:
        pass  # Expected to fail - we only care about the timing


def _authenticate(self, username: str, password: str) -> Optional[LDAPUserInfo]:
    # ... search for user ...
    user_entry = self._search_user(conn, escaped_username)
    if not user_entry:
        # TIMING ATTACK MITIGATION: Perform dummy bind to prevent username enumeration
        # Both "user not found" and "wrong password" now perform the same network I/O
        self._dummy_bind_for_timing(server, password)
        return None

    # User found - verify password as normal
    if not self._verify_user_password(server, user_dn, password):
        return None
```

**使用虚拟绑定而非休眠的原因**：
- `asyncio.sleep()` 可预测，无法反映网络波动
- 真实绑定尝试具有可变延迟，包括 TLS 握手、网络 RTT 和服务器负载
- 虚拟绑定执行相同 I/O 操作，使时序难以区分
- 随机 DN（`token_hex(8)`）防止 LDAP 服务器缓存或优化响应

**结果**：用户存在和未找到两条代码路径均执行搜索与绑定，使响应时间在统计上不可区分。

---

<a id="rate-limiting"></a>

## 限流

**实现**（Phoenix 使用自定义 `ServerRateLimiter`）：
```python
from phoenix.server.rate_limiters import ServerRateLimiter, fastapi_ip_rate_limiter

# Configure rate limiter (0.2 req/sec = ~12 req/min per IP)
rate_limiter = ServerRateLimiter(
    per_second_rate_limit=0.2,
    enforcement_window_seconds=60,
    partition_seconds=60,
    active_partitions=2,
)

# Apply to authentication endpoints
login_rate_limiter = fastapi_ip_rate_limiter(
    rate_limiter,
    paths=[
        "/auth/login",
        "/auth/ldap/login",
        "/auth/logout",
        "/auth/refresh",
        "/auth/password-reset-email",
        "/auth/password-reset",
    ],
)

# Add as router dependency (can be disabled via PHOENIX_DISABLE_RATE_LIMIT)
auth_dependencies = [Depends(login_rate_limiter)] if not get_env_disable_rate_limit() else []
router = APIRouter(prefix="/auth", dependencies=auth_dependencies)
```

**账户锁定**（未来增强，尚未实现）：
```python
# Track failed attempts per username
failed_attempts = {}  # In production: use Redis

if failed_attempts.get(username, 0) >= 5:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Account temporarily locked"
    )

# Increment on failure
if not success:
    failed_attempts[username] = failed_attempts.get(username, 0) + 1
```

---

<a id="referral-credential-leakage-prevention"></a>

## 防止转介凭证泄漏

**威胁**：ldap3 默认配置会跟随 LDAP 转介，并向任意服务器发送凭证。

**攻击场景**：
1. 攻击者入侵或架设恶意 LDAP 服务器
2. 合法 LDAP 服务器发送转介：`ldap://attacker.com/...`
3. ldap3 跟随转介，将服务账户凭证发送给攻击者
4. 攻击者捕获 `bind_dn` 和 `bind_password`

**ldap3 默认行为**（存在漏洞）：
```python
# ldap3/core/server.py - DEFAULT allows ANY host with credentials!
if allowed_referral_hosts is None:
    allowed_referral_hosts = [("*", True)]  # Allow all hosts, send credentials
```

**STARTTLS 的额外风险**：
```python
# ldap3/strategy/base.py - Referral TLS config ignores original settings!
tls = Tls(...) if selected_referral["ssl"] else None  # STARTTLS referrals get NO TLS config!
```

对于指向 `ldap://` URL 的 STARTTLS 转介：
- 原连接：`Tls(validate=ssl.CERT_REQUIRED)` ✅
- 转介创建：`Tls()`，默认 `validate=ssl.CERT_NONE` ❌
- 结果：转介连接可能遭受中间人攻击！

**防护**（Phoenix 实现）：
```python
# Disable referral following on ALL Connection objects
Connection(
    server,
    user=bind_dn,
    password=bind_password,
    auto_referrals=False,  # SECURITY: Prevent credential leakage
    ...
)
```

**为什么禁用而非限制？**
- Phoenix 已有多服务器故障转移，可实现高可用
- 转介通常用于跨域查询，身份验证不需要
- Phoenix LDAP 流程没有跟随转介的合法使用场景

**受影响连接**（全部三种）：
1. 服务账户连接（`_establish_connection`）
2. 匿名绑定连接（`_establish_connection`）
3. 用户密码验证（`_verify_user_password`）

---

<a id="tls-configuration"></a>

## TLS 配置

**Phoenix TLS 实现**（参见 `ldap.py` 中的 `_create_servers()`）：
```python
# Certificate validation configuration
tls_kwargs: dict[str, Any] = {"validate": ssl.CERT_REQUIRED if config.tls_verify else ssl.CERT_NONE}

# Custom CA certificate for private/internal CAs
if config.tls_ca_cert_file:
    tls_kwargs["ca_certs_file"] = config.tls_ca_cert_file

# Client certificate for mutual TLS (mTLS)
if config.tls_client_cert_file and config.tls_client_key_file:
    tls_kwargs["local_certificate_file"] = config.tls_client_cert_file
    tls_kwargs["local_private_key_file"] = config.tls_client_key_file

tls_config = Tls(**tls_kwargs)
```

**建议**：生产环境启用 TLS（`PHOENIX_LDAP_TLS_MODE=starttls` 或 `ldaps`）和证书校验（`PHOENIX_LDAP_TLS_VERIFY=true`），防止凭证被截获。

**STARTTLS 安全**：关键执行顺序要求和对抗测试方法，参见[协议合规性 — STARTTLS 实现](./protocol-compliance.md#7-starttls-implementation--security)。

---

<a id="logging"></a>

## 日志

**MVP 方案**：仅记录用于运维调试的错误，不包含任何个人身份信息。

**记录的事件**（实际实现在 `ldap.py` 中）：
```python
# Empty credentials rejected (warning - security event)
logger.warning("LDAP authentication rejected: empty username")
logger.warning("LDAP authentication rejected: empty password")

# Server failure (warning - includes only error type, not details)
logger.warning(
    f"LDAP server {server.host} failed during authentication. Error type: {type(e).__name__}"
)

# All servers exhausted (error)
logger.error("All LDAP servers failed")

# Configuration/schema issues (error)
logger.error(
    f"LDAP user missing required email attribute "
    f"({config.attr_email}). Check LDAP schema configuration."
)
logger.error(
    f"Ambiguous LDAP search: found {len(conn.entries)} matching entries. "
    f"Rejecting authentication for safety. ..."
)

# Debug-level (not shown in production logs by default)
logger.debug("User not found in LDAP directory")
logger.debug("LDAP password verification failed")
```

**原因**：仅记录管理员排查运维问题所需的错误，例如服务器连接、TLS 问题和配置错误。不记录成功或失败事件，避免个人身份信息处理复杂度。

**禁止记录**：
- ❌ 用户名，属于个人身份信息
- ❌ 密码，绝不记录凭证
- ❌ 绑定 DN 密码，即服务账户凭证
- ❌ 邮箱地址，属于个人身份信息
- ❌ 组 DN，属于个人身份信息，会暴露组织结构
- ❌ 用户特定失败，例如“用户 X 的凭证无效”
- ❌ 成功的身份验证

**未来增强**：MVP 之后添加可选安全审计日志，包括用户名哈希、个人身份信息控制、保留策略和 GDPR、SOC2 合规文档。

---

<a id="event-loop-dos-prevention"></a>

## 事件循环 DoS 防护

**威胁**：LDAP 操作受网络限制，如未适当隔离，会阻塞 FastAPI 事件循环。

**攻击场景**：
```
1. Attacker opens multiple slow LDAP connections
2. Each connection blocks an async worker thread
3. Legitimate requests queue up (503 Service Unavailable)
4. Service degradation even with rate limiting
```

**根因**：`ldap3` 库仅支持同步。连接、TLS 握手、绑定和搜索等所有操作都会阻塞调用线程。

**防护**：
```python
# Phoenix implementation: Thread pool isolation
async def authenticate(self, username: str, password: str) -> Optional[LDAPUserInfo]:
    # Timeout prevents HTTP request hang, but thread continues until socket timeout
    with anyio.fail_after(60):
        return await anyio.to_thread.run_sync(self._authenticate, username, password)

def _authenticate(self, username: str, password: str) -> Optional[LDAPUserInfo]:
    # Socket-level timeout is the real enforcement mechanism
    conn = Connection(server, receive_timeout=30, ...)
```

**收益**：
- ✅ LDAP 操作期间主事件循环保持响应
- ✅ 缓慢 LDAP 服务器不会耗尽 FastAPI 工作进程
- ✅ 多个并发 LDAP 身份验证互不阻塞
- ✅ 在异步框架中封装同步 I/O 的标准模式

**超时执行**：
- **实际超时**：`receive_timeout=30`，socket 级，终止阻塞操作
- **HTTP 超时**：`fail_after(60)`，防止客户端挂起，返回 500 错误
- **限制**：无法从外部取消线程，这是 Python 限制
- **结果**：若 socket 超时失效，线程会成为孤立线程，直到自然完成

**为何不使用 ldap3.ASYNC**：`ldap3` 提供 `ASYNC` 策略，但不兼容 Python `asyncio`：
- 使用后台线程，而非 asyncio 任务
- 仍执行阻塞 socket 操作
- 设计早于 Python async/await，属于 2013 年代

通过 `anyio.to_thread.run_sync()` 进行线程池隔离，是将同步 LDAP 库集成至异步框架的标准方式。

---

<a id="email-recycling-attack-prevention"></a>

## 防止邮箱回收攻击

**威胁**：企业模式下配置了 unique_id，使用回收邮箱的新员工可能劫持旧员工账户。

**攻击场景**（未防护时）：
1. 用户 A 离职，数据库中为 `email=john@corp.com`、`oauth2_user_id=UUID-A`
2. 用户 B 入职，使用回收邮箱，LDAP 中为 `email=john@corp.com`、`unique_id=UUID-B`
3. 用户 B 登录：
   - 按 unique_id 查找：数据库中未找到 `UUID-B`
   - 邮箱回退：找到用户 A 的账户
   - **有漏洞的代码会将用户 A 的 `oauth2_user_id` 更新为 `UUID-B`**
   - 用户 B 由此可以访问用户 A 的数据！

**防护**（Phoenix 实现）：
```python
# Only migrate if user has no existing unique_id
if user.oauth2_user_id is None:
    user.oauth2_user_id = unique_id  # Safe: first-time migration
elif user.oauth2_user_id.lower() != unique_id.lower():
    # Different person - reject (email is unique in DB, can't create new account)
    raise HTTPException(
        status_code=403,
        detail="Account conflict: this email is associated with a different "
        "LDAP account. Contact your administrator.",
    )
```

**为什么返回 403，而不创建新账户？**
- 邮箱在数据库中唯一（`CREATE UNIQUE INDEX ix_users_email`）
- 使用相同邮箱创建新用户会因违反约束而失败
- 明确的 403 为用户提供清晰错误，并引导其联系管理员

**解决方案**（需要管理员介入）：
1. 删除旧账户，确认原用户确实离职时使用
2. 将旧账户的 `oauth2_user_id` 更新为新 UUID
3. 修改旧账户邮箱，释放原邮箱

---

<a id="uuid-case-normalization"></a>

## UUID 大小写规范化

**威胁**：区分大小写的 UUID 查找可能导致账户锁定或重复账户。

**场景**：
1. 旧版 Phoenix 存储：`oauth2_user_id = "550E8400-..."`，大写
2. 新版 Phoenix 规范化为：`unique_id = "550e8400-..."`，小写
3. 区分大小写查找失败 → 用户无法登录或产生重复账户

**防护**：

1. **将输出规范化为小写**（在 `_get_unique_id` 中）：
```python
# UUIDs are case-insensitive per RFC 4122
return decoded.lower()  # Normalize entryUUID
return str(uuid.UUID(bytes_le=...))  # uuid.UUID always returns lowercase
```

2. **不区分大小写的数据库查找**：
```python
# Use func.lower() for case-insensitive comparison
.where(func.lower(models.User.oauth2_user_id) == unique_id.lower())
```

3. **不区分大小写的冲突检测**：
```python
# Compare lowercase to handle legacy data
elif user.oauth2_user_id.lower() != unique_id.lower():
    raise HTTPException(403, ...)
```

**结果**：UUID 大小写不同的已有用户会在下次登录时被找到并更新。

---

<a id="unique-id-extraction-robustness"></a>

## 唯一 ID 提取健壮性

**威胁**：格式错误或边界情况的 LDAP 属性值可能导致崩溃或错误 ID。

**已处理的边界情况**：

| 输入 | 处理 | 结果 |
|-------|----------|--------|
| 缺少属性 | `getattr(entry, attr_name, None)` | `None` |
| 空属性（`values=[]`） | 检查 `attr is None` | `None` |
| 空字节（`b""`） | 检查长度 | `None` |
| 仅空白（`b"   "`） | 去除空白后检查 | `None` |
| 16 字节二进制，objectGUID | `uuid.UUID(bytes_le=...)` | 小写 UUID |
| 字节形式字符串 UUID，entryUUID | UTF-8 解码并转换为小写 | 小写 UUID |
| 大写 UUID | `.lower()` 规范化 | 小写 UUID |
| 无效 UTF-8 二进制 | `.hex()` 回退 | 十六进制字符串 |

**实现**（防御式编码）：
```python
def _get_unique_id(entry: Any, attr_name: str) -> Optional[str]:
    attr = getattr(entry, attr_name, None)
    if attr is None:
        return None
    
    raw_value = attr.raw_values[0] if hasattr(attr, "raw_values") and attr.raw_values else None
    if raw_value is None:
        return None
    
    if isinstance(raw_value, (bytes, bytearray, memoryview)):
        raw_bytes = bytes(raw_value)
        if len(raw_bytes) == 0:
            return None
        if len(raw_bytes) == 16:
            return str(uuid.UUID(bytes_le=raw_bytes))  # Always lowercase
        else:
            try:
                decoded = raw_bytes.decode("utf-8").strip()
                return decoded.lower() if decoded else None
            except UnicodeDecodeError:
                return raw_bytes.hex()  # Hex is already lowercase
    
    result = str(raw_value).strip()
    return result.lower() if result else None
```

---

<a id="configuration-validation"></a>

## 配置校验

**威胁**：LDAP 属性名称拼写错误会导致静默失败。

**场景**：
```bash
# Typo: space in attribute name
PHOENIX_LDAP_ATTR_UNIQUE_ID="object GUID"  # Should be "objectGUID"
```

LDAP 服务器对 `"object GUID"` 不返回结果，因为该属性不存在，导致所有用户身份验证均以“missing unique_id”错误失败。

**防护**（`config.py` 中的启动校验）：
```python
# Validate attribute names don't contain spaces
for attr_var, attr_val in [
    ("PHOENIX_LDAP_ATTR_EMAIL", attr_email),
    ("PHOENIX_LDAP_ATTR_DISPLAY_NAME", attr_display_name),
    ("PHOENIX_LDAP_ATTR_MEMBER_OF", attr_member_of),
    ("PHOENIX_LDAP_ATTR_UNIQUE_ID", attr_unique_id),
]:
    if attr_val and " " in attr_val:
        raise ValueError(
            f"{attr_var} contains spaces: '{attr_val}'. "
            f"LDAP attribute names cannot contain spaces. "
            f"Did you mean '{attr_val.replace(' ', '')}'?"
        )
```

**结果**：启动时捕获配置错误，并提供有用建议。

---

<a id="socket-leak-prevention"></a>

## 防止 socket 泄漏

**威胁**：连接未正确清理时，失败的 LDAP 操作可能泄漏文件描述符。

**漏洞**：仅在满足条件时执行的连接清理代码可能使 socket 保持打开：
```python
# VULNERABLE: Socket leak on bind failure
try:
    conn.open()
    conn.start_tls()
    conn.bind()
    return conn.bound
finally:
    if conn.bound:  # ← Only runs if bind() succeeded!
        conn.unbind()
```

**泄漏场景**：
1. `conn.open()` 抛出异常 → socket 已打开，跳过清理 → **泄漏**
2. `conn.start_tls()` 抛出异常 → socket 已打开，跳过清理 → **泄漏**
3. `conn.bind()` 抛出异常 → socket 已打开，跳过清理 → **泄漏**
4. 密码错误 → `conn.bound = False` → 跳过清理 → **泄漏**

**影响**：重复登录失败耗尽文件描述符 → 进程崩溃

**防护**：
```python
# Phoenix implementation: Unconditional cleanup
try:
    conn.open()
    conn.start_tls()
    conn.bind()
    return conn.bound
finally:
    # CRITICAL: Always unbind to close socket, regardless of bind state
    conn.unbind()  # Closes socket even if connection not bound
```

**要点**：无论连接状态如何，`ldap3.Connection.unbind()` 均能安全关闭底层 socket。以下情况也可调用：
- `open()` 从未成功
- `start_tls()` 在握手中途失败
- 尚未尝试 `bind()`
- 密码验证失败

**测试覆盖**：单元测试验证以下情况的 socket 清理：
- 绑定失败，密码错误
- `open()` 异常
- `start_tls()` 异常
- 匿名绑定中 TLS 失败

---

<a id="additional-security-resources"></a>

## 更多安全资源

- [用户识别策略](./user-identification-strategy.md) — 邮箱回收保护、大小写规范化、迁移逻辑
- [协议合规性](./protocol-compliance.md) — 防止匿名绑定、拒绝歧义搜索、DN 校验
- [配置参考](./configuration.md) — TLS 配置选项和安全建议
- [Grafana 对比](./grafana-comparison.md) — 从 Grafana 实现借鉴的安全模式

<a id="references"></a>

## 参考资料

- [RFC 4122 — UUID URN 命名空间](https://www.rfc-editor.org/rfc/rfc4122.html) — UUID 不区分大小写
- [RFC 4515 — LDAP 搜索过滤器](https://www.rfc-editor.org/rfc/rfc4515.html) — 过滤器转义规则
- [MS-DTYP §2.3.4 — GUID 结构](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-dtyp/001eec5a-7f8b-4293-9e21-ca349392db40) — objectGUID 二进制格式
- [ldap3 转介处理](https://ldap3.readthedocs.io/en/latest/referrals.html) — 默认 `auto_referrals=True` 行为

