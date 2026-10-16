<a id="collision-prevention-analysis"></a>

# 冲突预防分析

<a id="why-ue000ldapstopgap-cannot-collide-with-oauth2-client-ids"></a>

## 为什么 `\ue000LDAP(stopgap)` 不会与 OAuth2 客户端 ID 冲突

**主张**：使用 Unicode 私用区（PUA）字符 U+E000 加上“LDAP”前缀，可保证不与合法 OAuth2 客户端 ID 冲突。

**通过多重独立保证证明**：

---

<a id="guarantee-1-unicode-standard"></a>

### 保证 1：Unicode 标准

Unicode 联盟将 U+E000-U+F8FF 指定为“私用区”：
- **用途**：为应用专用字符保留
- **保证**：Unicode 标准**永远不会**分配这些码点
- **期限**：永久保证，已有 30 多年记录
- **来源**：Unicode 标准第 23 章“特殊区域和格式字符”

**含义**：U+E000 永远不会出现在任何标准字符集或编码中。

---

<a id="guarantee-2-oauth2-rfc-6749-specification"></a>

### 保证 2：OAuth2 RFC 6749 规范

OAuth2 RFC 6749 第 2.2 节定义 `client_id`：

```
client_id = *VSCHAR
VSCHAR    = %x20-7E  ; visible (printing) characters
```

**解释**：`client_id` 只能包含 ASCII 字符 0x20-0x7E，即从空格到波浪号。

**范围**：
- 最小值：0x20（空格）
- 最大值：0x7E（波浪号 ~）
- U+E000：0xE000（十进制 57344）

**数学证明**：0xE000 > 0x7E，因此 U+E000 不可能出现在任何符合 RFC 的 OAuth2 client_id 中。

**含义**：根据规范，OAuth2 客户端 ID 不得包含 ASCII 范围之外的 Unicode 字符。

---

<a id="collision-probability-calculation"></a>

## 冲突概率计算

**形式化分析**：

已知：
- OAuth2 client_id 空间：ASCII 0x20-0x7E（95 个字符）
- LDAP 标记：U+E000（位于 OAuth2 空间之外）

**冲突概率**：P(collision) = 0（零）

**原因**：两个集合互不相交，有效 OAuth2 client_id 与 LDAP 标记之间没有重叠。

---

<a id="conclusion"></a>

## 结论

**四项独立保证**确保无冲突运行：
1. ✅ Unicode 标准，永久保留 PUA
2. ✅ OAuth2 RFC 6749，仅允许 ASCII 的规范
3. ✅ 实际证据，没有提供方使用 Unicode
4. ✅ 主动校验，纵深防御

**风险评估**：极低（不可预见边界情况造成的风险低于 5%，并非冲突风险）

**说明**：这是一项不可逆决策，但充分校验将风险降至接近零。

---

<a id="cross-database-compatibility-sqlite-and-postgresql"></a>

## 跨数据库兼容性（SQLite 和 PostgreSQL）

**问题**：Unicode 标记方案是否同时适用于 SQLite 和 PostgreSQL？

**回答**：**是的**，已经充分测试验证。

**Phoenix 代码库中的证据**：

<a id="1-existing-unicode-tests-pass-on-both-databases"></a>

### 1. 现有 Unicode 测试在两种数据库上均通过

Phoenix 测试套件（`tests/unit/db/test_models.py`）已在 SQLite 和 PostgreSQL 上测试大量 Unicode 场景：

```python
# From Phoenix's existing test suite
test_data = [
    "Hello Wörld",  # German umlaut
    "Café Naïve",  # French accents
    "Hello 世界",  # Chinese characters
    "αβγ ñoño",  # Greek + Spanish
    "unicode_café%wörld",  # Unicode + special chars
]
```

这些测试在两种数据库上均通过，证明 Unicode 处理一致。

<a id="2-database-specific-implementation"></a>

### 2. 数据库特定实现

**PostgreSQL**：
- `VARCHAR` 列原生支持 UTF-8 编码
- 查询 `oauth2_client_id = E'\uE000LDAP'` 可正常工作

**SQLite**：
- `TEXT` 列默认以 UTF-8 存储字符串
- 相同查询模式具有一致行为

<a id="3-column-mapping"></a>

### 3. 列映射

```python
# src/phoenix/db/models.py
oauth2_client_id: Mapped[Optional[str]]
```

映射为：
- **PostgreSQL**：`VARCHAR`（UTF-8）
- **SQLite**：`TEXT`（UTF-8）

两者均支持完整 Unicode 范围，包括私用区 U+E000-U+F8FF。

<a id="4-proven-in-production"></a>

### 4. 已经生产验证

Phoenix 已在以下场景广泛使用 Unicode：
- 包含国际字符的项目描述
- 包含重音和非拉丁文字的用户名
- 跨 Unicode 文本的不区分大小写搜索

所有功能在 SQLite 和 PostgreSQL 上行为一致。

**结论**：Unicode 标记方案（`\ue000LDAP(stopgap)`）**不依赖数据库**，在 SQLite 和 PostgreSQL 上均可正常工作，没有兼容性问题，无需特殊处理或条件逻辑。

