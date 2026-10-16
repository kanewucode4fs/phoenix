<a id="phoenix-smtp-development-server"></a>

# Phoenix SMTP 开发服务

一个简单的 SMTP 服务，用于在开发期间可视化查看和调试 Phoenix 发出的邮件。**不能用于生产环境。**

<a id="what-it-does"></a>

## 功能

- 捕获 Phoenix 在开发期间发送的邮件
- 提供 Web 界面查看邮件内容（HTML、文本、邮件头）
- 将邮件存储在内存中，便于调试
- 仅用于可视化查看，不实际投递邮件

<a id="quick-start"></a>

## 快速开始

SMTP 服务随 Phoenix 开发环境自动运行：

```bash
# Start Phoenix dev environment (includes SMTP server)
tox r -e docker_devops

# View emails at:
# http://localhost:18273/mail
```

<a id="how-to-use"></a>

## 使用方法

1. **启动开发环境**：SMTP 服务会自动启动
2. **在 Phoenix 中触发邮件**：使用应用的邮件功能
3. **查看邮件**：访问 http://localhost:18273/mail
4. **调试邮件内容**：查看 Phoenix 实际发送的内容

<a id="email-viewing"></a>

## 邮件查看方式

- **HTML 视图**：查看渲染后的邮件
- **文本视图**：查看纯文本内容
- **原始视图**：以 JSON 查看完整邮件数据
- **邮件头视图**：查看 SMTP 头和元数据

<a id="configuration"></a>

## 配置

服务使用以下默认值（在 Phoenix 开发环境中配置）：

- **SMTP 端口**：1025（Phoenix 向此端口发送邮件）
- **Web 端口**：8025（通过 Traefik 在 `/mail` 提供访问）
- **存储**：内存（重启后邮件清空）
- **最大邮件数**：1000（自动删除最早的邮件）

<a id="troubleshooting"></a>

## 故障排查

**没有显示邮件时：**

- 检查 Phoenix 是否配置为向 `localhost:1025` 发送邮件
- 确认开发环境正在运行
- 检查浏览器控制台是否报错

**无法访问 Web 界面时：**

- 确认使用 http://localhost:18273/mail 访问（不要直接访问 8025 端口）
- 确认开发环境中的 Traefik 路由正常

此工具有意保持简单，专注于 Phoenix 开发期间的邮件调试。
