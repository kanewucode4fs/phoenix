<a id="background-ldap-sync-future"></a>

# 后台 LDAP 同步（未来）

**可选后台 LDAP 同步的完整设计** — 面向企业部署的未来增强功能。

<a id="overview"></a>

## 概述

后台 LDAP 同步是一项 **MVP 之后的功能**，按计划（例如每晚）自动将所有 LDAP 用户与目录同步。它参考 Grafana 仅企业版提供的后台同步功能。

<a id="what-it-does"></a>

## 功能

1. **计划执行**：按 cron 计划运行（例如每天凌晨 1 点）
2. **用户同步**：遍历数据库中的所有 LDAP 用户
3. **属性更新**：从 LDAP 目录同步邮箱、姓名和角色
4. **自动停用**：禁用已从 LDAP 移除的用户并撤销其会话
5. **重新启用**：重新激活在 LDAP 中找到的已禁用用户

<a id="implementation-pattern"></a>

## 实现模式

Phoenix 将采用现有 `DaemonTask` 模式，与 `TraceDataSweeper`、`TokenStore` 等相同：

```python
class LDAPUserSynchronizer(DaemonTask):
    """Background task to sync LDAP users with the database."""
    
    async def _run(self) -> None:
        while self._running:
            await self._sleep_until_next_run()  # Based on cron expression
            await self._sync_all_ldap_users()
```

<a id="configuration"></a>

## 配置

```bash
# Enable background sync (default: false)
PHOENIX_LDAP_BACKGROUND_SYNC_ENABLED="true"

# Cron schedule (default: "0 1 * * *" = 1 AM daily)
PHOENIX_LDAP_BACKGROUND_SYNC_CRON="0 1 * * *"
```

<a id="when-to-use"></a>

## 使用场景

**适合启用**：
- 大型组织（1000 名以上 LDAP 用户）
- 要求立即停用账户的严格安全策略
- 不经常登录的用户

**适合跳过**：
- 小规模部署（少于 100 名用户）
- 用户经常登录，登录时已同步
- LDAP 服务器限流或网络成本较高

<a id="implementation-roadmap"></a>

## 实现路线图

- **阶段 1（MVP）**：仅登录时同步 ✅
- **阶段 2（MVP 之后）**：手动同步 API 端点
- **阶段 3（未来）**：自动后台同步

**决策**：推迟至用户提出需求。大多数 Phoenix 部署规模为中小型，登录时同步已经足够。

**说明**：完整实现详情，包括详细代码示例、指标、性能调优和批处理，见原完整文档中的“Phoenix 后台同步设计（未来）”章节（第 1849—2356 行）。

