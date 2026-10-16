<a id="ldap-authentication---appendices"></a>

# LDAP 身份验证附录

[LDAP 身份验证规范](../ldap-authentication.md)的详细技术参考。

<a id="quick-reference"></a>

## 快速参考

**初次接触 LDAP？**
- [LDAP 入门](./ldap-primer.md) — **面向熟悉 OIDC 的工程师的 LDAP 基础知识**，从这里开始！

**最常用**：
- [配置参考](./configuration.md) — 环境变量及 Phoenix 与 Grafana 对比
- [协议合规性](./protocol-compliance.md) — STARTTLS 安全、DN 规范化、Docker 测试
- [安全详解](./security.md) — 威胁模型和 LDAP 注入防护
- [身份验证框架](./authentication-framework.md) — 多方法身份验证、跨验证方式安全和管理员配置
- [DN 与邮箱策略](./dn-email-strategy.md) — 用户识别、RFC 4514 规范化和邮箱回退

**实现**：
- [代码示例](./code-examples.md)
- [前端实现](./frontend-implementation.md)
- [Phoenix 集成](./phoenix-integration.md)

**设计与架构**：
- [数据库结构](./database-schema.md)
- [用户识别策略](./user-identification-strategy.md)
- [LDAP 用户邮箱可选](./optional-email.md) — 支持没有邮箱属性的 LDAP 目录
- [决策可逆性](./decision-reversibility.md)
- [迁移计划](./migration-plan.md)

**安全与合规**：
- [冲突预防](./collision-prevention.md)

**测试**：
- [测试流程](./testing.md) — 运行和扩展 LDAP 测试，包括集成、Docker 和覆盖率

**研究**：
- [Grafana 对比](./grafana-comparison.md)
- [后台同步（未来）](./background-sync-future.md)

**路线图**：
- [未来改进](./future-improvements.md) — MVP 之后的增强：密码策略、指标、重试逻辑和嵌套组
