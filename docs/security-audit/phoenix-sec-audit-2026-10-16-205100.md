# Phoenix 本次变更安全审计

审计日期：2026-10-16（北京时间）。触发方式：提交前自动执行 `sec-skill`。规则来源：`~/.codex/skills/sec-skill/references/security_rules.md`，R01–R27。审查人为当前 Codex 代理，非独立人工审计；未进行全工程安全审计。

## 范围与结论

范围共 10 个文件：`AGENTS.md`、`Dockerfile`、`docs/03-技术架构/全工程分析-2026-10-16.md`、`docs/03-技术架构/REA证据摘要-2026-10-16.json`、`docs/04-部署文档/源码Docker运行.md`，以及 `examples/langgraph_phoenix_demo/` 中的 `demo.py`、`test_demo.py`、`Makefile`、`requirements.txt`、`README.md`。本报告另作为审查记录提交。

| 指标 | 结果 |
|---|---|
| 核对规则 | 27 条，按变更是否涉及对应功能判断适用性 |
| 已发现违规 | 0：CRITICAL 0、HIGH 0、MEDIUM 0 |
| 结论 | 本次变更检查通过，未发现阻止提交的问题 |
| 依赖扫描 | pip-audit 2.9.0：`No known vulnerabilities found`，退出码 0 |

## 规则核对

| 规则 | 核对结果与边界 |
|---|---|
| R01、R02 | 未新增共享授权凭证或服务端业务接口；示例是本机 CLI。部署仅绑定主机回环地址，沿用本地关闭认证的配置，不作为公网部署方案。 |
| R03 | 未新增文件上传下载业务；分析文档、测试和 Docker 工作目录不属于业务文件管理接口。 |
| R04、R05 | 示例使用公开技术资料；配置文档仅含用户名／密码占位符，无真实 Key、密码、Token 或私钥。测试 Agent 路径是用户明确要求记录的本机路径。 |
| R06、R07 | CLI 输出属于演示结果，不是业务审计日志；文档明确问题与回答会进入终端和追踪，只使用非敏感演示数据。未增加身份或敏感业务操作。 |
| R08、R09 | 未新增个人敏感信息存储或前端脱敏逻辑；未改数据库加密／认证策略。 |
| R10、R11 | 未新增暴露自增主键的接口或全量数据接口。验证时按 Trace ID 过滤并限制 100 个 Span。 |
| R12、R13 | 新增代码无 SQL 拼接、HTML 渲染或动态脚本执行；本次 PostgreSQL 仅通过服务现有数据库层接入。 |
| R14 | 追踪地址来自操作者进程配置，不来自外部请求；示例没有 URL 代理、抓取或模型可调用的网络工具。 |
| R15、R16 | 未新增上传、Cookie 会话或状态变更 HTTP 接口。 |
| R17 | 4 个直接运行依赖使用稳定精确版本；隔离运行 pip-audit 扫描 requirements 及解析依赖，未发现已知漏洞；Docker 保留冻结锁文件及既有供应链校验。未扫描整个镜像和全仓依赖。 |
| R18 | 未新增面向客户端的错误返回；本地 CLI 错误显式抛出，未吞掉异常。 |
| R19、R20、R21、R22、R23 | 不涉及移动端代码、证书处理、WebView、组件导出或移动发布。 |
| R24、R25、R26 | 使用 FakeListChatModel，不调用外部模型、不需要模型密钥；固定 system 消息与用户问题分开，无 function calling、命令执行或生成代码执行。追踪记录输入输出，限定非敏感演示数据；接入真实模型后的风险不在本次保证范围。 |
| R27 | 已阅读新增代码、核对数据流与配置、执行依赖扫描及行为测试，并以本报告留档。 |

## 可核对的验证

- `make -C examples/langgraph_phoenix_demo test`：`test_demo.py` 共 4 项、通过 4、失败 0、跳过 0；Python 3.12.13、pytest 8.4.2，0.32 秒。场景包括 Phoenix 问答含“追踪／评测”、LangGraph 问答含“节点／状态”、未知问题明确无相关信息，以及真实框架埋点的单 Trace 连通性／单模型 Span／模型输入。
- `uv --no-config tool run --managed-python --python 3.12 --from pip-audit==2.9.0 pip-audit --requirement examples/langgraph_phoenix_demo/requirements.txt --progress-spinner off`：1 次扫描通过，无已知漏洞。
- UTF-8、尾空白、JSON 解析、89 个本地 Markdown 链接及常见 Key／私钥模式检查：10 个文件未发现问题；`git diff --check` 通过。这些静态检查不等同完整秘密检测或渗透测试。
- [部署验证记录](../04-部署文档/源码Docker运行.md)：8 项构建／运行检查通过，包含 PostgreSQL 直接入库和容器重启后 8 个 Span 保留。

仍有 3 条 LangChain 依赖弃用警告；未执行全仓测试、浏览器 E2E、真实模型调用、全镜像漏洞扫描或独立人工审查。截图错误未通过修改产品代码修复，当前项目 GraphQL 查询已实际返回 `FirstAgent` 且无 errors。
