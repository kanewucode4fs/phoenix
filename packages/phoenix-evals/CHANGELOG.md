<a id="changelog"></a>

# 更新日志

## [3.9.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.9.1...arize-phoenix-evals-v3.9.2) (2026-10-09)


<a id="bug-fixes"></a>

### 问题修复

* **evals:** 拒绝非有限的 precision、recall 和 beta ([#16226](https://github.com/Arize-ai/phoenix/issues/16226)) ([a944a14](https://github.com/Arize-ai/phoenix/commit/a944a14963cde37f6b9e6d75612f331d5506ad3e))

## [3.9.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.9.0...arize-phoenix-evals-v3.9.1) (2026-10-08)


<a id="bug-fixes-1"></a>

### 问题修复

* **evals:** SyncExecutor 遇到 RateLimitError 时重试，避免整次运行失败 ([#16376](https://github.com/Arize-ai/phoenix/issues/16376)) ([56e9a89](https://github.com/Arize-ai/phoenix/commit/56e9a8994e9074eb9958dfe77e4552e7a8b6d38c))

## [3.9.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.8.0...arize-phoenix-evals-v3.9.0) (2026-09-21)


<a id="features"></a>

### 新功能

* **evals:** 新增检索相关性评估器 ([#14766](https://github.com/Arize-ai/phoenix/issues/14766)) ([7efa7b2](https://github.com/Arize-ai/phoenix/commit/7efa7b21fc3284f0af928ddedda15927974ee94d))
* **evals:** 新增会话级 pii_detection 评估器  ([#15096](https://github.com/Arize-ai/phoenix/issues/15096)) ([0e3b2c2](https://github.com/Arize-ai/phoenix/commit/0e3b2c2ae55b671cdc523363ea18bcc7e6ae6c31))
* **evals:** 新增完整性评估器 ([#15767](https://github.com/Arize-ai/phoenix/issues/15767)) ([63805d0](https://github.com/Arize-ai/phoenix/commit/63805d0f13eb3c2cf5b55378abd542ca505e0d9a))
* **evals:** 弃用文档相关性评估器 ([#15991](https://github.com/Arize-ai/phoenix/issues/15991)) ([d67ea3f](https://github.com/Arize-ai/phoenix/commit/d67ea3fdaaa3df4c006c950e12e785f2bdc81960))


<a id="bug-fixes-2"></a>

### 问题修复

* **evals:** 允许 PromptTemplate 消息列表使用角色别名 ([#16002](https://github.com/Arize-ai/phoenix/issues/16002)) ([767847c](https://github.com/Arize-ai/phoenix/commit/767847c3386492f9783b623cf78e3eee47d0cea3))
* **evals:** 异步限流器使用非阻塞休眠 ([#15404](https://github.com/Arize-ai/phoenix/issues/15404)) ([2ecfd47](https://github.com/Arize-ai/phoenix/commit/2ecfd4788963ee2a01cb981b25baca4eb3372502))
* **evals:** 校验初始请求速率 ([#16227](https://github.com/Arize-ai/phoenix/issues/16227)) ([b8e5cf8](https://github.com/Arize-ai/phoenix/commit/b8e5cf846a45b4f34d0ad297188ddef8d87e973d))
* 升级至 anthropic SDK v1 ([#15588](https://github.com/Arize-ai/phoenix/issues/15588)) ([b28cf94](https://github.com/Arize-ai/phoenix/commit/b28cf94fcd37afeacfd059b4a01e7ad38327e483))

## [3.8.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.7.0...arize-phoenix-evals-v3.8.0) (2026-09-11)


<a id="features-1"></a>

### 新功能

* **evals:** 新增检索相关性评估器 ([#14766](https://github.com/Arize-ai/phoenix/issues/14766)) ([7efa7b2](https://github.com/Arize-ai/phoenix/commit/7efa7b21fc3284f0af928ddedda15927974ee94d))
* **evals:** 新增会话级 pii_detection 评估器  ([#15096](https://github.com/Arize-ai/phoenix/issues/15096)) ([0e3b2c2](https://github.com/Arize-ai/phoenix/commit/0e3b2c2ae55b671cdc523363ea18bcc7e6ae6c31))
* **evals:** 新增完整性评估器 ([#15767](https://github.com/Arize-ai/phoenix/issues/15767)) ([63805d0](https://github.com/Arize-ai/phoenix/commit/63805d0f13eb3c2cf5b55378abd542ca505e0d9a))
* **evals:** 弃用文档相关性评估器 ([#15991](https://github.com/Arize-ai/phoenix/issues/15991)) ([d67ea3f](https://github.com/Arize-ai/phoenix/commit/d67ea3fdaaa3df4c006c950e12e785f2bdc81960))


<a id="bug-fixes-3"></a>

### 问题修复

* **evals:** 异步限流器使用非阻塞休眠 ([#15404](https://github.com/Arize-ai/phoenix/issues/15404)) ([2ecfd47](https://github.com/Arize-ai/phoenix/commit/2ecfd4788963ee2a01cb981b25baca4eb3372502))
* 升级至 anthropic SDK v1 ([#15588](https://github.com/Arize-ai/phoenix/issues/15588)) ([b28cf94](https://github.com/Arize-ai/phoenix/commit/b28cf94fcd37afeacfd059b4a01e7ad38327e483))

## [3.7.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.6.0...arize-phoenix-evals-v3.7.0) (2026-09-10)


<a id="features-2"></a>

### 新功能

* **evals:** 新增完整性评估器 ([#15767](https://github.com/Arize-ai/phoenix/issues/15767)) ([63805d0](https://github.com/Arize-ai/phoenix/commit/63805d0f13eb3c2cf5b55378abd542ca505e0d9a))
* **evals:** 弃用文档相关性评估器 ([#15991](https://github.com/Arize-ai/phoenix/issues/15991)) ([d67ea3f](https://github.com/Arize-ai/phoenix/commit/d67ea3fdaaa3df4c006c950e12e785f2bdc81960))

## [3.6.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.5.1...arize-phoenix-evals-v3.6.0) (2026-09-01)


<a id="features-3"></a>

### 新功能

* **evals:** 新增会话级 pii_detection 评估器  ([#15096](https://github.com/Arize-ai/phoenix/issues/15096)) ([0e3b2c2](https://github.com/Arize-ai/phoenix/commit/0e3b2c2ae55b671cdc523363ea18bcc7e6ae6c31))


<a id="bug-fixes-4"></a>

### 问题修复

* **evals:** 异步限流器使用非阻塞休眠 ([#15404](https://github.com/Arize-ai/phoenix/issues/15404)) ([2ecfd47](https://github.com/Arize-ai/phoenix/commit/2ecfd4788963ee2a01cb981b25baca4eb3372502))

## [3.5.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.5.0...arize-phoenix-evals-v3.5.1) (2026-08-25)


<a id="bug-fixes-5"></a>

### 问题修复

* 升级至 anthropic SDK v1 ([#15588](https://github.com/Arize-ai/phoenix/issues/15588)) ([b28cf94](https://github.com/Arize-ai/phoenix/commit/b28cf94fcd37afeacfd059b4a01e7ad38327e483))

## [3.5.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.4.0...arize-phoenix-evals-v3.5.0) (2026-08-21)


<a id="features-4"></a>

### 新功能

* **evals:** 新增检索相关性评估器 ([#14766](https://github.com/Arize-ai/phoenix/issues/14766)) ([7efa7b2](https://github.com/Arize-ai/phoenix/commit/7efa7b21fc3284f0af928ddedda15927974ee94d))

## [3.4.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.3.0...arize-phoenix-evals-v3.4.0) (2026-08-15)


<a id="features-5"></a>

### 新功能

* **evals:** 新增幻觉评估器 ([#14708](https://github.com/Arize-ai/phoenix/issues/14708)) ([1aa1a84](https://github.com/Arize-ai/phoenix/commit/1aa1a8454b6524a9e7618f3c9970ae9466df67d2))

## [3.4.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.3.0...arize-phoenix-evals-v3.4.0) (2026-08-08)


<a id="features-6"></a>

### 新功能

* **evals:** 新增幻觉评估器 ([#14708](https://github.com/Arize-ai/phoenix/issues/14708)) ([1aa1a84](https://github.com/Arize-ai/phoenix/commit/1aa1a8454b6524a9e7618f3c9970ae9466df67d2))

## [3.3.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.2.0...arize-phoenix-evals-v3.3.0) (2026-07-23)


<a id="features-7"></a>

### 新功能

* **evals:** 新增毒性模板库模板及输入输出无关的基准测试 ([#14636](https://github.com/Arize-ai/phoenix/issues/14636)) ([1082155](https://github.com/Arize-ai/phoenix/commit/1082155e6e27e06d98a97af776c8d8b6892d4b2f))

## [3.2.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.1.1...arize-phoenix-evals-v3.2.0) (2026-07-21)


<a id="features-8"></a>

### 新功能

* **evals:** 新增用户阻力评估器 ([#14193](https://github.com/Arize-ai/phoenix/issues/14193)) ([1ae1a39](https://github.com/Arize-ai/phoenix/commit/1ae1a3933d4c0aa1dcf43660287da024dd8dbc6f))


<a id="bug-fixes-6"></a>

### 问题修复

* **evals:** 改进用户阻力提示词 ([#14561](https://github.com/Arize-ai/phoenix/issues/14561)) ([115d3f2](https://github.com/Arize-ai/phoenix/commit/115d3f24c1f5244abc49d2d1a25ef27d40469fae))
* **evals:** 在 Python 3.14 上跳过 LiteLLM ([#14407](https://github.com/Arize-ai/phoenix/issues/14407)) ([bc9b533](https://github.com/Arize-ai/phoenix/commit/bc9b533e5b4526478a8d3ca59dce284e8a0acef3))


<a id="documentation"></a>

### 文档

* 补齐评估、追踪、playground 和软件包的少量功能文档缺口 ([e5764b3](https://github.com/Arize-ai/phoenix/commit/e5764b348eeaca2d824638264b9d929c5a730c5a))

## [3.1.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.1.0...arize-phoenix-evals-v3.1.1) (2026-07-14)


<a id="bug-fixes-7"></a>

### 问题修复

* **evals:** 按类别计算宏平均和加权 F 分数，以符合 sklearn 语义 ([#13740](https://github.com/Arize-ai/phoenix/issues/13740)) ([c0f6267](https://github.com/Arize-ai/phoenix/commit/c0f6267f24e14d4e22e237be146fd05e0310f8f1))
* **evals:** 将 AsyncExecutor 超时计入 max_retries ([#14361](https://github.com/Arize-ai/phoenix/issues/14361)) ([90eee08](https://github.com/Arize-ai/phoenix/commit/90eee082b9e357a6669df29bc926a68f731fbc43))
* **evals:** 仅在默认宏平均下自动检测 0/1 positive_label ([#14012](https://github.com/Arize-ai/phoenix/issues/14012)) ([f96dbd9](https://github.com/Arize-ai/phoenix/commit/f96dbd9f6a405ead30a0acf5602f93e6f8488a43))

## [3.1.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v3.0.0...arize-phoenix-evals-v3.1.0) (2026-05-04)


<a id="features-9"></a>

### 新功能

* **agents:** 将 PXI 提示词组装移至服务端并缓存提示词 ([#12959](https://github.com/Arize-ai/phoenix/issues/12959)) ([f223f92](https://github.com/Arize-ai/phoenix/commit/f223f922420a25152f2ef9624be35b21e6003e89))
* **evals:** 收紧提示词消息处理并新增适配器测试 ([#12838](https://github.com/Arize-ai/phoenix/issues/12838)) ([fbb5270](https://github.com/Arize-ai/phoenix/commit/fbb52701361fb638405aa8732a76ea774a6cd929))


<a id="bug-fixes-8"></a>

### 问题修复

* **evals:** 使用运行时回退替代硬编码模型能力列表 ([#12709](https://github.com/Arize-ai/phoenix/issues/12709)) ([69a2ade](https://github.com/Arize-ai/phoenix/commit/69a2ade1405a78b10d7778e8d8ba24229d2fb405))


<a id="documentation-1"></a>

### 文档

* 在 X/Bluesky 旁新增 LinkedIn 社交链接 ([#12993](https://github.com/Arize-ai/phoenix/issues/12993)) ([5d14f23](https://github.com/Arize-ai/phoenix/commit/5d14f23598202c062530466a9dbdc9a1a033d6c8))

## [3.0.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.13.0...arize-phoenix-evals-v3.0.0) (2026-04-07)


<a id="-breaking-changes"></a>

### ⚠ 不兼容变更

* **evals:** 弃用 evals 1.0 并移除旧版 experiments 模块 ([#12239](https://github.com/Arize-ai/phoenix/issues/12239))

<a id="features-10"></a>

### 新功能

* **evals:** 弃用 evals 1.0 并移除旧版 experiments 模块 ([#12239](https://github.com/Arize-ai/phoenix/issues/12239)) ([15e6415](https://github.com/Arize-ai/phoenix/commit/15e6415105ce4757de905172cbd0e07215d38990))

## [2.13.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.12.0...arize-phoenix-evals-v2.13.0) (2026-04-01)


<a id="features-11"></a>

### 新功能

* 新增 Python 3.14 支持（Windows 除外） ([#12475](https://github.com/Arize-ai/phoenix/issues/12475)) ([50c08e3](https://github.com/Arize-ai/phoenix/commit/50c08e3ff4e41c0693e92b7d3de7dbc41384fad1))

## [2.12.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.11.0...arize-phoenix-evals-v2.12.0) (2026-03-24)


<a id="features-12"></a>

### 新功能

* **evals:** 接受结构化数据评估输入 ([#12095](https://github.com/Arize-ai/phoenix/issues/12095)) ([5f33727](https://github.com/Arize-ai/phoenix/commit/5f3372794fc2dfe0184d08f7d5d44f39284dbe67))


<a id="bug-fixes-9"></a>

### 问题修复

* **evals:** 允许内置分类评估器使用 prompt_template 和 kwargs ([#11984](https://github.com/Arize-ai/phoenix/issues/11984)) ([2ec192c](https://github.com/Arize-ai/phoenix/commit/2ec192c07c5e2f1831a2b159bdcbc17c3902a1aa))
* 固定 LiteLLM &lt;1.82.7 以缓解供应链攻击 ([#12342](https://github.com/Arize-ai/phoenix/issues/12342)) ([48970b6](https://github.com/Arize-ai/phoenix/commit/48970b62815a8230b38f67f4246c69cab3d473c0))
* **playground:** 防止 OTel 上下文泄漏导致数据集运行 trace_id 重复 ([#12062](https://github.com/Arize-ai/phoenix/issues/12062)) ([2a24625](https://github.com/Arize-ai/phoenix/commit/2a24625c5b390332a059266e9f05a972550c9cdc))


<a id="documentation-2"></a>

### 文档

* **evals:** 弃用 evals 1.0 文档 ([#12123](https://github.com/Arize-ai/phoenix/issues/12123)) ([b0dc90f](https://github.com/Arize-ai/phoenix/commit/b0dc90f445a25ba74ddc86e0cc8bcdf721260344))
* 根据最新能力更新所有软件包 README ([#12315](https://github.com/Arize-ai/phoenix/issues/12315)) ([b4ded15](https://github.com/Arize-ai/phoenix/commit/b4ded157987e0ce6fcbf749bf48225d9408313c2))

## [2.11.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.10.0...arize-phoenix-evals-v2.11.0) (2026-02-27)


<a id="features-13"></a>

### 新功能

* **evals:** 新增简洁性分类评估器  ([#11437](https://github.com/Arize-ai/phoenix/issues/11437)) ([d43c4ee](https://github.com/Arize-ai/phoenix/commit/d43c4eef5cf24845fdf26f0241f36496abf1a006))
* **evals:** 新增拒答评估器 ([#11718](https://github.com/Arize-ai/phoenix/issues/11718)) ([45a88fc](https://github.com/Arize-ai/phoenix/commit/45a88fc9354796b798b24b2e107427bbd8282995))
* **evals:** 新增将 Phoenix 提示词转换为评估模板的工具 ([#11696](https://github.com/Arize-ai/phoenix/issues/11696)) ([ded46ba](https://github.com/Arize-ai/phoenix/commit/ded46bab21702650fb479fffbb68cd08dff74268))


<a id="bug-fixes-10"></a>

### 问题修复

* **evals:** 处理 litellm 1.81.16 不再将 usage=None 自动转换为 Usage(0,0,0) 的变化 ([#11754](https://github.com/Arize-ai/phoenix/issues/11754)) ([ad516c8](https://github.com/Arize-ai/phoenix/commit/ad516c81778da52f94d4f364249f8998b26db56a))
* 更新 Slack 邀请链接 ([#11612](https://github.com/Arize-ai/phoenix/issues/11612)) ([316833e](https://github.com/Arize-ai/phoenix/commit/316833e629baf1b9185d7c712d8816b927d69a96))

## [2.10.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.9.0...arize-phoenix-evals-v2.10.0) (2026-02-13)


<a id="-breaking-changes-1"></a>

### ⚠ 不兼容变更

* 新增数据集评估器

<a id="features-14"></a>

### 新功能

* 新增工具响应处理评估器模板 ([#11276](https://github.com/Arize-ai/phoenix/issues/11276)) ([0738cb9](https://github.com/Arize-ai/phoenix/commit/0738cb9209d158b4aebab42339d20e3a71da3f2d))
* 新增数据集评估器 ([1274b03](https://github.com/Arize-ai/phoenix/commit/1274b03f3be64c450094d620d65af6749af01ec4))
* 新增数据集评估器 ([5f47820](https://github.com/Arize-ai/phoenix/commit/5f4782012537d533570184a6ce1e005e9945d8bf))
* 新增数据集评估器 ([cf0e09a](https://github.com/Arize-ai/phoenix/commit/cf0e09a82a5e44c9df26619c6372d2474a289b49))
* 在服务端启用完整 Mustache 提示词模板 ([#11229](https://github.com/Arize-ai/phoenix/issues/11229)) ([68ba0ed](https://github.com/Arize-ai/phoenix/commit/68ba0ed2316b6d690bcf782c8575b56f4a8c4d9e))
* 按标签过滤内置分类评估器 ([#11416](https://github.com/Arize-ai/phoenix/issues/11416)) ([aa95a3f](https://github.com/Arize-ai/phoenix/commit/aa95a3fb15badfe9d2b706e9bb3d604c0287e66b))


<a id="bug-fixes-11"></a>

### 问题修复

* **templates:** 简化模板格式化器 ([#11410](https://github.com/Arize-ai/phoenix/issues/11410)) ([1f6df01](https://github.com/Arize-ai/phoenix/commit/1f6df01e2975c6b713538a8b4c19787225c9d042))


<a id="miscellaneous-chores"></a>

### 其他维护

* 发布 2.10.0 ([4561612](https://github.com/Arize-ai/phoenix/commit/4561612d7e2547e45ffd15970548f8a2d5d3070d))

## [2.9.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.8.0...arize-phoenix-evals-v2.9.0) (2026-02-02)


<a id="features-15"></a>

### 新功能

* 新增 FaithfulnessEvaluator 并弃用 HallucinationEvaluator ([#10962](https://github.com/Arize-ai/phoenix/issues/10962)) ([fc8b1b5](https://github.com/Arize-ai/phoenix/commit/fc8b1b5eaeadbd4e23ed684f0f2286f5a55d00a2))
* 新增工具调用准确性指标 ([#10988](https://github.com/Arize-ai/phoenix/issues/10988)) ([d1c89bf](https://github.com/Arize-ai/phoenix/commit/d1c89bf80e6460efa6ee5ae94ee94972f95ab0ea))
* **evals:** 为两个库补充缺失的 tool_selection 评估器 ([#11167](https://github.com/Arize-ai/phoenix/issues/11167)) ([d6d1953](https://github.com/Arize-ai/phoenix/commit/d6d19530e319e215695e418c99e706d2c270dc4a))
* **evals:** 新增中性优化方向选项 ([#10932](https://github.com/Arize-ai/phoenix/issues/10932)) ([5768a14](https://github.com/Arize-ai/phoenix/commit/5768a146950821ac5ba28bc4f0cbb7ac1cf34e2d))
* 在 Scores 中返回 trace_id，并改进 trace 装饰器 ([#10954](https://github.com/Arize-ai/phoenix/issues/10954)) ([a8dfb54](https://github.com/Arize-ai/phoenix/commit/a8dfb54da77c084733876440d441a0f462fcf751))


<a id="bug-fixes-12"></a>

### 问题修复

* 使用未弃用的 pandas 缺失值检查 ([#11069](https://github.com/Arize-ai/phoenix/issues/11069)) ([383ac2a](https://github.com/Arize-ai/phoenix/commit/383ac2a0fdf6e65bf3aa3e383616675200067a79))

## [2.8.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.7.1...arize-phoenix-evals-v2.8.0) (2026-01-08)


<a id="features-16"></a>

### 新功能

* 新增正确性评估器 ([#10829](https://github.com/Arize-ai/phoenix/issues/10829)) ([da13ad5](https://github.com/Arize-ai/phoenix/commit/da13ad54784bfbdcd133a0c18e5f99e80a2b6482))
* 允许 LLM 构造函数接受同步和异步客户端 kwargs ([#10808](https://github.com/Arize-ai/phoenix/issues/10808)) ([1442074](https://github.com/Arize-ai/phoenix/commit/14420746db25e67ef58787c5e0656f9b41c968c8))
* **evals:** 新增内置工具选择正确性指标 ([#10744](https://github.com/Arize-ai/phoenix/issues/10744)) ([9e816c9](https://github.com/Arize-ai/phoenix/commit/9e816c9dd988dabf864cf05764efcef6573b6930))


<a id="bug-fixes-13"></a>

### 问题修复

* **prompts:** 移除内置提示词中的换行 ([#10736](https://github.com/Arize-ai/phoenix/issues/10736)) ([edf35f0](https://github.com/Arize-ai/phoenix/commit/edf35f00ef90cc27160e0887b97a5bc49c6cd0e8))

## [2.7.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.7.0...arize-phoenix-evals-v2.7.1) (2025-12-12)


<a id="bug-fixes-14"></a>

### 问题修复

* **evals:** 修复限流器 ([#10576](https://github.com/Arize-ai/phoenix/issues/10576)) ([5bbd5de](https://github.com/Arize-ai/phoenix/commit/5bbd5de427c8b33e0c48dab0f00e526f71561e43))

## [2.7.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.6.1...arize-phoenix-evals-v2.7.0) (2025-12-04)


<a id="features-17"></a>

### 新功能

* **evals:** 支持提示词和模板消息 ([#10356](https://github.com/Arize-ai/phoenix/issues/10356)) ([7d3dc7d](https://github.com/Arize-ai/phoenix/commit/7d3dc7d2846807053da63a8aa9cb776283deb370))

## [2.6.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.6.0...arize-phoenix-evals-v2.6.1) (2025-11-22)


<a id="bug-fixes-15"></a>

### 问题修复

* 处理 AnthropicModel 中 top_p 和 temperature 为 None 的情况 ([#10361](https://github.com/Arize-ai/phoenix/issues/10361)) ([2ade906](https://github.com/Arize-ai/phoenix/commit/2ade9067080e3557472518472c76efbfd08b343f))

## [2.6.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.5.0...arize-phoenix-evals-v2.6.0) (2025-11-12)


<a id="features-18"></a>

### 新功能

* 新增 anthropic 和 google-genai 适配器 ([#9993](https://github.com/Arize-ai/phoenix/issues/9993)) ([724b2de](https://github.com/Arize-ai/phoenix/commit/724b2de51fea41f21890a3c8ad55ee78d4686c86))
* 为 Azure OpenAI 模型新增 GPT-5 支持 ([#9829](https://github.com/Arize-ai/phoenix/issues/9829)) ([e4c664d](https://github.com/Arize-ai/phoenix/commit/e4c664d4c3f890338e1313a9da543d75869133fb))
* ClassificationEvaluators 支持调用参数 ([#9831](https://github.com/Arize-ai/phoenix/issues/9831)) ([1530304](https://github.com/Arize-ai/phoenix/commit/15303046cd95a203f2863524c8770fbacb7e7de9))


<a id="bug-fixes-16"></a>

### 问题修复

* **evals:** 建议使用 kwargs，避免位置参数 ([#9996](https://github.com/Arize-ai/phoenix/issues/9996)) ([efdc954](https://github.com/Arize-ai/phoenix/commit/efdc954f818915b5b59207cad1c9cb1fb17b7063))
* **evals:** 修复杂项问题并改善易用性 ([#9879](https://github.com/Arize-ai/phoenix/issues/9879)) ([5546179](https://github.com/Arize-ai/phoenix/commit/5546179b230812d38770e011d541d3ac5107d652))


<a id="documentation-3"></a>

### 文档

* 将 main 合并至文档 ([#10087](https://github.com/Arize-ai/phoenix/issues/10087)) ([740aca0](https://github.com/Arize-ai/phoenix/commit/740aca004b28e31a5bde0735d26d2e5d8c78b276))
* 将 main 同步至文档 ([65a68f4](https://github.com/Arize-ai/phoenix/commit/65a68f4c05635e76068b2c85b2929b4d13ca2668))

## [2.5.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.4.0...arize-phoenix-evals-v2.5.0) (2025-10-07)


<a id="features-19"></a>

### 新功能

* **evals:** 新增正则表达式评估器 ([#9756](https://github.com/Arize-ai/phoenix/issues/9756)) ([d3ba324](https://github.com/Arize-ai/phoenix/commit/d3ba324a75a7863d54f028f2f1d92fc2d8b00966))
* 改进绑定易用性 ([#9612](https://github.com/Arize-ai/phoenix/issues/9612)) ([2989a91](https://github.com/Arize-ai/phoenix/commit/2989a914ef3249327a0f06592aa2cc226d2d367c))
* LLM 支持更多提供方 ([#9701](https://github.com/Arize-ai/phoenix/issues/9701)) ([b6bd07d](https://github.com/Arize-ai/phoenix/commit/b6bd07d295cb2553bf80030c5fd1f8bd15c46e82))


<a id="documentation-4"></a>

### 文档

* **evals:** 更新分类评估器文档字符串 ([#9715](https://github.com/Arize-ai/phoenix/issues/9715)) ([cb71cfd](https://github.com/Arize-ai/phoenix/commit/cb71cfded1458d76ccfb7b6bae5348d016a11266))

## [2.4.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.3.0...arize-phoenix-evals-v2.4.0) (2025-10-02)


<a id="features-20"></a>

### 新功能

* `phoenix.evals.create_evaluator` 支持协程函数 ([#9746](https://github.com/Arize-ai/phoenix/issues/9746)) ([3f6a182](https://github.com/Arize-ai/phoenix/commit/3f6a1825f53e4deb73e285846495770e9bac0966))


<a id="documentation-5"></a>

### 文档

* **evals:** 为 evaluators 模块新增示例 ([#9727](https://github.com/Arize-ai/phoenix/issues/9727)) ([f62468d](https://github.com/Arize-ai/phoenix/commit/f62468d9cddabcf3b96c0e4ced2da764aa211f85))
* **evals:** 自动生成 metrics 和 utils 文档 ([#9737](https://github.com/Arize-ai/phoenix/issues/9737)) ([e5d6ede](https://github.com/Arize-ai/phoenix/commit/e5d6ede2dfa34efe2a183228b79f25e498770925))

## [2.3.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.2.0...arize-phoenix-evals-v2.3.0) (2025-10-01)


<a id="features-21"></a>

### 新功能

* 允许 evals Templates 使用点分隔 f-string 键 ([#9725](https://github.com/Arize-ai/phoenix/issues/9725)) ([505ead8](https://github.com/Arize-ai/phoenix/commit/505ead838725ab447ef323d6549286d00d132b1e))


<a id="bug-fixes-17"></a>

### 问题修复

* **evals:** 搜索 jsonpath 前先尝试直接从 eval_input 提取键 ([#9721](https://github.com/Arize-ai/phoenix/issues/9721)) ([04f3da7](https://github.com/Arize-ai/phoenix/commit/04f3da7b6c9aa318924a4abd61256dc81ae2afa8))

## [2.2.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.1.0...arize-phoenix-evals-v2.2.0) (2025-09-27)


<a id="features-22"></a>

### 新功能

* **evals:** 新增文档相关性评估器 ([#9661](https://github.com/Arize-ai/phoenix/issues/9661)) ([34b583f](https://github.com/Arize-ai/phoenix/commit/34b583f85128f35ff0d8c85ce13343b2b7e66c9c))
* **evals:** 新增将 DataFrame 评估格式化为标注并记录至 Phoenix 的工具 ([#9610](https://github.com/Arize-ai/phoenix/issues/9610)) ([58cce2b](https://github.com/Arize-ai/phoenix/commit/58cce2bbe838aace1995f32cb17cbcf26bbb08bd))

## [2.1.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.0.1...arize-phoenix-evals-v2.1.0) (2025-09-24)


<a id="features-23"></a>

### 新功能

* 新增 Azure 提供方支持 ([#9605](https://github.com/Arize-ai/phoenix/issues/9605)) ([edf448a](https://github.com/Arize-ai/phoenix/commit/edf448a14954a63ec0251cdf6b4f2e24b0b09bc2))


<a id="bug-fixes-18"></a>

### 问题修复

* 移除 OpenAI SDK 重试 ([#9587](https://github.com/Arize-ai/phoenix/issues/9587)) ([08d78f9](https://github.com/Arize-ai/phoenix/commit/08d78f9d12d0e29c0a154b93ee99d18657c0fe13))
* 使用 OITracer ([#9588](https://github.com/Arize-ai/phoenix/issues/9588)) ([8bb7743](https://github.com/Arize-ai/phoenix/commit/8bb7743c8fbbe231d500d49109c04a56624328bf))

## [2.0.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v2.0.0...arize-phoenix-evals-v2.0.1) (2025-09-17)


<a id="documentation-6"></a>

### 文档

* 修复预览文档导入路径 ([#9538](https://github.com/Arize-ai/phoenix/issues/9538)) ([dc771e7](https://github.com/Arize-ai/phoenix/commit/dc771e72370de513eb0fb5ae7d32f2b6b4017735))

## [2.0.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.29.0...arize-phoenix-evals-v2.0.0) (2025-09-17)

<a id="what-is-evals-20"></a>

## 什么是 evals 2.0？

新版 Phoenix evals 库提供轻量、可组合的基础组件，用于编写和运行自动评估。

- 通过适配器配合偏好的模型 SDK，例如 OpenAI、LiteLLM 和 LangChain。
- 提供强大的输入映射和绑定功能，以处理复杂数据结构。
- 包含多项常见评估任务的预置指标。
- 评估器已集成 OpenTelemetry 追踪埋点。
- 还提供大量便利功能，改善开发体验！

<a id="quickstart"></a>

### 快速入门

```python
from phoenix.evals import create_classifier
from phoenix.evals.llm import LLM

llm = LLM(provider="openai", model="gpt-4o")

evaluator = create_classifier(
    name="helpfulness",
    prompt_template="Rate the response to the user query as helpful or not:\n\nQuery: {input}\nResponse: {output}",
    llm=llm,
    choices={"helpful": 1.0, "not_helpful": 0.0},
)

# Simple evaluation
scores = evaluator.evaluate({"input": "How do I reset?", "output": "Go to settings > reset."})
scores[0].pretty_print()

# With input mapping for nested data
scores = evaluator.evaluate(
    {"data": {"query": "How do I reset?", "response": "Go to settings > reset."}},
    input_mapping={"input": "data.query", "output": "data.response"},
)
scores[0].pretty_print()
```

<a id="-breaking-changes-2"></a>

### ⚠ 不兼容变更

- 将 Evals 2.0 移出预览阶段 ([#9526](https://github.com/Arize-ai/phoenix/issues/9526))
- 使用 `LLMEvaluator` 配合 `run_evals` 时，导入语句现为：`phoenix.evals.legacy import LLMEvaluator`
  - 2.0 引入新的 `LLMEvaluator` 抽象，与之前版本不同。

<a id="features-24"></a>

### 新功能

- **evals:** 为 LLM 方法新增限流 ([#9271](https://github.com/Arize-ai/phoenix/issues/9271)) ([67ca56b](https://github.com/Arize-ai/phoenix/commit/67ca56b3293812cbf4ec96e9c2a57afd516ae73c))
- **evals:** 新增异步 DataFrame 评估 ([#9315](https://github.com/Arize-ai/phoenix/issues/9315)) ([da6d88f](https://github.com/Arize-ai/phoenix/commit/da6d88f70907223257aeb08c903afc44f6c3b765))
- 兼容 Experiments&lt;-&gt;Evals 2.0 ([#9442](https://github.com/Arize-ai/phoenix/issues/9442)) ([90e4dbc](https://github.com/Arize-ai/phoenix/commit/90e4dbc08e63ee707f3ab7e42dc5146ad6054e82))
- 将 Evals 2.0 移出预览阶段 ([#9526](https://github.com/Arize-ai/phoenix/issues/9526)) ([c644766](https://github.com/Arize-ai/phoenix/commit/c644766a7eea3784e155c1df2ffd7403efecb514))

<a id="bug-fixes-19"></a>

### 问题修复

- 新增 Gemini 2.0 Flash 支持 ([#9440](https://github.com/Arize-ai/phoenix/issues/9440)) ([3521599](https://github.com/Arize-ai/phoenix/commit/35215995b681e021b94b670e4177f730c705d983))
- **evals:** 统一同步和异步 LLM ([#9287](https://github.com/Arize-ai/phoenix/issues/9287)) ([21b8dfe](https://github.com/Arize-ai/phoenix/commit/21b8dfee05c71ce9b614aca8def32ffda821862b))

<a id="documentation-7"></a>

### 文档

- 为所有 README 新增文档链接 ([#9322](https://github.com/Arize-ai/phoenix/issues/9322)) ([b0b671b](https://github.com/Arize-ai/phoenix/commit/b0b671bbabf05279ea7254e2b92972725a7a86b6))
- **client:** 修复 Python 客户端文档 ([#9317](https://github.com/Arize-ai/phoenix/issues/9317)) ([d94835a](https://github.com/Arize-ai/phoenix/commit/d94835aad129216fdb7d480a70aa2a501e615a8e))
- 统一文档字符串 ([#9324](https://github.com/Arize-ai/phoenix/issues/9324)) ([00dcea9](https://github.com/Arize-ai/phoenix/commit/00dcea97aac7a8165395bfaefe52f771feadca2d))
- **evals:** 更新预览版评估自动文档 ([#9426](https://github.com/Arize-ai/phoenix/issues/9426)) ([756c1b6](https://github.com/Arize-ai/phoenix/commit/756c1b64b9552af723d853f1e5e6c98d2996cab1))

## [0.29.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.28.1...arize-phoenix-evals-v0.29.0) (2025-08-26)

<a id="features-25"></a>

### 新功能

- 新增 evals 2.0 追踪 ([#9163](https://github.com/Arize-ai/phoenix/issues/9163)) ([aee7edf](https://github.com/Arize-ai/phoenix/commit/aee7edf7fdf8fb37a243166589fdb92615067bad))
- **evals:** 新增 evaluate_dataframe 函数 ([#9197](https://github.com/Arize-ai/phoenix/issues/9197)) ([47c562c](https://github.com/Arize-ai/phoenix/commit/47c562c5b434828152bc5199ca7a3a913e0f36c6))

<a id="bug-fixes-20"></a>

### 问题修复

- **evals:** 输入映射从 glom 切换至 jsonpath-ng ([#9199](https://github.com/Arize-ai/phoenix/issues/9199)) ([5daaada](https://github.com/Arize-ai/phoenix/commit/5daaadac605269d96a17fb5cce68b773619e6abc))

<a id="documentation-8"></a>

### 文档

- **evals:** 新增评估预览模块文档 ([#9159](https://github.com/Arize-ai/phoenix/issues/9159)) ([8f38e06](https://github.com/Arize-ai/phoenix/commit/8f38e066edc8659478a40a4b3d99db8b555b8f06))

## [0.28.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.28.0...arize-phoenix-evals-v0.28.1) (2025-08-20)

<a id="bug-fixes-21"></a>

### 问题修复

- **evals:** 使评估器输入 schema 更明确且易于发现 ([#9109](https://github.com/Arize-ai/phoenix/issues/9109)) ([b5c7170](https://github.com/Arize-ai/phoenix/commit/b5c71702a1e634c8ac6df130f2b5ea0355e9e7e2))
- **evals:** 更新 `create_evaluator` 装饰器，将函数输出转换为有效 Scores ([#9143](https://github.com/Arize-ai/phoenix/issues/9143)) ([b51b677](https://github.com/Arize-ai/phoenix/commit/b51b677c90e6379f427db3120604113b2813f4b8))

## [0.28.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.27.0...arize-phoenix-evals-v0.28.0) (2025-08-19)

<a id="features-26"></a>

### 新功能

- 支持动态并发 ([#8992](https://github.com/Arize-ai/phoenix/issues/8992)) ([3e48611](https://github.com/Arize-ai/phoenix/commit/3e48611896011e820c628b73f592aaa2f5c53889))

<a id="bug-fixes-22"></a>

### 问题修复

- [evals] 移除批量评估方法 ([#9052](https://github.com/Arize-ai/phoenix/issues/9052)) ([38df753](https://github.com/Arize-ai/phoenix/commit/38df753a1916ca970c6288cd81e00efa25beb2e1))
- [evals] 原样抛出异常 ([#9066](https://github.com/Arize-ai/phoenix/issues/9066)) ([f8703b5](https://github.com/Arize-ai/phoenix/commit/f8703b511b41feb47eb1f43b08a06d0b8158286e))

## [0.27.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.26.1...arize-phoenix-evals-v0.27.0) (2025-08-13)

<a id="features-27"></a>

### 新功能

- [evals] 新增精确率、召回率和 F 分数指标 ([#9000](https://github.com/Arize-ai/phoenix/issues/9000)) ([7aeec60](https://github.com/Arize-ai/phoenix/commit/7aeec60d6a9e91a88e56b9d803b49a99fe922ebe))
- 新增评估器和分数抽象 ([#8842](https://github.com/Arize-ai/phoenix/issues/8842)) ([f56b9cf](https://github.com/Arize-ai/phoenix/commit/f56b9cf92f7853575d0892aaea165a36dcf6c7a3))

<a id="bug-fixes-23"></a>

### 问题修复

- [evals] 重命名并更新评估器装饰器 ([#9044](https://github.com/Arize-ai/phoenix/issues/9044)) ([bb3500b](https://github.com/Arize-ai/phoenix/commit/bb3500b657e13741d23badb3a74ad262fc64f8de))
- 向非 Azure OpenAI 客户端传递默认请求头 ([#9001](https://github.com/Arize-ai/phoenix/issues/9001)) ([baf54a0](https://github.com/Arize-ai/phoenix/commit/baf54a040a1a6cbc258d960f18b3fe4efdf53413))
- 从 Anthropic 适配器正确返回对象 ([#8977](https://github.com/Arize-ai/phoenix/issues/8977)) ([e9a2e11](https://github.com/Arize-ai/phoenix/commit/e9a2e11719de53ff1f54879f38463746a6813de8))
- 在 Azure 中支持 o4 ([#9059](https://github.com/Arize-ai/phoenix/issues/9059)) ([9bec39f](https://github.com/Arize-ai/phoenix/commit/9bec39fc2e184b0778e1fb59d84077b2f6cdbe0a))

## [0.26.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.26.0...arize-phoenix-evals-v0.26.1) (2025-08-01)

<a id="bug-fixes-24"></a>

### 问题修复

- 将 `_generate` 和 `_async_generate` 的函数返回类型恢复为 `str` ([#8901](https://github.com/Arize-ai/phoenix/issues/8901)) ([91550dc](https://github.com/Arize-ai/phoenix/commit/91550dc8039cf3d1087e63ef763cdee6f95a75f2))

## [0.26.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.25.0...arize-phoenix-evals-v0.26.0) (2025-08-01)

<a id="features-28"></a>

### 新功能

- 允许指定对象生成方法 ([#8884](https://github.com/Arize-ai/phoenix/issues/8884)) ([c73e1a6](https://github.com/Arize-ai/phoenix/commit/c73e1a6752b88e73f030cff3b23df42b958b425f))
- **evals:** 在 `llm_classify` 中返回 token 用量 ([#8692](https://github.com/Arize-ai/phoenix/issues/8692)) ([aa71d81](https://github.com/Arize-ai/phoenix/commit/aa71d8164124c88028d1c18b217d3ec899e5b4f9))
- 改进评估模板 ([#8799](https://github.com/Arize-ai/phoenix/issues/8799)) ([b32717c](https://github.com/Arize-ai/phoenix/commit/b32717c94971d43124253e21ba10f366bc8228fa))

<a id="bug-fixes-25"></a>

### 问题修复

- 为实验模块警告新增 emoji 保护 ([#8887](https://github.com/Arize-ai/phoenix/issues/8887)) ([0c63de7](https://github.com/Arize-ai/phoenix/commit/0c63de70b2891a09b6fa5ad74704e21ff96c70a4))
- **evals:** 新增 LLM 客户端选择优先级 ([#8868](https://github.com/Arize-ai/phoenix/issues/8868)) ([06bda51](https://github.com/Arize-ai/phoenix/commit/06bda51affb5a2e034e3c6473565a13f3fee4ada))
- 处理 Windows 有时无法渲染 emoji 的问题 ([#8880](https://github.com/Arize-ai/phoenix/issues/8880)) ([c592e5c](https://github.com/Arize-ai/phoenix/commit/c592e5c766e9ac457cab5d84846e44413f611794))

<a id="documentation-9"></a>

### 文档

- 更新 GoogleGenAI 支持文档 ([#8858](https://github.com/Arize-ai/phoenix/issues/8858)) ([a8bef55](https://github.com/Arize-ai/phoenix/commit/a8bef55b65a92b0d325e54c715f342728e63aa7b))

## [0.25.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.24.0...arize-phoenix-evals-v0.25.0) (2025-07-30)

<a id="features-29"></a>

### 新功能

- 生成分类原语 ([#8816](https://github.com/Arize-ai/phoenix/issues/8816)) ([88d5090](https://github.com/Arize-ai/phoenix/commit/88d5090d33fbe384c08cf305ab75863520e7fa03))

<a id="bug-fixes-26"></a>

### 问题修复

- 移除 requests 库依赖 ([#8854](https://github.com/Arize-ai/phoenix/issues/8854)) ([ad9f311](https://github.com/Arize-ai/phoenix/commit/ad9f311aee3997c8caa8e505cc84faa1e8fb7428))

## [0.24.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.23.1...arize-phoenix-evals-v0.24.0) (2025-07-30)

<a id="features-30"></a>

### 新功能

- **evals:** 新增 google-genai SDK 支持 ([#8798](https://github.com/Arize-ai/phoenix/issues/8798)) ([08ad038](https://github.com/Arize-ai/phoenix/commit/08ad0384d0d53d6068234b8a2d0a9fd4859b020e))
- 新增 LLM 包装器原型 ([#8729](https://github.com/Arize-ai/phoenix/issues/8729)) ([1b25009](https://github.com/Arize-ai/phoenix/commit/1b25009683dd52803162786466a34e0b897c6fc0))

## [0.23.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.23.0...arize-phoenix-evals-v0.23.1) (2025-07-21)

<a id="bug-fixes-27"></a>

### 问题修复

- 从工具调用函数参数获取响应 ([#8706](https://github.com/Arize-ai/phoenix/issues/8706)) ([0db40ca](https://github.com/Arize-ai/phoenix/commit/0db40cadc5f7bcc015aa13dfa7c2a2a46c41c02f))

## [0.23.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.22.0...arize-phoenix-evals-v0.23.0) (2025-07-16)

<a id="features-31"></a>

### 新功能

- 提示词变量跳过解析 ([#8587](https://github.com/Arize-ai/phoenix/issues/8587)) ([a031c3c](https://github.com/Arize-ai/phoenix/commit/a031c3cedad3203b29ca4b9ef23ca89a40444ff8))

## [0.22.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.21.1...arize-phoenix-evals-v0.22.0) (2025-07-02)

<a id="features-32"></a>

### 新功能

- 允许 Vertex GenerativeModel 实例化时使用额外关键字参数 ([#8387](https://github.com/Arize-ai/phoenix/issues/8387)) ([a09a6ce](https://github.com/Arize-ai/phoenix/commit/a09a6ce88806dfbe606d1bd971a1b9180de6690a))

## [0.21.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.21.0...arize-phoenix-evals-v0.21.1) (2025-07-02)

<a id="documentation-10"></a>

### 文档

- 新增 Agent 工具选择和参数提取模板 ([#8353](https://github.com/Arize-ai/phoenix/issues/8353)) ([e4a2e73](https://github.com/Arize-ai/phoenix/commit/e4a2e732e670aad64dc4256767e198c024593266))

## [0.21.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.8...arize-phoenix-evals-v0.21.0) (2025-06-21)

<a id="features-33"></a>

### 新功能

- **auth:** 支持登出 ([#7985](https://github.com/Arize-ai/phoenix/issues/7985)) ([63128c5](https://github.com/Arize-ai/phoenix/commit/63128c5328222147fe5c5103d8dd3576d5534bc2))
- 拆分 Phoenix client 和 evals 文档 ([#7948](https://github.com/Arize-ai/phoenix/issues/7948)) ([e569b68](https://github.com/Arize-ai/phoenix/commit/e569b6802ab9e31cb230a30dbc08f60d7e28e993))

<a id="documentation-11"></a>

### 文档

- 改进 Read the Docs 的命名和结构 ([#8009](https://github.com/Arize-ai/phoenix/issues/8009)) ([76a4b92](https://github.com/Arize-ai/phoenix/commit/76a4b9282ff8476757ee1c0b3c85a7767208795b))
- 更新 phoenix-evals README ([#8029](https://github.com/Arize-ai/phoenix/issues/8029)) ([3261555](https://github.com/Arize-ai/phoenix/commit/326155513813f05b617f27f674fdb34151c5735b))

## [0.20.8](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.7...arize-phoenix-evals-v0.20.8) (2025-06-04)

<a id="bug-fixes-28"></a>

### 问题修复

- **evals:** 支持乱序评估 ([#7849](https://github.com/Arize-ai/phoenix/issues/7849)) ([63c012d](https://github.com/Arize-ai/phoenix/commit/63c012d49bf318190cd3170e664d50dbb8179e8a))

## [0.20.7](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.6...arize-phoenix-evals-v0.20.7) (2025-05-28)

<a id="bug-fixes-29"></a>

### 问题修复

- 稳定标签提取 ([#7499](https://github.com/Arize-ai/phoenix/issues/7499)) ([830247e](https://github.com/Arize-ai/phoenix/commit/830247ef97bca6f4bcbeb6fc2f9ac663c1e19344))

## [0.20.6](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.5...arize-phoenix-evals-v0.20.6) (2025-04-17)

<a id="bug-fixes-30"></a>

### 问题修复

- 更新 Azure 最大 token 数 ([#7144](https://github.com/Arize-ai/phoenix/issues/7144)) ([ce72e76](https://github.com/Arize-ai/phoenix/commit/ce72e76242fef34dbe7eaa4544da7c12a37138cd))

## [0.20.5](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.4...arize-phoenix-evals-v0.20.5) (2025-04-16)

<a id="bug-fixes-31"></a>

### 问题修复

- 根据模型格式化 additionalModelRequestFields ([#6943](https://github.com/Arize-ai/phoenix/issues/6943)) ([aec9541](https://github.com/Arize-ai/phoenix/commit/aec9541524e5aa1e91ea7c3bf96d8960f202ba35))

## [0.20.4](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.3...arize-phoenix-evals-v0.20.4) (2025-03-24)

<a id="bug-fixes-32"></a>

### 问题修复

- 从 Bedrock invoke_model API 迁移至 converse API ([#6503](https://github.com/Arize-ai/phoenix/issues/6503)) ([a393dc9](https://github.com/Arize-ai/phoenix/commit/a393dc9ce864cfb2ce06296e70f39459b195053a))

<a id="documentation-12"></a>

### 文档

- 修复图片（GITBOOK-1022） ([171c65e](https://github.com/Arize-ai/phoenix/commit/171c65e95053aece8ed182cfd1547cb2cf4df0f7))
- 修复社区链接（GITBOOK-1026） ([432ed92](https://github.com/Arize-ai/phoenix/commit/432ed9297533edbef73c8c58ae4af098d5ff94b1))
- 无主题（GITBOOK-1020） ([6c0ef74](https://github.com/Arize-ai/phoenix/commit/6c0ef74930c7ee0baa38659e21524b25b5b5fd71))
- 无主题（GITBOOK-1038） ([812ea2c](https://github.com/Arize-ai/phoenix/commit/812ea2caaee1889741bb893995fb89b4653430d7))
- 无主题（GITBOOK-1040） ([1d31ae8](https://github.com/Arize-ai/phoenix/commit/1d31ae8de6c924f9ecd0d3c77f77fef033320c86))
- 无主题（GITBOOK-1045） ([0aa0301](https://github.com/Arize-ai/phoenix/commit/0aa03011bda53faad35267facc73047e4be35142))
- 无主题（GITBOOK-1087） ([6fa5fd7](https://github.com/Arize-ai/phoenix/commit/6fa5fd71cdf57a9a5a7efc3e2822ad57497f3b5a))
- 无主题（GITBOOK-1090） ([024c49f](https://github.com/Arize-ai/phoenix/commit/024c49fe57487ee816317f798ec648331a866ae4))
- 无主题（GITBOOK-1099） ([b4357e3](https://github.com/Arize-ai/phoenix/commit/b4357e324a9444704fbf85370c193ef2ee59495f))
- 更新措辞（GITBOOK-1030） ([9e9142b](https://github.com/Arize-ai/phoenix/commit/9e9142be0cbc6d5cc08cc373ce1c14eee0479b00))

## [0.20.3](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.2...arize-phoenix-evals-v0.20.3) (2025-02-13)

<a id="bug-fixes-33"></a>

### 问题修复

- 处理 o1-preview 不支持 developer 角色 ([#6370](https://github.com/Arize-ai/phoenix/issues/6370)) ([9ea8651](https://github.com/Arize-ai/phoenix/commit/9ea8651b7734898a8b3050b335a759657ea18712))

## [0.20.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.1...arize-phoenix-evals-v0.20.2) (2025-02-06)

<a id="bug-fixes-34"></a>

### 问题修复

- 使用最大补全 token 数并检查工具调用 ([#6287](https://github.com/Arize-ai/phoenix/issues/6287)) ([e5e5294](https://github.com/Arize-ai/phoenix/commit/e5e5294b2b2b2f725ee673520a71cdca0457936d))

## [0.20.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.20.0...arize-phoenix-evals-v0.20.1) (2025-02-06)

<a id="bug-fixes-35"></a>

### 问题修复

- 更新参数过滤逻辑 ([#6285](https://github.com/Arize-ai/phoenix/issues/6285)) ([0f552e6](https://github.com/Arize-ai/phoenix/commit/0f552e6aec08f918408d82a248788e21bac8803d))

## [0.20.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.19.0...arize-phoenix-evals-v0.20.0) (2025-02-05)

<a id="features-34"></a>

### 新功能

- 允许按模型覆盖执行器超时 ([#6206](https://github.com/Arize-ai/phoenix/issues/6206)) ([23fb2b0](https://github.com/Arize-ai/phoenix/commit/23fb2b03e2aa8cf3f0940b857cd2ca3f7dfd71b7))
- 支持不使用“system”角色的 OpenAI 推理模型 ([#6239](https://github.com/Arize-ai/phoenix/issues/6239)) ([84f9d8e](https://github.com/Arize-ai/phoenix/commit/84f9d8e96846a496aafa1c360932268cba935d3c))

<a id="bug-fixes-36"></a>

### 问题修复

- 修复局部变量 'prompt_message' 在赋值前被引用 ([#6102](https://github.com/Arize-ai/phoenix/issues/6102)) ([10b1535](https://github.com/Arize-ai/phoenix/commit/10b1535dc7c9c5016d2b7c30574fa7e771601992))

## [0.19.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.18.1...arize-phoenix-evals-v0.19.0) (2025-01-16)

<a id="features-35"></a>

### 新功能

- 为 llm_classify() 新增音频评估和数据处理器 ([#5616](https://github.com/Arize-ai/phoenix/issues/5616)) ([0eda8ce](https://github.com/Arize-ai/phoenix/commit/0eda8ce9d1443d679734fe76cd6481f9a352e59b))

## [0.18.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.18.0...arize-phoenix-evals-v0.18.1) (2025-01-07)

<a id="bug-fixes-37"></a>

### 问题修复

- 允许 ClassificationTemplate 不使用解释模板 ([#5877](https://github.com/Arize-ai/phoenix/issues/5877)) ([d2df7ad](https://github.com/Arize-ai/phoenix/commit/d2df7ad8792df3d0637c003ba367dc483f6ad40d))

## [0.18.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.17.5...arize-phoenix-evals-v0.18.0) (2024-12-20)

<a id="features-36"></a>

### 新功能

- 允许 `phoenix.evals` 处理多模态消息模板 ([#5522](https://github.com/Arize-ai/phoenix/issues/5522)) ([41a4fc2](https://github.com/Arize-ai/phoenix/commit/41a4fc2ef98b8a06747e5cdd07f07d9bbe5662c3))

<a id="bug-fixes-38"></a>

### 问题修复

- 修复提示词模板拼写错误 ([#5571](https://github.com/Arize-ai/phoenix/issues/5571)) ([9646c8e](https://github.com/Arize-ai/phoenix/commit/9646c8ebc7ba81043f4e1a678977a8c6a0fa50c1))

<a id="documentation-13"></a>

### 文档

- 更新会话（GITBOOK-940） ([88dc135](https://github.com/Arize-ai/phoenix/commit/88dc135f99b03697387df0140533a0808454a88e))

## [0.17.5](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.17.4...arize-phoenix-evals-v0.17.5) (2024-11-19)

<a id="bug-fixes-39"></a>

### 问题修复

- 允许模板中使用点分隔键值 ([#5436](https://github.com/Arize-ai/phoenix/issues/5436)) ([8181094](https://github.com/Arize-ai/phoenix/commit/8181094ebd66e01f01a00ebe97473a965f7274e8))

## [0.17.4](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.17.3...arize-phoenix-evals-v0.17.4) (2024-11-12)

<a id="bug-fixes-40"></a>

### 问题修复

- **evals:** 提高默认最大 token 数 ([#5339](https://github.com/Arize-ai/phoenix/issues/5339)) ([b4af61e](https://github.com/Arize-ai/phoenix/commit/b4af61ee544c929fb01ac97724c1c657f0a46715))

## [0.17.3](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.17.2...arize-phoenix-evals-v0.17.3) (2024-11-06)

<a id="bug-fixes-41"></a>

### 问题修复

- **evals:** 模型实例化仅允许关键字参数 ([#5287](https://github.com/Arize-ai/phoenix/issues/5287)) ([aa95902](https://github.com/Arize-ai/phoenix/commit/aa95902e82b9207d6108e2a19b8531a817273e06))

## [0.17.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.17.1...arize-phoenix-evals-v0.17.2) (2024-10-18)

<a id="bug-fixes-42"></a>

### 问题修复

- 允许禁用进度条 ([#5064](https://github.com/Arize-ai/phoenix/issues/5064)) ([07d9856](https://github.com/Arize-ai/phoenix/commit/07d985672de77ed5f90a8195cbac24554c951ac4))

## [0.17.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.17.0...arize-phoenix-evals-v0.17.1) (2024-10-17)

<a id="bug-fixes-43"></a>

### 问题修复

- 提高 Python 版本上限，使 `arize-phoenix-evals` 和 `arize-phoenix-otel` 支持 Python 3.13 ([#5077](https://github.com/Arize-ai/phoenix/issues/5077)) ([ef5c893](https://github.com/Arize-ai/phoenix/commit/ef5c893ef7bc81690662a7687ed190f5b6dca701))

## [0.17.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.16.1...arize-phoenix-evals-v0.17.0) (2024-10-09)

<a id="features-37"></a>

### 新功能

- OpenAI 模型始终使用 system 提示 ([#4937](https://github.com/Arize-ai/phoenix/issues/4937)) ([5f28ef2](https://github.com/Arize-ai/phoenix/commit/5f28ef244db2c4dd59fad6c6d6f1b63ff235817b))

## [0.16.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.16.0...arize-phoenix-evals-v0.16.1) (2024-09-27)

<a id="bug-fixes-44"></a>

### 问题修复

- 标准模板分隔符使用 Python 字符串格式化 ([#4781](https://github.com/Arize-ai/phoenix/issues/4781)) ([26b422f](https://github.com/Arize-ai/phoenix/commit/26b422f70dd5e7b295f79a30a82dab1cc1ed9173))

## [0.16.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.15.1...arize-phoenix-evals-v0.16.0) (2024-09-17)

<a id="features-38"></a>

### 新功能

- OpenAI 支持 o1 preview ([#4633](https://github.com/Arize-ai/phoenix/issues/4633)) ([1ad7b79](https://github.com/Arize-ai/phoenix/commit/1ad7b79d95bd362ca15f34f2cebe7e1332a19846))

<a id="bug-fixes-45"></a>

### 问题修复

- 确保 dataloader 结果顺序正确 ([#4524](https://github.com/Arize-ai/phoenix/issues/4524)) ([f9239d6](https://github.com/Arize-ai/phoenix/commit/f9239d63af9d06c04430f9dca808caf08d152d3d))

## [0.15.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.15.0...arize-phoenix-evals-v0.15.1) (2024-08-27)

<a id="bug-fixes-46"></a>

### 问题修复

- 支持 2.4.1&lt;=pydantic<=2.7.1 范围内的 pydantic ([#4323](https://github.com/Arize-ai/phoenix/issues/4323)) ([fa5eeff](https://github.com/Arize-ai/phoenix/commit/fa5eeff45b0752508d4bc51334607ef4acc19474))

## [0.15.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.14.1...arize-phoenix-evals-v0.15.0) (2024-08-15)

<a id="features-39"></a>

### 新功能

- 公开初始速率限制配置 ([#4087](https://github.com/Arize-ai/phoenix/issues/4087)) ([194a66d](https://github.com/Arize-ai/phoenix/commit/194a66d6315ffd93275e1a8e19560a435701ddc8))

<a id="bug-fixes-47"></a>

### 问题修复

- 为 span 标注使用 dataloader ([#4139](https://github.com/Arize-ai/phoenix/issues/4139)) ([2456ad4](https://github.com/Arize-ai/phoenix/commit/2456ad47c6cb73901152bec5b4bfed8c77c96933))

<a id="documentation-14"></a>

### 文档

- 更新 API 参考并修复文档字符串 ([e089f99](https://github.com/Arize-ai/phoenix/commit/e089f99fa2e63cdf9cb342bc3810361947c28e61))
- 修复文档字符串 ([#3969](https://github.com/Arize-ai/phoenix/issues/3969)) ([f6a5b62](https://github.com/Arize-ai/phoenix/commit/f6a5b62a1f53ba34d22c678e7bbb314693641993))
- 更新 LiteLLM 和 OpenAI 文档字符串 ([#3910](https://github.com/Arize-ai/phoenix/issues/3910)) ([be57127](https://github.com/Arize-ai/phoenix/commit/be5712761a1eb59c73ca38bc207f9e6078bf60f6))

## [0.14.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.14.0...arize-phoenix-evals-v0.14.1) (2024-07-16)

<a id="bug-fixes-48"></a>

### 问题修复

- 异步时在执行器中运行 Bedrock 调用 ([#3884](https://github.com/Arize-ai/phoenix/issues/3884)) ([46e3b1c](https://github.com/Arize-ai/phoenix/commit/46e3b1c7c705e6fd6df7cdcc10f1ec0f14efb03c))

## [0.14.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.13.2...arize-phoenix-evals-v0.14.0) (2024-07-12)

<a id="features-40"></a>

### 新功能

- 为 span_templates.py 和教程 notebook 新增函数调用评估器模板

<a id="bug-fixes-49"></a>

### 问题修复

- 确保实验错误消息适用于 Python 3.8 和 3.9 ([#3840](https://github.com/Arize-ai/phoenix/issues/3840)) ([25a7fb9](https://github.com/Arize-ai/phoenix/commit/25a7fb93fe7512a0ac2da9a59915c9e145c58ae2))

<a id="documentation-15"></a>

### 文档

- 更新模型包装器文档字符串 ([#3834](https://github.com/Arize-ai/phoenix/issues/3834)) ([531360b](https://github.com/Arize-ai/phoenix/commit/531360b4f1a7180c892504ffbc567d78503283f2))

## [0.13.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.13.1...arize-phoenix-evals-v0.13.2) (2024-07-03)

<a id="bug-fixes-50"></a>

### 问题修复

- 允许不提供 API 密钥调用 OpenAIModel ([#3820](https://github.com/Arize-ai/phoenix/issues/3820)) ([4dd8c0e](https://github.com/Arize-ai/phoenix/commit/4dd8c0e15308971fe42c5fd11f04f80b18c55746))

## [0.13.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.13.0...arize-phoenix-evals-v0.13.1) (2024-06-30)

<a id="bug-fixes-51"></a>

### 问题修复

- 调整警告消息中的 llm_classify ([#3752](https://github.com/Arize-ai/phoenix/issues/3752)) ([717a0c7](https://github.com/Arize-ai/phoenix/commit/717a0c786b1aa78000d6bc3e47f369bbba7662a3))

## [0.13.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.12.0...arize-phoenix-evals-v0.13.0) (2024-06-26)

<a id="features-41"></a>

### 新功能

- 新增 SQLEvaluator ([#3577](https://github.com/Arize-ai/phoenix/issues/3577)) ([0a79535](https://github.com/Arize-ai/phoenix/commit/0a79535f20426072c8ffa60960b605a8dbb95a18))

<a id="bug-fixes-52"></a>

### 问题修复

- 支持查询日期时间 ([#3439](https://github.com/Arize-ai/phoenix/issues/3439)) ([90fd619](https://github.com/Arize-ai/phoenix/commit/90fd61927d11a0eaf151ca41b81f149b9fc8214f))
- 解决评估模型 GeminiModel 的身份验证问题 ([#3662](https://github.com/Arize-ai/phoenix/issues/3662)) ([b79d946](https://github.com/Arize-ai/phoenix/commit/b79d946cebd7447bcda7edbdf23603a2ceef5f03))

## [0.12.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.11.0...arize-phoenix-evals-v0.12.0) (2024-06-06)

<a id="features-42"></a>

### 新功能

- 新增用于评估幻觉和问答正确性的 span 级模板 ([#3380](https://github.com/Arize-ai/phoenix/issues/3380)) ([1689b49](https://github.com/Arize-ai/phoenix/commit/1689b49cfa3ea99d39bd98873580e5253101a0c7))
- 为 llm_classify 新增耗时信息 ([#3377](https://github.com/Arize-ai/phoenix/issues/3377)) ([3e2785f](https://github.com/Arize-ai/phoenix/commit/3e2785f7d53dd628e7027fe988ae066fa1be0da1))

## [0.11.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.10.0...arize-phoenix-evals-v0.11.0) (2024-05-31)

<a id="features-43"></a>

### 新功能

- 允许模板映射错误时跳过，并返回调试信息 ([#3350](https://github.com/Arize-ai/phoenix/issues/3350)) ([dc18123](https://github.com/Arize-ai/phoenix/commit/dc1812379c33fbb89537c6aed6361f808f29ec73))
- 支持序列化执行详情 ([#3358](https://github.com/Arize-ai/phoenix/issues/3358)) ([fc74513](https://github.com/Arize-ai/phoenix/commit/fc7451372c9b938a27c7b36f7e32704f7b3a8e87))

## [0.10.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.9.2...arize-phoenix-evals-v0.10.0) (2024-05-29)

<a id="features-44"></a>

### 新功能

- Docker 镜像默认以 root 运行，并提供 nonroot 和 debug 镜像标签 ([#3280](https://github.com/Arize-ai/phoenix/issues/3280)) ([41a4826](https://github.com/Arize-ai/phoenix/commit/41a4826733e104a3ec533a73049df5b778391e7f))
- 支持 Mistral ([#3270](https://github.com/Arize-ai/phoenix/issues/3270)) ([4e38531](https://github.com/Arize-ai/phoenix/commit/4e3853159881fa936d04beff5feb971df72ad038))

## [0.9.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.9.1...arize-phoenix-evals-v0.9.2) (2024-05-21)

<a id="bug-fixes-53"></a>

### 问题修复

- 在线程中运行时绕过信号处理器 ([#3251](https://github.com/Arize-ai/phoenix/issues/3251)) ([8c82306](https://github.com/Arize-ai/phoenix/commit/8c8230606d173a55a2f84b2fbdbb48e920cbdb70))

## [0.9.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.9.0...arize-phoenix-evals-v0.9.1) (2024-05-21)

<a id="bug-fixes-54"></a>

### 问题修复

- 明确缺少 Azure API 密钥的错误消息 ([#3256](https://github.com/Arize-ai/phoenix/issues/3256)) ([58a1398](https://github.com/Arize-ai/phoenix/commit/58a1398b4f1fcc64af7fdb06463f9a0fc0f53b76))

## [0.9.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.8.2...arize-phoenix-evals-v0.9.0) (2024-05-17)

<a id="features-45"></a>

### 新功能

- 为 azure_openai 新增 default_headers 支持。 ([#3211](https://github.com/Arize-ai/phoenix/issues/3211)) ([2d48192](https://github.com/Arize-ai/phoenix/commit/2d48192d57a1b97e4b08efc30f5c689423667c93))

## [0.8.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.8.1...arize-phoenix-evals-v0.8.2) (2024-05-14)

<a id="bug-fixes-55"></a>

### 问题修复

- 修正评估器类型提示 ([#3195](https://github.com/Arize-ai/phoenix/issues/3195)) ([7d57e2e](https://github.com/Arize-ai/phoenix/commit/7d57e2e760a98095c57b45b3e39e2d009972faaf))

## [0.8.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.8.0...arize-phoenix-evals-v0.8.1) (2024-05-03)

<a id="bug-fixes-56"></a>

### 问题修复

- **evals:** 修正幻觉评估措辞 ([#3085](https://github.com/Arize-ai/phoenix/issues/3085)) ([7aa0292](https://github.com/Arize-ai/phoenix/commit/7aa029239c2c36b677070e270f7127f6bf6cff5e))

## [0.8.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.7.0...arize-phoenix-evals-v0.8.0) (2024-04-22)

<a id="features-46"></a>

### 新功能

- 新增用户挫败感评估 ([#2928](https://github.com/Arize-ai/phoenix/issues/2928)) ([406938b](https://github.com/Arize-ai/phoenix/commit/406938b1f19ee6efb7cec630772d9d8940c0953f))

## [0.7.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.6.1...arize-phoenix-evals-v0.7.0) (2024-04-12)

<a id="features-47"></a>

### 新功能

- 新增 SQL 和代码功能评估模板 ([#2861](https://github.com/Arize-ai/phoenix/issues/2861)) ([c7d776a](https://github.com/Arize-ai/phoenix/commit/c7d776a23e1843cc1bb5c74059496615700a3396))

## [0.6.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.6.0...arize-phoenix-evals-v0.6.1) (2024-04-04)

<a id="bug-fixes-57"></a>

### 问题修复

- 切换 TOML 中的许可格式 ([5c6f345](https://github.com/Arize-ai/phoenix/commit/5c6f345691dcab3d460823329ce31b9060bab02c))

## [0.6.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.5.0...arize-phoenix-evals-v0.6.0) (2024-03-29)

<a id="features-48"></a>

### 新功能

- 更新 bedrock.py，为 Claude 使用 messages API ([#2636](https://github.com/Arize-ai/phoenix/issues/2636)) ([3d7d91a](https://github.com/Arize-ai/phoenix/commit/3d7d91ac6f399ceb40771461cd1fc7bfe60ff04f))

## [0.5.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.4.0...arize-phoenix-evals-v0.5.0) (2024-03-20)

<a id="features-49"></a>

### 新功能

- 为 `MistralAIModel` 新增 `response_format` 参数 ([#2660](https://github.com/Arize-ai/phoenix/issues/2660)) ([7da51af](https://github.com/Arize-ai/phoenix/commit/7da51afc77984925cd59d7d909142141530684cc))

## [0.4.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.3.1...arize-phoenix-evals-v0.4.0) (2024-03-20)

<a id="features-50"></a>

### 新功能

- **evals:** 新增 Mistral 作为评估模型 ([#2640](https://github.com/Arize-ai/phoenix/issues/2640)) ([c13ab6b](https://github.com/Arize-ai/phoenix/commit/c13ab6bf644ec285c37e92cc6a7b114a309cec52))

## [0.3.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.3.0...arize-phoenix-evals-v0.3.1) (2024-03-15)

<a id="bug-fixes-58"></a>

### 问题修复

- 向评估器传递 verbose ([#2597](https://github.com/Arize-ai/phoenix/issues/2597)) ([9467e1d](https://github.com/Arize-ai/phoenix/commit/9467e1deabe58c0079ad8bdb9dfc972ee2ae5c0b))

## [0.3.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.2.0...arize-phoenix-evals-v0.3.0) (2024-03-13)

<a id="features-51"></a>

### 新功能

- phoenix-evals 支持 Python 3.12 ([#2554](https://github.com/Arize-ai/phoenix/issues/2554)) ([efb6a76](https://github.com/Arize-ai/phoenix/commit/efb6a764a2aaecfff271b2cd7b7569771989a6a1))

## [0.2.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.1.0...arize-phoenix-evals-v0.2.0) (2024-03-07)

<a id="features-52"></a>

### 新功能

- 更新 `AnthropicModel` 以使用 `messages` API ([#2489](https://github.com/Arize-ai/phoenix/issues/2489)) ([5aa3842](https://github.com/Arize-ai/phoenix/commit/5aa3842d3e3d8a1fe21fb62c594032474899fb81))

<a id="bug-fixes-59"></a>

### 问题修复

- `llm_generate` 构造输出时保留输入索引 ([#2441](https://github.com/Arize-ai/phoenix/issues/2441)) ([ee36987](https://github.com/Arize-ai/phoenix/commit/ee369874649ac36fadcce3322cf87cf22d04aed4))

## [0.1.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.0.5...arize-phoenix-evals-v0.1.0) (2024-03-05)

<a id="features-53"></a>

### 新功能

- 从 `phoenix.evals` 移除 token 处理模块 ([#2421](https://github.com/Arize-ai/phoenix/issues/2421)) ([fbd4961](https://github.com/Arize-ai/phoenix/commit/fbd496163d6cf46b3299da4ac7962b19da054bd8))

<a id="bug-fixes-60"></a>

### 问题修复

- 正确定义 `BedrockModel` ([#2425](https://github.com/Arize-ai/phoenix/issues/2425)) ([81a720c](https://github.com/Arize-ai/phoenix/commit/81a720c8264f80fc37fcfe76c1c982014e9f12b3))
- 修复源码分发构建 ([#2407](https://github.com/Arize-ai/phoenix/issues/2407)) ([1e67d7e](https://github.com/Arize-ai/phoenix/commit/1e67d7e4eb037f85b1e33e59b42014fe3daa876d))

## [0.0.5](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.0.4...arize-phoenix-evals-v0.0.5) (2024-02-24)

<a id="bug-fixes-61"></a>

### 问题修复

- **evals:** 导出参考链接模板 ([#2393](https://github.com/Arize-ai/phoenix/issues/2393)) ([d9e21b7](https://github.com/Arize-ai/phoenix/commit/d9e21b7cb6f4c9cc9c863623696f3987f96dd174))

## [0.0.4](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.0.3...arize-phoenix-evals-v0.0.4) (2024-02-24)

<a id="bug-fixes-62"></a>

### 问题修复

- 导出参考链接模板 ([#2390](https://github.com/Arize-ai/phoenix/issues/2390)) ([d5e4121](https://github.com/Arize-ai/phoenix/commit/d5e41213e897bfb64e121a72b85c614b29e1358c))

## [0.0.3](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-evals-v0.0.2...arize-phoenix-evals-v0.0.3) (2024-02-23)

<a id="bug-fixes-63"></a>

### 问题修复

- 移除 run_relevance_evals 并修复导入问题 ([#2375](https://github.com/Arize-ai/phoenix/issues/2375)) ([9a97e62](https://github.com/Arize-ai/phoenix/commit/9a97e6251cddf4ca7aa03ba71d4831cb0de4a165))

<a id="documentation-16"></a>

### 文档

- **evals:** 新增 README ([#2363](https://github.com/Arize-ai/phoenix/issues/2363)) ([47842da](https://github.com/Arize-ai/phoenix/commit/47842da560f004944852ea1071edf30eb3993ac8))

## [0.0.2](https://github.com/Arize-ai/phoenix/compare/phoenix-evals-v0.0.1...phoenix-evals-v0.0.2) (2024-02-22)

<a id="features-54"></a>

### 新功能

- 将 `phoenix.experimental.evals` 提取为独立 `phoenix.evals` 包 ([#2142](https://github.com/Arize-ai/phoenix/issues/2142)) ([7b63431](https://github.com/Arize-ai/phoenix/commit/7b63431ee329a3916a9898e1437efef0added22f))

<a id="bug-fixes-64"></a>

### 问题修复

- 软件包在 pyproject.toml 使用静态版本 ([#2346](https://github.com/Arize-ai/phoenix/issues/2346)) ([ef2148c](https://github.com/Arize-ai/phoenix/commit/ef2148c18bbbece08755fdee58f66c50ab6a7de8))
