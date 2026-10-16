<a id="phoenix-helm"></a>

# Phoenix Helm 部署

![版本： 12.0.23](https://img.shields.io/badge/Version-12.0.23-informational?style=flat-square) ![类型：应用](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![应用版本： 20.23.0](https://img.shields.io/badge/AppVersion-20.23.0-informational?style=flat-square)

<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=helm/README.md" />

Phoenix 是面向实验、评估和故障排查的开源 AI 可观测平台。此 Helm chart 的部署方法见[自行部署文档](https://arize.com/docs/phoenix/self-hosting)。
  - [**_追踪_**](https://arize.com/docs/phoenix/tracing/llm-traces) - 基于 OpenTelemetry 插桩，追踪 LLM 应用的运行过程。
  - [**_评估_**](https://arize.com/docs/phoenix/evaluation/llm-evals) - 使用 LLM，通过回答和检索评估衡量应用表现。
  - [**_数据集_**](https://arize.com/docs/phoenix/datasets-and-experiments/overview-datasets) - 创建带版本的示例数据集，用于实验、评估和微调。
  - [**_实验_**](https://arize.com/docs/phoenix/datasets-and-experiments/overview-datasets#experiments) - 跟踪并评估提示词、LLM 和检索的改动。
  - [**_Playground 试验台_**](https://arize.com/docs/phoenix/prompt-engineering/overview-prompts) - 优化提示词、比较模型、调整参数，并重放已追踪的 LLM 调用。
  - [**_提示词管理_**](https://arize.com/docs/phoenix/prompt-engineering/overview-prompts/prompt-management) - 通过版本控制、标签和实验，系统管理并测试提示词改动。

**主页：** <https://phoenix.arize.com/>

<a id="maintainers"></a>

## 维护者

| 名称 | 邮箱 | URL |
| ---- | ------ | --- |
| arize | <phoenix-devs@arize.com> | <https://phoenix.arize.com/> |

<a id="source-code"></a>

## 源代码

* <https://github.com/Arize-ai/phoenix>

<a id="requirements"></a>

## 依赖要求

| 仓库 | 名称 | 版本 |
|------------|------|---------|
| https://groundhog2k.github.io/helm-charts/ | postgresql(postgres) | 1.5.8 |

<a id="values"></a>

## 配置值

| 配置键 | 类型 | 默认值 | 说明 |
|-----|------|---------|-------------|
| additionalEnv | list | `[]` | 添加到部署 Pod 规格中的额外环境变量。支持的变量见 https://arize.com/docs/phoenix/self-hosting/configuration#environment-variables 。仅用于 Helm chart 未直接暴露的能力。 |
| auth.accessTokenExpiryMinutes | int | `60` | 访问令牌过期并需要续期前的有效时长，单位为分钟。（PHOENIX_ACCESS_TOKEN_EXPIRY_MINUTES） |
| auth.admins | string | `""` | 启动时创建为管理员的用户名与邮箱对，以分号分隔。格式："username=email;username2=email2"，例如 "John Doe=john@example.com;Jane Doe=jane@example.com"。这些用户将获得随机密码，首次登录时必须重置。（PHOENIX_ADMINS） |
| auth.allowedOrigins | list | `[]` | 允许跨域请求 Phoenix API 的 CORS 来源列表。（PHOENIX_ALLOWED_ORIGINS） |
| auth.bruteForceLoginProtectionMaxAttempts | int | `5` | 临时锁定前允许的最大登录失败次数。仅在启用暴力破解防护时生效，锁定时长为 5 分钟。（PHOENIX_BRUTE_FORCE_LOGIN_PROTECTION_MAX_ATTEMPTS） |
| auth.cookiesPath | string | `"/"` | 认证 Cookie 的路径。Phoenix 部署在子路径下时需要设置。（PHOENIX_COOKIES_PATH） |
| auth.createSecret | bool | `true` | 是否创建 Secret 的布尔开关。为 False 且启用认证时，Secret 必须预先存在。 |
| auth.csrfTrustedOrigins | list | `[]` | CSRF 防护使用的可信来源列表，用于防止跨站请求伪造。（PHOENIX_CSRF_TRUSTED_ORIGINS） |
| auth.defaultAdminPassword | string | `"admin"` | 首次配置时管理员用户的默认密码。（PHOENIX_DEFAULT_ADMIN_INITIAL_PASSWORD） |
| auth.disableBasicAuth | bool | `false` | 禁用基于密码的认证。为 true 时，用户只能通过 OAuth2/OIDC 认证，适用于仅使用 SSO 的部署。（PHOENIX_DISABLE_BASIC_AUTH） |
| auth.disableBruteForceLoginProtection | bool | `false` | 禁用暴力破解防护。为 false（默认）时，连续登录失败会暂时锁定账户。（PHOENIX_DISABLE_BRUTE_FORCE_LOGIN_PROTECTION） |
| auth.enableAuth | bool | `true` | 启用 Phoenix 身份认证与授权。（PHOENIX_ENABLE_AUTH） |
| auth.enableStrongPasswordPolicy | bool | `false` | 启用强密码策略：至少 12 个字符，且包含大写字母、小写字母、数字和特殊字符。（PHOENIX_ENABLE_STRONG_PASSWORD_POLICY） |
| auth.ldap.allowSignUp | bool | `true` | 首次 LDAP 登录时允许自动创建用户。设为 false 则要求预先配置用户。 |
| auth.ldap.attrDisplayName | string | `"displayName"` | 包含用户显示名称的 LDAP 属性。 |
| auth.ldap.attrEmail | string | `"mail"` | 包含用户邮箱地址的 LDAP 属性。有效值："mail"（或其他属性名）表示使用该 LDAP 属性作为邮箱；"null" 表示用于没有邮箱的目录的无邮箱模式。使用无邮箱模式（"null"）时：必须设置 attrUniqueId（按唯一 ID 而非邮箱识别用户）；allowSignUp 必须为 true（首次登录时自动配置用户）；不能使用 auth.admins（应通过 groupRoleMappings 分配管理员）。 |
| auth.ldap.attrMemberOf | string | `"memberOf"` | 包含组成员关系的 LDAP 属性（默认为 "memberOf"）。未设置 groupSearchFilter 时使用（Active Directory 模式）。典型值为 "memberOf"（AD、启用 memberOf overlay 的 OpenLDAP）。 |
| auth.ldap.attrUniqueId | string | `""` | 包含不可变唯一标识符的 LDAP 属性。attrEmail 为 "null"（无邮箱模式）时必填。如果用户邮箱可能频繁变化，也建议设置。Active Directory："objectGUID"；OpenLDAP："entryUUID"；389 DS："nsUniqueId"。 |
| auth.ldap.bindDn | string | `""` | 用于绑定 LDAP 服务的服务账户 DN。例如："CN=svc-phoenix,OU=Service Accounts,DC=corp,DC=com"。 |
| auth.ldap.bindPassword | string | `""` | 用于绑定 LDAP 服务的服务账户密码。可直接在此设置，也可通过 auth.secret 中的 PHOENIX_LDAP_BIND_PASSWORD 键设置。 |
| auth.ldap.enabled | bool | `false` | 启用 LDAP 认证。 |
| auth.ldap.groupRoleMappings | string | `"[]"` | 将 LDAP 组映射到 Phoenix 角色的 JSON 数组。格式：[{"group_dn": "CN=Phoenix Admins,OU=Groups,DC=corp,DC=com", "role": "ADMIN"}]。支持 "ADMIN"、"MEMBER"、"VIEWER"（不区分大小写）。特殊 group_dn 值 "*" 匹配所有用户（默认角色通配符）。 |
| auth.ldap.groupSearchBaseDns | list | `[]` | 组搜索的基础 DN 列表，设置 groupSearchFilter 时必填。例如：["ou=groups,dc=example,dc=com"]；多个 DN：["ou=groups,dc=corp,dc=com", "ou=teams,dc=corp,dc=com"]。 |
| auth.ldap.groupSearchFilter | string | `""` | 查找组的 LDAP 筛选器，使用 %s 作为用户标识符占位符。两种模式：AD 模式（不设置，推荐用于 Active Directory）从用户条目读取 memberOf；搜索模式（设置后）搜索包含该用户的组。POSIX 示例："(&(objectClass=posixGroup)(memberUid=%s))"。 |
| auth.ldap.groupSearchFilterUserAttr | string | `""` | 从用户条目中读取、用于替换 groupSearchFilter 中 %s 的 LDAP 属性。设置后读取用户 LDAP 条目的指定属性；未设置时（默认）直接使用登录用户名。组类型说明：POSIX（memberUid）包含 "jdoe" 这样的用户名，应使用默认值或 "uid"；groupOfNames（member）包含完整 DN，应使用 "distinguishedName"（仅 AD）。注意：OpenLDAP 不将 DN 暴露为属性；OpenLDAP 的 groupOfNames 应改用 memberOf overlay（AD 模式）。 |
| auth.ldap.host | string | `""` | LDAP 服务主机名，启用时必填。多个主机以逗号分隔以支持故障切换，例如 "ldap.corp.com" 或 "dc1.corp.com,dc2.corp.com,dc3.corp.com"。 |
| auth.ldap.port | string | `""` | LDAP 服务端口。StartTLS 默认为 389，LDAPS 默认为 636。 |
| auth.ldap.tlsCaCertFile | string | `""` | TLS 验证使用的自定义 CA 证书文件路径（PEM 格式）。LDAP 服务使用未纳入系统信任库的私有或内部 CA 时使用。 |
| auth.ldap.tlsClientCertFile | string | `""` | 双向 TLS 认证使用的客户端证书文件路径（PEM 格式），还必须设置 tlsClientKeyFile。 |
| auth.ldap.tlsClientKeyFile | string | `""` | 双向 TLS 认证使用的客户端私钥文件路径（PEM 格式），还必须设置 tlsClientCertFile。 |
| auth.ldap.tlsMode | string | `"starttls"` | TLS 连接模式："starttls"、"ldaps" 或 "none"。starttls 在 389 端口从明文升级为 TLS（推荐）；ldaps 在 636 端口从连接建立时就使用 TLS；none 不加密（仅用于测试，凭证明文传输）。 |
| auth.ldap.tlsVerify | bool | `true` | 验证 TLS 证书。生产环境应始终为 true。 |
| auth.ldap.userSearchBaseDns | list | `[]` | 用户搜索的基础 DN 列表，启用时必填，按顺序搜索。例如：["OU=Users,DC=corp,DC=com"]；多个 DN：["OU=Employees,DC=corp,DC=com", "OU=Contractors,DC=corp,DC=com"]。 |
| auth.ldap.userSearchFilter | string | `"(&(objectClass=user)(sAMAccountName=%s))"` | 查找用户的 LDAP 筛选器，使用 %s 作为用户名占位符。Active Directory 默认值："(&(objectClass=user)(sAMAccountName=%s))"；OpenLDAP 示例："(&(objectClass=inetOrgPerson)(uid=%s))"。 |
| auth.name | string | `"phoenix-secret"` | 包含认证凭证的 Kubernetes Secret 名称。 |
| auth.oauth2.enabled | bool | `false` | 启用 OAuth2/OIDC 认证。 |
| auth.oauth2.providers | string | `nil` | 要配置的 OAuth2 身份提供方列表。每项需要 client_id、client_secret（token_endpoint_auth_method="none" 或 "client_assertion_jwt" 时除外）及 oidc_config_url。也可通过 auth.secrets[].valueFrom 定义对应环境变量以使用现有 Secret。变量格式：PHOENIX_OAUTH2_{{ $provider_upper }}_{{ setting }}，例如 PHOENIX_OAUTH2_GOOGLE_CLIENT_SECRET。 |
| auth.oauth2AuthorizationServer.allowedRedirectHosts | list | `[]` | 允许动态注册 OAuth2 客户端使用的 HTTPS 重定向主机列表。为空且 dynamicClientRegistration 为 "enabled" 时，接受所有 HTTPS 重定向主机；设置后将 HTTPS 重定向限制到指定主机。始终允许回环重定向 URI。例如：["app.example.com"]。（PHOENIX_OAUTH2_ALLOWED_REDIRECT_HOSTS） |
| auth.oauth2AuthorizationServer.consentOriginCheck | string | `"strict"` | OAuth2 授权同意端点的 Origin 请求头检查模式。有效值："strict"（拒绝来自不可信来源的同意决定）或 "off"。（PHOENIX_OAUTH2_CONSENT_ORIGIN_CHECK） |
| auth.oauth2AuthorizationServer.dcrRateLimitPerHour | int | `10` | 动态 OAuth2 客户端注册的每 IP 每小时速率限制。（PHOENIX_OAUTH2_DCR_RATE_LIMIT_PER_HOUR） |
| auth.oauth2AuthorizationServer.dynamicClientRegistration | string | `"enabled"` | 动态客户端注册模式。有效值："disabled"、"local_only"（仅允许回环重定向 URI）或 "enabled"。（PHOENIX_OAUTH2_DYNAMIC_CLIENT_REGISTRATION） |
| auth.oauth2AuthorizationServer.enabled | bool | `true` | 提供内置 OAuth2 授权服务器。（PHOENIX_ENABLE_OAUTH2_AUTHORIZATION_SERVER） |
| auth.oauth2AuthorizationServer.grantExpiryDays | int | `90` | 新签发 OAuth2 授权的有效期上限，单位为天。（PHOENIX_OAUTH2_GRANT_EXPIRY_DAYS） |
| auth.passwordResetTokenExpiryMinutes | int | `60` | 密码重置令牌过期前的有效时长，单位为分钟。（PHOENIX_PASSWORD_RESET_TOKEN_EXPIRY_MINUTES） |
| auth.refreshTokenExpiryMinutes | int | `43200` | 刷新令牌过期前的有效时长，单位为分钟。（PHOENIX_REFRESH_TOKEN_EXPIRY_MINUTES） |
| auth.secret[0] | object | `{"key":"PHOENIX_SECRET","value":""}` | 用于加密的 Phoenix 主密钥对应的环境变量名称。 |
| auth.secret[0].value | string | `""` | 为空时自动生成。 |
| auth.secret[1] | object | `{"key":"PHOENIX_ADMIN_SECRET","value":""}` | 管理员密钥对应的环境变量名称。 |
| auth.secret[1].value | string | `""` | 为空时自动生成。 |
| auth.secret[2] | object | `{"key":"PHOENIX_POSTGRES_PASSWORD","value":"postgres"}` | PostgreSQL 密码对应的环境变量名称。 |
| auth.secret[2].value | string | `"postgres"` | 使用本 chart 的 PostgreSQL 时，密码必须与 database.postgres.password 一致。 |
| auth.secret[3] | object | `{"key":"PHOENIX_SMTP_PASSWORD","value":""}` | SMTP 密码对应的环境变量名称。 |
| auth.secret[3].value | string | `""` | 为空时自动生成。 |
| auth.secret[4] | object | `{"key":"PHOENIX_DEFAULT_ADMIN_INITIAL_PASSWORD","value":""}` | 默认管理员密码对应的环境变量名称。 |
| auth.secret[4].value | string | `""` | 首次配置时管理员用户的默认密码；为空则使用 defaultAdminPassword。 |
| auth.useSecureCookies | bool | `false` | 启用安全 Cookie（使用 HTTPS 时应为 true）。 |
| database.allocatedStorageGiB | int | `20` | 数据库持久卷的存储分配量，单位为 GiB。 |
| database.defaultRetentionPolicyDays | int | `0` | 追踪记录的默认保留天数。设为 0 可禁用自动清理；为正数时，数据库中早于该天数的追踪记录会被自动删除。（PHOENIX_DEFAULT_RETENTION_POLICY_DAYS） |
| database.postgres.azureScope | string | `""` | 请求 PostgreSQL 访问令牌的 Azure scope URL。为空时，Phoenix 使用 Azure Database for PostgreSQL - Flexible Server 默认 scope（https://ossrdbms-aad.database.windows.net/.default）。Azure Government 等主权云可覆盖为相应地址（https://ossrdbms-aad.database.usgovcloudapi.net/.default）。仅 useAzureManagedIdentity 为 true 时使用。（PHOENIX_POSTGRES_AZURE_SCOPE） |
| database.postgres.db | string | `"phoenix"` | PostgreSQL 数据库名称。（PHOENIX_POSTGRES_DB） |
| database.postgres.host | string | `""` | PostgreSQL 主机。postgresql.enabled=true 时默认指向 groundhog2k PostgreSQL 服务。重要：仅在使用外部 PostgreSQL（postgresql.enabled=false 且 database.url 为空）时修改。例如："localhost"、"postgres.example.com"、"your-rds-endpoint.region.rds.amazonaws.com"。（PHOENIX_POSTGRES_HOST） |
| database.postgres.password | string | `"postgres"` | PostgreSQL 密码（应与 auth.secret."PHOENIX_POSTGRES_PASSWORD" 一致）。 |
| database.postgres.port | int | `5432` | PostgreSQL 连接端口。（PHOENIX_POSTGRES_PORT） |
| database.postgres.schema | string | `""` | 使用的 PostgreSQL 模式。为空时 chart 不设置此环境变量，Phoenix 使用默认模式（通常为 public）。（PHOENIX_SQL_DATABASE_SCHEMA） |
| database.postgres.useAwsIamAuth | bool | `false` | 启用 PostgreSQL 的 AWS RDS IAM 认证。启用后，Phoenix 使用 AWS IAM 凭证生成短期认证令牌，代替静态密码。需要安装 aioboto3：pip install 'arize-phoenix[aws]'。重要：启用时不要设置 database.postgres.password。（PHOENIX_POSTGRES_USE_AWS_IAM_AUTH） |
| database.postgres.useAzureManagedIdentity | bool | `false` | 启用 PostgreSQL 的 Azure 托管身份认证。启用后，Phoenix 使用 Azure DefaultAzureCredential 获取短期认证令牌，代替静态密码。需要安装 azure-identity：pip install 'arize-phoenix[azure]'。不能与 useAwsIamAuth 同时使用。重要：启用时不要设置 database.postgres.password。（PHOENIX_POSTGRES_USE_AZURE_MANAGED_IDENTITY） |
| database.postgres.user | string | `"postgres"` | PostgreSQL 用户名。（PHOENIX_POSTGRES_USER） |
| database.readReplicaUrl | string | `""` | 可选的 PostgreSQL 只读副本 URL，用于只读查询路由。设置后，Phoenix 将只读查询路由至副本，写入仍发送到主库。SQLite 部署忽略此设置。（PHOENIX_SQL_DATABASE_READ_REPLICA_URL） |
| database.url | string | `""` | 完整数据库连接 URL，设置后覆盖 postgres 配置。重要：仅用于外部数据库（策略 3）。SQLite（策略 1）时必须为空，自动使用持久卷；内置 PostgreSQL（策略 2）时必须为空，由系统自动配置；外部数据库（策略 3）时必须提供完整连接串。外部数据库示例：PostgreSQL 为 "postgresql://username:password@your-rds-endpoint.region.rds.amazonaws.com:5432/phoenix"；SQLite 为 "sqlite:///path/to/database.db"（仅限外部 SQLite 文件，不推荐）。警告：此设置会覆盖所有 database.postgres.* 配置，并禁用内置 PostgreSQL 验证。 |
| deployment.affinity | object | `{}` |  |
| deployment.nodeSelector | object | `{}` |  |
| deployment.podLabels | object | `{}` | Phoenix Pod 的额外标签。按 Pod 标签筛选的准入 Webhook 需要这些标签，例如 OAuth2 工作负载身份使用的 `azure.workload.identity/use: "true"`。 |
| deployment.strategy | object | `{"rollingUpdate":{"maxSurge":"25%","maxUnavailable":"25%"},"type":"RollingUpdate"}` | 部署策略。 |
| deployment.terminationGracePeriodSeconds | int | `90` | 关闭期间 Kubernetes 允许 Phoenix 等待进行中工作完成的秒数。 |
| deployment.tolerations | list | `[]` | Pod 在节点上的调度策略，包括 tolerations、nodeSelector 和 affinity。 |
| extraVolumeMounts | list | `[]` | 额外卷挂载。 |
| extraVolumes | list | `[]` | 额外卷配置。 |
| healthChecks | object | `{"livenessProbe":{"failureThreshold":3,"initialDelaySeconds":0,"periodSeconds":10,"successThreshold":1,"timeoutSeconds":5},"readinessProbe":{"failureThreshold":3,"initialDelaySeconds":0,"periodSeconds":5,"successThreshold":1,"timeoutSeconds":3},"startupProbe":{"enabled":true,"failureThreshold":30,"initialDelaySeconds":1,"periodSeconds":1,"successThreshold":1,"timeoutSeconds":1}}` | 健康检查配置。 |
| healthChecks.livenessProbe | object | `{"failureThreshold":3,"initialDelaySeconds":0,"periodSeconds":10,"successThreshold":1,"timeoutSeconds":5}` | 存活探针配置。 |
| healthChecks.livenessProbe.failureThreshold | int | `3` | 重启容器前允许的失败次数。 |
| healthChecks.livenessProbe.initialDelaySeconds | int | `0` | 存活探针开始前的初始延迟。 |
| healthChecks.livenessProbe.periodSeconds | int | `10` | 执行存活探针的频率。 |
| healthChecks.livenessProbe.successThreshold | int | `1` | 将探针视为成功所需的连续成功次数。 |
| healthChecks.livenessProbe.timeoutSeconds | int | `5` | 存活探针超时时间。 |
| healthChecks.readinessProbe | object | `{"failureThreshold":3,"initialDelaySeconds":0,"periodSeconds":5,"successThreshold":1,"timeoutSeconds":3}` | 就绪探针配置。 |
| healthChecks.readinessProbe.failureThreshold | int | `3` | 将 Pod 标记为未就绪前允许的失败次数。 |
| healthChecks.readinessProbe.initialDelaySeconds | int | `0` | 就绪探针开始前的初始延迟。 |
| healthChecks.readinessProbe.periodSeconds | int | `5` | 执行就绪探针的频率。 |
| healthChecks.readinessProbe.successThreshold | int | `1` | 将探针视为成功所需的连续成功次数。 |
| healthChecks.readinessProbe.timeoutSeconds | int | `3` | 就绪探针超时时间。 |
| healthChecks.startupProbe | object | `{"enabled":true,"failureThreshold":30,"initialDelaySeconds":1,"periodSeconds":1,"successThreshold":1,"timeoutSeconds":1}` | 启动探针配置。 |
| healthChecks.startupProbe.enabled | bool | `true` | 启用启动探针。 |
| healthChecks.startupProbe.failureThreshold | int | `30` | 将容器视为启动失败前允许的失败次数。 |
| healthChecks.startupProbe.initialDelaySeconds | int | `1` | 启动探针开始前的初始延迟。 |
| healthChecks.startupProbe.periodSeconds | int | `1` | 执行启动探针的频率。 |
| healthChecks.startupProbe.successThreshold | int | `1` | 将探针视为成功所需的连续成功次数。 |
| healthChecks.startupProbe.timeoutSeconds | int | `1` | 启动探针超时时间。 |
| image.pullPolicy | string | `"IfNotPresent"` | Phoenix 容器的镜像拉取策略（Always、IfNotPresent 或 Never）。 |
| image.registry | string | `"docker.io"` | Phoenix 的 Docker 镜像注册表。 |
| image.repository | string | `"arizephoenix/phoenix"` | Phoenix 的 Docker 镜像仓库。 |
| image.tag | string | `"version-20.23.0-nonroot"` | 要部署的 Docker 镜像标签或版本。 |
| ingress.annotations | object | `{}` | 添加到 Ingress 资源的注解。 |
| ingress.apiPath | string | `"/"` | Phoenix API 的路径前缀。 |
| ingress.enabled | bool | `true` | 启用 Ingress 控制器以允许外部访问。 |
| ingress.host | string | `""` | Ingress 主机名。 |
| ingress.labels | object | `{}` | 添加到 Ingress 资源的标签。 |
| ingress.pathType | string | `"Prefix"` | Ingress 路径类型（Prefix、Exact 或 ImplementationSpecific）。 |
| ingress.tls.enabled | bool | `false` | 为 Ingress 启用 TLS/HTTPS。 |
| instrumentation.otlpTraceCollectorGrpcEndpoint | string | `""` | 用于发送追踪记录的 OpenTelemetry 收集器 gRPC 端点。（PHOENIX_SERVER_INSTRUMENTATION_OTLP_TRACE_COLLECTOR_GRPC_ENDPOINT） |
| instrumentation.otlpTraceCollectorHttpEndpoint | string | `""` | 用于发送追踪记录的 OpenTelemetry 收集器 HTTP 端点。（PHOENIX_SERVER_INSTRUMENTATION_OTLP_TRACE_COLLECTOR_HTTP_ENDPOINT） |
| logging.dbLevel | string | `"warning"` | 数据库日志级别（debug、info、warning、error）。（PHOENIX_DB_LOGGING_LEVEL） |
| logging.level | string | `"info"` | 应用日志级别（debug、info、warning、error）。（PHOENIX_LOGGING_LEVEL） |
| logging.logMigrations | bool | `true` | 启用数据库迁移操作日志。（PHOENIX_LOG_MIGRATIONS） |
| logging.logSql | bool | `false` | 将所有 SQL 语句记录到标准输出以便调试。（PHOENIX_LOG_SQL） |
| logging.mode | string | `"default"` | 日志模式配置：default|structured。（PHOENIX_LOGGING_MODE） |
| persistence.accessModes | list | `["ReadWriteOnce"]` | 持久卷的访问模式。 |
| persistence.annotations | object | `{}` | 添加到 PVC 的注解。 |
| persistence.enabled | bool | `false` | 为 Phoenix 主目录启用持久存储。启用时，Phoenix 使用存放在持久卷上的 SQLite 本地存储。重要：不能与 postgresql.enabled=true 同时启用。注意：database.url="sqlite:///:memory:"（内存数据库）时忽略此设置。请选择一种持久化策略：SQLite 使用 persistence.enabled=true、postgresql.enabled=false；SQLite 内存模式使用 persistence.inMemory=true、postgresql.enabled=false；groundhog2k PostgreSQL 使用 persistence.enabled=false、postgresql.enabled=true；外部数据库使用 persistence.enabled=false、postgresql.enabled=false，并配置 database.url。 |
| persistence.inMemory | bool | `false` | 启用 SQLite 策略的内存模式配置。 |
| persistence.labels | object | `{}` | 添加到 PVC 的标签。 |
| persistence.size | string | `"20Gi"` | Phoenix 主目录持久卷的大小。 |
| persistence.storageClass | string | `""` | Phoenix 主目录卷的 Kubernetes 存储类。 |
| postgresql.enabled | bool | `true` | 启用 PostgreSQL 部署。已有 PostgreSQL 实例（如 RDS、CloudSQL）时设为 false。禁用时必须配置 database.url 或 database.postgres，使其指向外部数据库。重要：不能与 persistence.enabled=true（SQLite）同时启用。请选择一种策略：groundhog2k PostgreSQL 使用 postgresql.enabled=true、persistence.enabled=false；SQLite 使用 postgresql.enabled=false、persistence.enabled=true；外部数据库使用 postgresql.enabled=false、persistence.enabled=false，并配置 database.url。 |
| postgresql.image.registry | string | `"docker.io"` |  |
| postgresql.image.repository | string | `"postgres"` |  |
| postgresql.image.tag | string | `"16"` |  |
| postgresql.podSecurityContext | object | `{"fsGroup":999,"supplementalGroups":[999]}` | PostgreSQL 容器的安全上下文。 |
| postgresql.resources | object | `{"limits":{"cpu":"500m","memory":"512Mi"},"requests":{"cpu":"100m","memory":"256Mi"}}` | 资源限制。 |
| postgresql.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| postgresql.securityContext.privileged | bool | `false` |  |
| postgresql.securityContext.readOnlyRootFilesystem | bool | `true` |  |
| postgresql.securityContext.runAsGroup | int | `999` |  |
| postgresql.securityContext.runAsNonRoot | bool | `true` |  |
| postgresql.securityContext.runAsUser | int | `999` |  |
| postgresql.service | object | `{"port":5432,"type":"ClusterIP"}` | 服务配置。 |
| postgresql.settings | object | `{"superuserPassword":{"value":"postgres"}}` | 数据库设置。 |
| postgresql.storage | object | `{"accessModes":["ReadWriteOnce"],"requestedSize":"20Gi"}` | 存储配置。 |
| postgresql.userDatabase | object | `{"name":{"value":"phoenix"},"password":{"value":"phoenix"},"user":{"value":"phoenix"}}` | 用户数据库配置。 |
| replicaCount | int | `1` | Phoenix Pod 的副本数。 |
| resources | object | `{"limits":{"cpu":"1000m","memory":"2Gi"},"requests":{"cpu":"500m","memory":"1Gi"}}` | 资源配置。 |
| sandbox.allowedProviders | string | `""` | 以逗号分隔的沙箱供应商允许列表。支持 WASM、E2B、DAYTONA、VERCEL、DENO、MODAL、MONTY、DOCKER（不区分大小写）。为空时 chart 不设置环境变量，允许所有供应商。设为 "NONE" 可禁用全部沙箱供应商。例如："WASM,DENO"。（PHOENIX_ALLOWED_SANDBOX_PROVIDERS） |
| securityContext | object | `{"container":{"allowPrivilegeEscalation":false,"capabilities":{"add":[],"drop":["ALL"]},"enabled":false,"privileged":false,"procMount":"Default","readOnlyRootFilesystem":true,"runAsGroup":65532,"runAsNonRoot":true,"runAsUser":65532,"seLinuxOptions":{},"seccompProfile":{"type":"RuntimeDefault"},"windowsOptions":{}},"pod":{"enabled":false,"fsGroup":65532,"fsGroupChangePolicy":"OnRootMismatch","runAsGroup":65532,"runAsNonRoot":true,"runAsUser":65532,"seLinuxOptions":{},"seccompProfile":{"type":"RuntimeDefault"},"supplementalGroups":[],"sysctls":[],"windowsOptions":{}}}` | 安全上下文配置。 |
| securityContext.container | object | `{"allowPrivilegeEscalation":false,"capabilities":{"add":[],"drop":["ALL"]},"enabled":false,"privileged":false,"procMount":"Default","readOnlyRootFilesystem":true,"runAsGroup":65532,"runAsNonRoot":true,"runAsUser":65532,"seLinuxOptions":{},"seccompProfile":{"type":"RuntimeDefault"},"windowsOptions":{}}` | 容器级安全上下文设置。 |
| securityContext.pod | object | `{"enabled":false,"fsGroup":65532,"fsGroupChangePolicy":"OnRootMismatch","runAsGroup":65532,"runAsNonRoot":true,"runAsUser":65532,"seLinuxOptions":{},"seccompProfile":{"type":"RuntimeDefault"},"supplementalGroups":[],"sysctls":[],"windowsOptions":{}}` | Pod 级安全上下文设置。 |
| server.allowExternalResources | bool | `true` | 允许调用外部资源，如 Web 界面中的 Google Fonts。隔离网络环境应设为 false，避免外部请求导致界面加载延迟。（PHOENIX_ALLOW_EXTERNAL_RESOURCES） |
| server.allowedProviders | string | `""` | 在 Playground 界面显示的模型供应商名称列表，以逗号分隔。未设置时显示全部供应商。设为 "NONE" 可隐藏全部供应商。支持：OPENAI、ANTHROPIC、AZURE_OPENAI、GOOGLE、DEEPSEEK、XAI、OLLAMA、AWS、CEREBRAS、FIREWORKS、GROQ、MOONSHOT、MINIMAX、PERPLEXITY、TOGETHER、ZAI、META。例如："OPENAI,ANTHROPIC"。（PHOENIX_ALLOWED_PROVIDERS） |
| server.annotations | object | `{}` | 添加到 Phoenix 服务的注解。 |
| server.enableMcpCodeMode | bool | `true` | 为内置 MCP 服务启用代码模式，通过代码执行接口暴露工具。仅启用 MCP 服务时生效。（PHOENIX_ENABLE_MCP_CODE_MODE） |
| server.enableMcpServer | bool | `true` | 提供内置 MCP 服务。（PHOENIX_ENABLE_MCP_SERVER） |
| server.enablePrometheus | bool | `false` | 在 9090 端口启用 Prometheus 指标端点。 |
| server.grpcPort | int | `4317` | OpenTelemetry gRPC 收集器端口。（PHOENIX_GRPC_PORT） |
| server.host | string | `"::"` | Phoenix 服务绑定的主机 IP。（PHOENIX_HOST） |
| server.hostRootPath | string | `""` | Phoenix 界面与 API 的根路径前缀。（PHOENIX_HOST_ROOT_PATH） |
| server.labels | object | `{}` | 添加到 Phoenix 服务的标签。 |
| server.maxSpansQueueSize | int | `20000` | 处理队列中可容纳的最大跨度数，超过后拒绝新请求。此启发式限制用于避免跨度积累速度超过写入数据库速度时出现内存问题。每个跨度约占 50KiB，因此 20,000 个跨度约为 1GiB。应根据可用内存和数据库吞吐量调整。（PHOENIX_MAX_SPANS_QUEUE_SIZE） |
| server.port | int | `6006` | Phoenix Web 界面和 HTTP API 的端口。（PHOENIX_PORT） |
| server.rootUrl | string | `""` | Phoenix 的外部根 URL。（PHOENIX_ROOT_URL） |
| server.telemetryEnabled | bool | `true` | 启用用于分析跟踪的遥测。设为 false 时禁用 Phoenix 中全部分析跟踪。（PHOENIX_TELEMETRY_ENABLED） |
| server.workingDir | string | `"/data"` | 保存、加载和导出数据的工作目录。设为空字符串会使用容器的 $HOME 目录（不建议用于持久化）。卷挂载默认使用 `/data`，以便在严格和普通安全上下文中都有正确权限。重要：persistence.enabled=true 时，此目录必须允许 Phoenix 容器（UID 65532）写入。启用 securityContext.pod 中的 fsGroup 设置可确保权限正确。（PHOENIX_WORKING_DIR） |
| service.annotations | object | `{}` | 添加到 Phoenix 服务的注解（适用于服务网格配置）。 |
| service.labels | object | `{}` | 添加到 Phoenix 服务的标签。 |
| service.type | string | `"NodePort"` | Phoenix 服务类型（ClusterIP、NodePort、LoadBalancer 或 ExternalName）。服务网格部署（Istio、Linkerd 等）使用 ClusterIP；不经过 Ingress 直接向外暴露时使用 NodePort。 |
| serviceAccount | object | `{"annotations":{},"create":false,"imagePullSecrets":[],"name":""}` | ServiceAccount 配置。 |
| serviceAccount.annotations | object | `{}` | 添加到 ServiceAccount 的注解。 |
| serviceAccount.create | bool | `false` | 为 Phoenix 创建 ServiceAccount。 |
| serviceAccount.imagePullSecrets | list | `[]` | 从私有注册表拉取镜像时使用的 Kubernetes Secret 列表。 |
| serviceAccount.name | string | `""` | 要使用的 ServiceAccount 名称。未设置且 create 为 true 时，根据发布名称生成名称；未设置且 create 为 false 时，使用默认 ServiceAccount。 |
| smtp.hostname | string | `""` | 发送邮件使用的 SMTP 服务主机名。（PHOENIX_SMTP_HOSTNAME） |
| smtp.mailFrom | string | `"noreply@arize.com"` | 系统邮件的发件人地址。（PHOENIX_SMTP_MAIL_FROM） |
| smtp.password | string | `""` | SMTP 认证密码。（PHOENIX_SMTP_PASSWORD） |
| smtp.port | int | `587` | SMTP 服务端口（TLS 通常使用 587）。（PHOENIX_SMTP_PORT） |
| smtp.username | string | `""` | SMTP 认证用户名。（PHOENIX_SMTP_USERNAME） |
| smtp.validateCerts | bool | `true` | 验证 SMTP 服务的 TLS 证书。（PHOENIX_SMTP_VALIDATE_CERTS） |
| tls.caFile | string | `""` | TLS CA 证书文件路径。（PHOENIX_TLS_CA_FILE） |
| tls.certFile | string | `""` | TLS 证书文件路径。（PHOENIX_TLS_CERT_FILE） |
| tls.enabled | bool | `false` | 为 Phoenix 服务启用 TLS。（PHOENIX_TLS_ENABLED） |
| tls.enabledForGrpc | bool | `false` | 为 gRPC 端点启用 TLS。（PHOENIX_TLS_ENABLED_FOR_GRPC） |
| tls.enabledForHttp | bool | `false` | 为 HTTP 端点启用 TLS。（PHOENIX_TLS_ENABLED_FOR_HTTP） |
| tls.keyFile | string | `""` | TLS 私钥文件路径。（PHOENIX_TLS_KEY_FILE） |
| tls.keyFilePassword | string | `""` | 加密 TLS 私钥的密码。（PHOENIX_TLS_KEY_FILE_PASSWORD） |
| tls.verifyClient | bool | `false` | 为双向 TLS 启用客户端证书验证。（PHOENIX_TLS_VERIFY_CLIENT） |

----------------------------------------------
使用 [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2) 根据 chart 元数据自动生成。
