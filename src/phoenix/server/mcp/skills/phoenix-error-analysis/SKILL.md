---
name: phoenix-error-analysis
description: 通过读取抽样的 Phoenix 追踪、跨度或会话，编写自由文本笔记（开放式编码），再将笔记归纳为少量范围明确的标注，发现 LLM 或智能体流量中的问题。每个失败维度使用小规模标签集并统计数量，以选择评估目标和修复优先级（主轴编码）。适用于“智能体哪里出问题了”“刚给应用接入插桩，从哪里开始”“检查这些追踪”“聊天机器人不断丢失上下文”“模型犯了哪些错误”“有哪些失败类别”“应该为哪些问题构建评估”“如何安排修复优先级”“归纳这些笔记”“MECE 拆解”等请求；凡是需要以真实追踪为依据形成观察或类别，而非自上而下凭空分类的任务，即使未提及技术名称，也应使用。
summary: 读取抽样追踪并记录开放式编码笔记，再将其归纳为范围明确的单维度标注，统计数量以选择评估目标和修复优先级。
license: Apache-2.0
metadata:
  author: arize-ai
  version: "1.0.0"
---

<a id="error-analysis"></a>

# 错误分析

对抽样的追踪、跨度或会话执行两个阶段。**开放式编码**逐个读取抽样实体，用简短具体的笔记记录出了什么问题。**主轴编码**将笔记归纳为少量范围明确的标注，每个标注只判断实体的一个维度，使用小规模标签集，并统计标签数量，供评估设计和修复排序使用。必须先开放式编码：没有笔记依据的维度和标签属于自上而下编造，正是此流程要避免的失败方式。主轴编码也可以从已有的任意一组开放式观察开始。

**已记录的笔记就是交付物。** 开放式编码的结束标准是：为每个有问题的实体将一条笔记写入服务端，并同步到本地伴随文件，而非只在聊天中总结。读取追踪后仅报告发现、不写任何记录，是只读诊断，也是此流程要替代的自上而下捷径。“查找问题”“哪里出错了”“这里有错误吗”等项目级问题，就是要求执行阶段 1：选择标识符和分析单位，每发现一个问题就记录笔记，最后再总结。项目还没有标注名称是正常起点，不能作为不写入的理由。

<a id="choosing-the-unit-of-analysis"></a>

## 选择分析单位

记录前应有意识地选择**追踪、跨度或会话**。此选择决定后续每条笔记和标注针对什么，中途撤销错误默认值成本很高。分析单位应与所调查失败模式实际发生的层级一致：

- **追踪**：一次输入到一次输出，例如分类器、单次摘要、无状态工具智能体、单次查询 RAG。
- **跨度**：追踪中的一个操作，例如可孤立分析的机械性失败（异常、工具错误响应、输出格式错误），或一眼即可归因于某个组件的失败。
- **会话**：共享 `session.id` 的一串追踪。适用于多轮智能体中只在多条追踪之间才出现的轨迹问题，例如跨轮上下文丢失、目标偏移、忘记偏好。

读取三类信号：

1. **用户表述。** “对话”“智能体忘记了”“偏移”“跨轮”指向会话；“这条追踪”“输出错误”指向追踪；“异常”“格式错误”“检索失败”指向跨度。
2. **会话关联。** 会话 ID 位于根跨度的 `session.id` 属性，不在追踪顶层；`""` 表示缺失。列出约 200 条最近追踪，统计非空会话 ID 的条数、不同会话 ID 数，以及每个会话追踪数的中位数。没有会话 ID 或中位数为 1 时，使用追踪或跨度层级；中位数为 2 或以上时，会话层级可能更合适。
3. **轮次结构。** 打开最近一条追踪根跨度的 `input.value`，内容可能很大，应筛选而非整体读取。单条用户消息表示单次请求；消息数组（`[{role: user}, {role: assistant}, ...]`）表示会话级对话中的一轮。

记录任何笔记前，明确说明所选单位。数据需要时可以调整：追踪级笔记持续发现“智能体从不记得前几轮”，下一批应转为会话分析。分析单位是起始假设，不是固定契约。

<a id="coding-annotation-identifier-pick-this-first"></a>

## 编码标注标识符（首先选择）

此流程生成的所有产物，包括开放式编码笔记、主轴编码标签和本地伴随文件，都使用同一个**编码标注标识符**，使整次运行可统一查询和撤销。记录前选择描述清楚且唯一的值，例如 `coding-run:chatbot-context-loss-2026-05-06`。`coding-run:` 前缀只是命名约定，不是 Phoenix 会话 ID。

每次服务端写入都显式传入标识符。可使用 shell 变量提高可读性，但不能依赖 shell 继承，因为许多智能体运行框架会为每条命令启动新的子 shell。

本地伴随文件相对于当前工作目录，位于 `.px/coding/<sanitized-identifier>.jsonl`（开放式笔记）和 `.px/coding/<sanitized-identifier>-axial.jsonl`（主轴标签）。净化时，将 `[a-zA-Z0-9_-]` 以外的字符全部替换为 `-`。唯一性通过**本地文件检查**确认，不查询服务端：

```bash
CODING_ANNOTATION_IDENTIFIER="coding-run:chatbot-context-loss-2026-05-06"
SLUG=$(echo -n "$CODING_ANNOTATION_IDENTIFIER" | sed 's/[^a-zA-Z0-9_-]/-/g')
NOTES_SIDECAR=".px/coding/${SLUG}.jsonl"
AXIAL_SIDECAR=".px/coding/${SLUG}-axial.jsonl"
test ! -f "$NOTES_SIDECAR" || { echo "Sidecar already exists at $NOTES_SIDECAR — pick a new identifier or delete the file"; exit 1; }
mkdir -p .px/coding
```

如果 `$NOTES_SIDECAR` 已存在，追加区分后缀，例如 `-v2`、`-dustin`，然后重新检查。

**恢复运行**：两个阶段可以独立调用。在新 shell 中开始主轴编码时，必须将标识符设为开放式编码时选定的同一值，可从结束时的界面 URL 或 `.px/coding/*.jsonl` 文件列表恢复；跳过唯一性检查，并据此重新推导伴随文件路径。运行中绝不能另建标识符。

<a id="where-the-writes-go"></a>

## 写入位置

以下步骤描述的是操作，而非具体命令。有两种实现方式，使用运行框架提供的即可。`phoenix-cli` 技能说明 `px` 选项；`phoenix-graphql` 技能的参考文件（`project-spans-traces.md`、`sessions.md`、`annotations.md`）说明 GraphQL 字段和变更输入。本技能不附带自己的参考文件。

| 操作 | Phoenix CLI（`px`） | GraphQL（`phoenix-gql` 或任意客户端） |
| --- | --- | --- |
| 抽样、展开、深入查看 | `px trace list`、`px trace get <trace-id>`、`px span get <span-id>`、`px session get <session-id>` | `Project.spans(filterCondition: "parent_span is None")`、`getTraceByOtelId`、`getSpanByOtelId`，会话使用 `node(id:)` |
| 检查已有笔记 | `get`/`list` 的 `--include-notes` | `Span.spanNotes`；`Trace.traceAnnotations` / `ProjectSession.sessionAnnotations` 中 `name == "note"` 的条目 |
| 写入笔记 | `px trace add-note <trace-id> --text "..." --identifier "$CODING_ANNOTATION_IDENTIFIER"`，也可用 `px span add-note`、`px session add-note` | `createTraceNotes`、`createSpanNotes`、`createProjectSessionNotes`，各自接收 `{ note, annotatorKind: LLM, source: API, identifier }`，以及 OTel ID（`{ otelId }`）或节点 ID（`{ id }`）实体引用 |
| 写入主轴标注 | `px trace annotate <trace-id> --name <annotation-name> --label <label> --identifier "$CODING_ANNOTATION_IDENTIFIER"`，也支持 `span`、`session` | `createTraceAnnotations`、`createSpanAnnotations`、`createProjectSessionAnnotations`，仅接收 Phoenix 节点 ID，并提供 `name`、`label`、`explanation`、`annotatorKind: LLM`、`source: API`、`metadata: {}`、`identifier` |
| 标注配置 | `px annotation-config list`、`create`、`update <identifier>` | `createAnnotationConfig`、`updateAnnotationConfig`、`addAnnotationConfigToProject` |
| 丢弃运行 | `px trace-annotations delete --identifier "$CODING_ANNOTATION_IDENTIFIER" --all -y`，也支持 `span-annotations`、`session-annotations` | 没有按标识符筛选清除的接口，先收集该运行标注的节点 ID，再调用 `deleteTraceAnnotations`、`deleteSpanAnnotations`、`deleteProjectSessionAnnotations` |

笔记和标注写入同步执行，并按 `(entity, name, identifier)` 更新或插入。运行框架通过审批步骤控制变更时，应说明每条命令会写什么，并让每次变更独立调用。

<a id="phase-1-open-coding"></a>

## 阶段 1：开放式编码

自由编写笔记，记录实际看到的内容，不要预先归类，分类属于阶段 2。

<a id="process"></a>

### 过程

1. **选择编码标注标识符**，确认伴随文件尚不存在。
2. **选择单位**：追踪、跨度或会话。
3. **检查**：获取所选单位的一个实体，读取输入、输出、异常、工具调用、检索上下文，以及会话级子追踪之间的执行轨迹。
4. **记笔记**：用一句具体的话描述问题，正确则跳过。
5. **记录**：将笔记写入服务端，并追加一行伴随记录。
6. **迭代**：直到样本耗尽或观察饱和。

<a id="inspection"></a>

### 检查

- **追踪单位**：将一条追踪的输入 → 工具调用 → 检索上下文 → 输出作为完整故事阅读。
- **跨度单位**：读取单个操作的输入输出，并查看周围跨度以获取上下文。
- **会话单位**：按顺序读取追踪序列；数据是跨追踪的轨迹，而非任意单条追踪。

> **不要按跨度状态 `ERROR` 抽样。** 只有插桩器捕获抛出的异常时，OTel 的 `status_code` 才变为 `ERROR`。幻觉、语气错误、检索遗漏和工具选择错误都会以 `OK` 或 `UNSET` 正常完成；只筛选错误状态会排除此流程真正要发现的样本。

<a id="what-to-look-for"></a>

#### 检查内容

以下是检查清单，不是分类体系，类别应稍后形成。记录最先出错的地方；下游症状只有存在独立原因时才单独记笔记。

- **显式错误**：工具、LLM 或检索跨度中的异常或错误消息。
- **费用与延迟**：异常高的令牌数或缓慢跨度。
- **检索质量**：不相关、缺失或低分的片段。
- **回复质量**：幻觉、事实错误、语气错误、不恰当拒绝。
- **工具使用**：选错工具、调用格式错误、结果处理不当。
- **执行轨迹**：循环、绕路、任务未完成；会话中的上下文丢失或目标偏移。
- **插桩缺口**：跨度或属性缺失，盲点本身也是发现。

已有评估和标注只是多个输入来源之一。读取内容，而非只看状态：成功状态可能在属性中隐藏错误，异常也可能是预期行为。

无论使用哪种工具，都要执行这些获取步骤：**抽样**最近追踪，包含追踪 ID、根跨度名称、状态、根跨度 `input.value` / `output.value`；**展开**一条追踪，按开始时间查看跨度；单位为跨度时，按 ID **深入查看**单个跨度；并**检查已有笔记**，笔记以保留名称 `note` 的标注存储在服务端。数据可能冗长，应避免撑爆上下文。

<a id="recording-notes"></a>

### 记录笔记

对检查的每个会话、追踪或跨度，向服务端提交笔记（见[写入位置](#where-the-writes-go)），并保留本地副本。每次写入都应带笔记正文，并显式将 `identifier` 设为编码标注标识符。逐个实体随查随记，不要将笔记攒到最后总结。

每次成功向服务端写入笔记后，向 `$NOTES_SIDECAR` 追加一行 JSONL；主轴编码直接读取此伴随文件，无需往返服务端：

```json
{"entity_kind":"trace","entity_id":"<trace-id>","note":"<text>","identifier":"<original identifier value, unsanitized>","ts":"<ISO-8601 UTC>"}
```

<a id="what-makes-a-good-note"></a>

### 好笔记的特征

| 较弱笔记 | 好笔记 |
| --- | --- |
| “答案错误” | “声称商店下午 6 点关门，但政策规定晚上 9 点” |
| “检索有问题” | “问题询问退货，却检索到了配送文档” |

<a id="saturation"></a>

### 观察饱和

当观察不再出现新内容时停止：最后 10–15 个实体重复已有失败，你开始换句话复述先前笔记，或跳过数超过笔记数。收集期间不要急着归类。不必标注每条追踪，给正确追踪作标注会稀释信号。

<a id="between-phases-proceed-or-offer"></a>

## 阶段之间：继续还是询问

达到饱和后，决定是否继续主轴编码：

- 用户要求类别、分类体系、数量、评估目标或修复优先级，或将任务表述为端到端错误分析时，直接继续阶段 2。
- 否则在此停止，先总结笔记揭示的内容，再提议继续主轴编码，并等待用户回答，不要直接开始。若运行在此结束，遵循[收尾](#wrapping-up)。

<a id="phase-2-axial-coding"></a>

## 阶段 2：主轴编码

将开放式笔记转为一小组**各自只判断实体一个维度的标注**：每个标注回答一个行为问题，只有少量标签。实体在笔记涉及的每个维度上各带一个标注，因此一条追踪可能有两三个。输出应是多个范围明确、各含二到四个标签的标注，不能是一个标签横跨无关问题的宽泛 `<app>_failure_mode` 标注。宽泛标注无法按维度汇总，无法被只判断一件事的评估复用，还会迫使同时存在两类失败的实体只选一个标签。

<a id="process-1"></a>

### 过程

1. **设置编码标注标识符**为开放式编码时的值，并推导伴随文件路径，见[恢复运行](#coding-annotation-identifier-pick-this-first)。
2. **收集**：从 `$NOTES_SIDECAR` 读取本次笔记。文件不存在，表示当前工作目录下尚未为此标识符执行开放式编码，应停止并先运行阶段 1。每个实体以最新 `ts` 为准；格式错误的行应单独修复或删除，不碰相邻行。要包含其他评审者或早先运行的笔记，从服务端读取保留名称 `note` 的标注。
3. **分组**：将回答同一实体问题的笔记聚为一类，如“是否选对工具”“答案是否忠于检索内容”“是否完成要求的任务”。每组是一个候选维度。必须由笔记自下而上形成，不能先列维度。
4. **定义**：按每个维度提出的问题命名标注，如 `tool_selection`、`answer_faithfulness`，标签包括笔记描述的失败结果和一个通过值，使后续评估也能标注成功实体。同一维度的标签应互斥；两个标签若可能同时适用于同一实体，就属于不同维度。
5. **归因**：判断各维度属于哪个层级，见[选择层级](#choosing-the-level)。
6. **配置**：每个维度注册一个分类标注配置，见[标注配置](#annotation-configs)。
7. **记录**：针对每个有笔记的实体，在笔记涉及的每个维度写入一个标注，并为每条标注追加一行伴随记录。
8. **量化**：从 `$AXIAL_SIDECAR` 按维度统计标签，按 `(annotation_name, axial_label)` 分组，每个 `(entity, annotation_name)` 取最新 `ts`。不查询服务端，伴随文件恰好包含本次运行写入的标签。

<a id="shaping-the-dimensions"></a>

### 塑造维度

- **每个标注一个问题。** 名称是问题（`tool_selection`），标签是答案（`hallucinated_tool`）。同时判断工具选择和运行框架稳定性，应拆成两个标注。
- **小规模标签集。** 通常二到四个标签。超过约五个标签，几乎总是混合了多个维度，应拆分。
- **标签是结果，不是组件。** `retrieval` 或 `tool_use` 是维度名，不是标签。如果标签像系统某个部分的名词，应提升为独立标注，并将其结果作为标签。
- **一次运行产生少量维度。** 通常三到六个。每条笔记应至少映射到一个维度的标签；无处归属的笔记意味着新维度，或现有维度定义太窄。
- **分开智能体判断与基础设施。** 供应商错误、持久化失败、界面崩溃都是实际发现，但不是智能体行为，应有独立维度，不能和模型错误并列成同一类标签。

<a id="choosing-the-level"></a>

### 选择层级

主轴编码默认继承开放式编码的单位，但标注可以向任意方向归因到其他层级。追踪级“问退货却回答配送”的笔记，如果持续指向检索问题，可以在检索跨度上生成跨度级 `retrieval_relevance` 标签；追踪级单轮混淆笔记，如果模式是“不跟踪跨轮上下文”，可以生成会话级 `context_tracking` 标签；会话级偏移笔记也可以归因于具体轮次，生成追踪级标签。每条标注都应写在维度实际涉及的层级，同一次运行的不同维度可以属于不同层级。

对已经记笔记的实体分类，候选来源是 `$NOTES_SIDECAR`，必须读取笔记正文和周围上下文后才写标签。**不要**按错误状态选择实体，否则只能捕获抛出的异常，排除大多数失败模式，如幻觉、语气错误、检索遗漏。

<a id="annotation-configs"></a>

### 标注配置

维度稳定后，即完成分组和定义之后、而非每次写入时，在记录前为**每个维度注册一个分类标注配置**：

1. **按维度命名配置。** 配置与标注共享名称，如 `tool_selection`、`answer_faithfulness`，Phoenix 据此关联。不能使用笼统的 `category`，也不能用一个配置打包全部维度。
2. **检查项目已有标注配置。** 已有配置判断同一维度时，复用其名称和标签，只有笔记发现缺失的结果时才扩展值，不要换名字创建近似重复配置。
3. **创建或更新**各配置，以该维度的最终标签作为值，并关联到项目。

没有配置也能写入标注，但配置让维度成为 Phoenix 界面中的正式对象：人工标注人员通过下拉列表选择标签，而非自由输入；后续运行继承共享词汇，避免漂移。记录过程中出现新标签时，应先添加到该维度配置，再用它写入。

<a id="what-makes-a-good-annotation"></a>

### 好标注的特征

标注只有可筛选、可汇总、可审计，后续才有用。因此：

1. **名称表达维度，标签表达结果。** 使用 `tool_selection` = `hallucinated_tool`，而非 `hallucinated_tool` = `true`，也非 `failure_mode` = `hallucinated_tool`。
2. **每个标注一个维度。** 判断相关性与忠实性需要两个标注，判断工具选择与任务完成也一样。
3. **标注责任实体。** 检索问题标在检索跨度，输出问题标在 LLM 跨度；只有端到端判断才标在追踪或会话。
4. **标注最先发生的失败。** 下游影响只有构成独立问题时才单独标注。
5. **优先标签而非分数。** 小规模标签集更容易一致应用和清晰汇总；只有配置定义了量表时才用分数。
6. **解释中引用证据。** 应写“询问取消服务，却检索到入门文档”，而非“检索很差”。
7. **跨运行保持名称和标签稳定。** 不添加 `_v2` 后缀，也不能仅因名称相符就借用其他项目配置。

<a id="recording-labels"></a>

### 记录标签

对每个实体及笔记涉及的每个维度，写入一个标注，包含：

- **name**：该维度标注名，例如 `retrieval_relevance`
- **label**：结果，例如 `off_topic`
- **explanation**（可选）：例如“问退货，检索到了配送文档”
- **annotator kind**：自己的判断使用 `LLM`，只有用户提供的判断才用 `HUMAN`
- **identifier**：编码标注标识符

服务端也接受可选分数。写入按 `(entity_id, name, identifier)` 更新或插入，因此同一实体在同一标识符下可以有多个不同名称的标注。服务端默认写入模式是异步入队；工具提供同步模式时优先使用，使记录在继续前已实际应用。

每次写入后，向 `$AXIAL_SIDECAR` 追加一行 JSONL，每个标注一行，因此在两个维度上被标注的实体有两行：

```json
{"entity_kind":"trace","entity_id":"<trace-id>","annotation_name":"<annotation-name>","axial_label":"<label>","explanation":"<optional explanation>","identifier":"<original identifier value, unsanitized>","ts":"<ISO-8601 UTC>"}
```

`entity_kind`（`"trace"`、`"span"` 或 `"session"`）匹配标注实际写入的层级；`identifier` 是**原始**未净化值，净化形式只用于文件名。修订标签时，可以替换行或追加新行；每个 `(entity_kind, entity_id, annotation_name)` 以最新 `ts` 为当前值，与服务端更新或插入一致。

<a id="example-dimensions"></a>

### 维度示例

每个键是标注名，其值是该标注的标签。一次运行产生其中少数几个，而不是一棵分类树。

```yaml
tool_selection: [correct, wrong_tool, hallucinated_tool, unnecessary_call]
retrieval_relevance: [relevant, off_topic, nothing_retrieved]
answer_faithfulness: [grounded, invented_fact, invented_citation]
context_tracking: [kept, ignored_preference, goal_drift]
task_completion: [completed, partial, abandoned]
```

<a id="what-makes-a-good-dimension"></a>

### 好维度的特征

- **只问一个问题**，答案相互排斥；两个标签若可同时适用，就应拆成两个维度。
- **按被判断的行为命名**，结果放在标签中，如 "tool_selection" = "wrong_tool"，而非 "bad_output"。
- **关联修复措施**：无法为失败标签说出补救办法，说明维度太含糊。
- **以数据为依据**：来自真实笔记，而非事先假定。

<a id="wrapping-up"></a>

## 收尾

无论运行在阶段 1 还是阶段 2 后结束，都适用。

如果执行了主轴编码，列出写入的维度，并逐一说明其标注配置是复用、扩展还是新建，让用户判断评分规则。将维度链接到项目配置页面 `<endpoint>/projects/<project-node-id>/config`，该页面在项目标注旁列出其标注配置；不要链接实例级标注设置页，那里混合了其他项目配置。

向用户分享 Phoenix 界面链接：本次运行实际写入笔记或标注的每个层级——跨度、追踪、会话——各给一个链接，筛选到本次工作；没有记录的层级跳过。每个标签页通过自己的查询参数读取筛选条件；未知或拼错的参数会被静默丢弃，导致表格未筛选。

按编码标注标识符筛选，标注访问器除 `.label`、`.score`、`.explanation` 外也提供 `.identifier`，从而每个链接只展示本次笔记和主轴标注。该层级每写入一个维度，就增加一个 `<annotation-name>` 子句，以 `or` 连接；未执行主轴编码时省略这些子句：

| 标注层级 | 标签页与查询参数 | 筛选表达式 |
| --- | --- | --- |
| 跨度 | `/spans?spanFilterCondition=` | `annotations['note'].identifier == '<id>' or annotations['<annotation-name>'].identifier == '<id>'` |
| 追踪 | `/traces?traceFilterCondition=` | `trace_annotations['note'].identifier == '<id>' or trace_annotations['<annotation-name>'].identifier == '<id>'` |
| 会话 | `/sessions?sessionFilterCondition=` | `session_annotations['note'].identifier == '<id>' or session_annotations['<annotation-name>'].identifier == '<id>'` |

将每个表达式进行 URL 编码，放入对应标签页参数：

    <endpoint>/projects/<project-node-id>/<tab>?<param>=<encoded-expression>

引用单个发现时，除分享筛选表格外，还应直接链接被标注实体。追踪使用 `<endpoint>/projects/<project-node-id>/traces/<otel-trace-id>`；跨度使用该追踪 URL，并添加 `selectedSpanNodeId=<span-node-id>`，使打开时选中目标跨度。从已获取的数据解析跨度 Relay 节点 ID 和所属 OpenTelemetry 追踪 ID；选择参数不接受 OpenTelemetry 跨度 ID。保留已有查询参数，例如 `timeRangeKey=30d`，并对新增值进行 URL 编码。

**丢弃运行**：只有用户明确确认后才执行，因为这具有破坏性。对追踪、跨度和会话，按编码标注标识符筛选并删除项目标注；所有维度共享标识符，因此可一并删除其标签。服务端要求显式的全部删除开关或时间边界，才能授权清除；标识符筛选仅缩小范围，本身不构成授权。随后删除 `$NOTES_SIDECAR` 和 `$AXIAL_SIDECAR`。每个类型的删除都会同时移除笔记和主轴标注，因为它们共享底层标注表。
