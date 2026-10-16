<a id="future-migration-stopgap--dedicated-ldap-schema"></a>

# 未来迁移：临时方案 → 独立 LDAP 数据库结构

**背景**：Phoenix 最初复用 OAuth2 列，以临时方案发布 LDAP。本文描述未来在认为值得投入时，迁移至独立 LDAP 数据库结构的方案。

---

<a id="current-implementation-stopgap"></a>

## 当前实现（临时方案）

Phoenix 使用现有 OAuth2 列保存 LDAP 用户：

| 字段 | 值 | 用途 |
|-------|-------|---------|
| `auth_method` | `'OAUTH2'` | 满足现有 CHECK 约束 |
| `oauth2_client_id` | `'\ue000LDAP(stopgap)'` | 识别 LDAP 用户的 Unicode 标记 |
| `oauth2_user_id` | `<unique_id>` 或 `NULL` | 不可变 LDAP ID（若已配置），或 NULL（基于邮箱） |
| `email` | `user@example.com` | 邮箱，具有唯一约束，也是简单模式的主要标识符 |

**识别策略**（参见[用户识别策略](./user-identification-strategy.md)）：

| 模式 | `oauth2_user_id` | 查找方式 |
|------|------------------|--------|
| 简单模式（默认） | `NULL` | 按邮箱列 |
| 企业模式 | objectGUID/entryUUID | 按 oauth2_user_id，回退至邮箱 |

---

<a id="future-migration-dedicated-schema"></a>

## 未来迁移（独立结构）

**迁移时机**：已决定清晰的数据库结构值得迁移成本。

**迁移原因**：
- ✅ 语义清晰：使用 `auth_method='LDAP'` 代替 `'OAUTH2'`
- ✅ 类型安全：具有多态支持的独立 `LDAPUser` 类
- ✅ 不再混用 OAuth2 列
- ⚠️ 需要数据库迁移和停机

**结构变更**：

```sql
-- Step 1: Allow 'LDAP' as auth_method
ALTER TABLE users DROP CONSTRAINT users_auth_method_check;
ALTER TABLE users ADD CONSTRAINT users_auth_method_check
    CHECK (auth_method IN ('LOCAL', 'OAUTH2', 'LDAP'));

-- Step 2: Migrate LDAP users
UPDATE users 
SET auth_method = 'LDAP'
WHERE oauth2_client_id = E'\uE000LDAP(stopgap)';

-- Step 3: Update field validation (oauth2_user_id may be NULL for email-based users)
ALTER TABLE users ADD CONSTRAINT users_ldap_check CHECK (
    (auth_method = 'LDAP' AND oauth2_client_id = E'\uE000LDAP(stopgap)')
    OR (auth_method != 'LDAP')
);
```

**代码变更**：

```python
# Before (stopgap)
def is_ldap_user(oauth2_client_id: str) -> bool:
    return oauth2_client_id == LDAP_CLIENT_ID_MARKER


# After (dedicated)
user = await session.scalar(
    select(models.User)
    .where(models.User.auth_method == "LDAP")
    .where(...)  # lookup by unique_id or email
)
```

---

<a id="migration-script"></a>

## 迁移脚本

```python
"""Migrate LDAP users to auth_method='LDAP'.

Revision ID: ldap_dedicated_schema
"""

from alembic import op
from sqlalchemy.sql import text

LDAP_MARKER = "\ue000LDAP(stopgap)"


def upgrade():
    conn = op.get_bind()

    # Step 1: Update CHECK constraint to allow 'LDAP'
    op.drop_constraint("users_auth_method_check", "users", type_="check")
    op.create_check_constraint(
        "users_auth_method_check", "users", "auth_method IN ('LOCAL', 'OAUTH2', 'LDAP')"
    )

    # Step 2: Migrate LDAP users
    result = conn.execute(
        text("""
        UPDATE users
        SET auth_method = 'LDAP'
        WHERE oauth2_client_id = :marker
    """),
        {"marker": LDAP_MARKER},
    )

    print(f"✓ Migrated {result.rowcount} LDAP users to auth_method='LDAP'")


def downgrade():
    conn = op.get_bind()

    # Revert auth_method
    conn.execute(
        text("""
        UPDATE users
        SET auth_method = 'OAUTH2'
        WHERE auth_method = 'LDAP'
    """)
    )

    # Restore original constraint
    op.drop_constraint("users_auth_method_check", "users", type_="check")
    op.create_check_constraint(
        "users_auth_method_check", "users", "auth_method IN ('LOCAL', 'OAUTH2')"
    )

    print("✓ Reverted LDAP users to stopgap format")
```

---

<a id="validation"></a>

## 验证

<a id="pre-migration"></a>

### 迁移前

```sql
-- Count LDAP users
SELECT COUNT(*) FROM users WHERE oauth2_client_id = E'\uE000LDAP(stopgap)';

-- Check identifier distribution
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE oauth2_user_id IS NOT NULL) as with_unique_id,
    COUNT(*) FILTER (WHERE oauth2_user_id IS NULL) as email_only
FROM users 
WHERE oauth2_client_id = E'\uE000LDAP(stopgap)';
```

<a id="post-migration"></a>

### 迁移后

```sql
-- Verify all LDAP users migrated
SELECT COUNT(*) FROM users WHERE auth_method = 'LDAP';

-- Should match pre-migration count
SELECT COUNT(*) FROM users WHERE oauth2_client_id = E'\uE000LDAP(stopgap)';
```

---

<a id="when-to-migrate"></a>

## 迁移时机

**以下情况保留临时方案**：
- ✅ 当前实现运行良好
- ✅ 查询和报表不需要 `auth_method='LDAP'`
- ✅ 不值得投入迁移协调成本

**以下情况进行迁移**：
- ✅ 希望语义清晰（`auth_method='LDAP'`）
- ✅ 希望使用支持多态的类型安全 `LDAPUser` 类
- ✅ 已准备好协调各部署的迁移

**说明**：临时方案功能完整。迁移属于可选清理，并非必需。

---

<a id="summary"></a>

## 汇总

| 方面 | 临时方案（当前） | 独立结构（未来） |
|--------|-------------------|-------------------|
| `auth_method` | `'OAUTH2'` | `'LDAP'` |
| 检测 | `oauth2_client_id == marker` | `auth_method == 'LDAP'` |
| 标识符 | 邮箱或 unique_id | 邮箱或 unique_id，不变 |
| 多态 | 不支持 | 支持，使用 `LDAPUser` 类 |
| 迁移 | 无 | 约一天工作量 |

**要点**：识别策略（邮箱/unique_id）保持不变。迁移仅影响数据库结构的语义。
