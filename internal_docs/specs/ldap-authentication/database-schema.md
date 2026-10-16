<a id="database-schema-details"></a>

# 数据库结构详情

<a id="current-implementation-stopgap"></a>

## 当前实现（临时方案）

**存储格式**：
```
users table:
  auth_method = 'OAUTH2'
  oauth2_client_id = '\ue000LDAP(stopgap)'  ← Identifies as LDAP user
  oauth2_user_id = '<unique_id>' or NULL    ← Immutable ID (if configured) or NULL (email-based)
  email = 'john@example.com'                ← User identifier (simple mode) or synced attribute
  username = 'John Doe'                     ← Display name (synced from LDAP)
```

**标记格式**：`\ue000LDAP(stopgap)`
- `\ue000` = Unicode 私用区（U+E000-U+F8FF）
- `LDAP` = 人类可读标识符
- 所有 LDAP 用户使用同一个简单常量值

**无冲突的原因**：
1. **Unicode PUA 保证**：U+E000-U+F8FF 保留为私用区，Unicode 标准永不分配，已有 30 多年保证
2. **OAuth2 RFC 6749**：将 `client_id` 限制为 ASCII（0x20-0x7E），不能包含 Unicode
3. **实际验证**：没有 OAuth2 提供方在客户端 ID 中使用 Unicode 字符
4. **主动防御**：`_validate_oauth2_client_id()` 拒绝已配置 OAuth2 客户端 ID 中的 PUA 字符

**用户识别**：

| 模式 | `oauth2_user_id` | 查找方式 |
|------|------------------|--------|
| 简单模式（默认） | `NULL` | 按 `email` 列 |
| 企业模式 | objectGUID/entryUUID | 按 `oauth2_user_id`，回退至 `email` |

详情参见[用户识别策略](./user-identification-strategy.md)。

**实现**：

```python
LDAP_CLIENT_ID_MARKER = "\ue000LDAP(stopgap)"  # Simple constant marker
```

**辅助函数**：
```python
LDAP_CLIENT_ID_MARKER = "\ue000LDAP(stopgap)"


def is_ldap_user(oauth2_client_id: Optional[str]) -> bool:
    """Check if user is authenticated via LDAP."""
    return oauth2_client_id == LDAP_CLIENT_ID_MARKER
```

**数据库查询**：
```sql
-- Find all LDAP users
SELECT * FROM users 
WHERE oauth2_client_id = E'\uE000LDAP(stopgap)';

-- Simple mode: Find LDAP user by email
SELECT * FROM users 
WHERE oauth2_client_id = E'\uE000LDAP(stopgap)'
  AND LOWER(email) = 'john@example.com';

-- Enterprise mode: Find LDAP user by unique_id
SELECT * FROM users 
WHERE oauth2_client_id = E'\uE000LDAP(stopgap)'
  AND oauth2_user_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

<a id="future-migration-dedicated-schema"></a>

## 未来迁移（独立结构）

如果将来迁移至独立的 LDAP 数据库结构，变更如下：

**结构变更**：
```sql
-- Step 1: Allow 'LDAP' as auth_method
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_auth_method_check;
ALTER TABLE users ADD CONSTRAINT users_auth_method_check
    CHECK (auth_method IN ('LOCAL', 'OAUTH2', 'LDAP'));

-- Step 2: Migrate LDAP users
UPDATE users 
SET auth_method = 'LDAP'
WHERE oauth2_client_id = E'\uE000LDAP(stopgap)';
```

**说明**：不新增 `ldap_dn` 列。DN 不用于识别用户，因为 DN 变化过于频繁。用户通过邮箱或 unique_id（objectGUID/entryUUID）识别。

**迁移后查询**：
```sql
-- Find all LDAP users (cleaner!)
SELECT * FROM users WHERE auth_method = 'LDAP';

-- Simple mode: Find LDAP user by email
SELECT * FROM users 
WHERE auth_method = 'LDAP'
  AND LOWER(email) = 'john@example.com';

-- Enterprise mode: Find LDAP user by unique_id
SELECT * FROM users 
WHERE auth_method = 'LDAP'
  AND oauth2_user_id = '550e8400-e29b-41d4-a716-446655440000';
```

**要点**：迁移仅更改 `auth_method` 以明确语义。识别策略（邮箱或 unique_id）保持不变。

完整详情参见[迁移计划](./migration-plan.md)。
