<a id="sqlalchemy-polymorphic-user-example"></a>

# SQLAlchemy 多态用户示例

本示例通过用户身份验证实例展示 SQLAlchemy 单表继承（STI）模式，说明如何在单个数据库表中建模本地和外部等不同用户类型，同时保持类型安全与整洁代码组织。

<a id="key-concepts-demonstrated"></a>

## 展示的核心概念

1. **单表继承（STI）**
   - 所有用户类型共享同一个数据库表
   - 鉴别列（`auth_method`）决定实例化哪个类
   - 高效存储，同时保持面向对象设计

2. **多态标识**
   - 每个子类在 `auth_method` 列具有唯一标识符
   - SQLAlchemy 根据该值自动实例化正确类
   - 支持对特定用户类型进行类型安全查询

3. **抽象基类**
   - 无法直接实例化 `User` 类
   - 定义所有用户类型的公共结构和行为
   - 强制各子类接口一致

4. **安全实现**
   - 使用 bcrypt 和唯一盐值进行密码哈希
   - 密码哈希与盐值分开存储
   - 类型安全的身份验证方法处理
   - 数据库约束确保数据完整性

<a id="initialization-behavior"></a>

## 初始化行为

SQLAlchemy ORM 的对象初始化方式较独特，需要理解：

1. **对象创建与数据库加载**
   - 对象创建时，例如 `LocalUser(email="user@example.com", password="secret")`：
     - 调用 `__init__` 方法
     - 执行密码哈希和盐值生成
     - 通过构造函数设置属性
   - 数据库加载时，例如 `session.query(User).all()`：
     - SQLAlchemy 绕过 `__init__`
     - 直接从数据库行设置属性
     - 更接近反序列化，而非构造

2. **多态加载**
   - `auth_method` 鉴别字段决定实例化哪个类
   - SQLAlchemy 自动选择正确子类
   - 所有属性直接从数据库行设置

3. **状态管理**
   - 非映射状态，例如计算属性，可通过以下方式维护：
     - Python 描述符（`@property`）
     - 事件钩子（`InstanceEvents.load()`）
   - 本示例根据密码字段计算 `auth_method`

此行为确保：
- 密码哈希仅在对象创建时执行
- 数据库加载高效直接
- 多态继承无缝工作

<a id="code-structure"></a>

## 代码结构

- `User`：定义公共用户属性的抽象基类
  - 类型安全的 `auth_method` 鉴别字段
  - 带检查约束的密码字段
  - 数据库级完整性检查

- `LocalUser`：本地密码身份验证用户子类
  - 使用 bcrypt 安全哈希密码
  - 每名用户使用唯一盐值
  - 创建时自动哈希密码

- `ExternalUser`：通过外部服务身份验证的用户子类
  - 不存储密码
  - 密码字段为 NULL
  - 职责清晰分离

<a id="database-constraints"></a>

## 数据库约束

1. **邮箱唯一性**
   - 确保没有重复邮箱地址
   - 适用于所有用户类型

2. **身份验证方法校验**
   - 将 `auth_method` 限制为有效值
   - 在数据库级强制类型安全

3. **密码字段一致性**
   - 确保两个密码字段同时为 NULL 或同时有值
   - 保持外部用户数据完整性

<a id="usage-example"></a>

## 使用示例

```python
# Create a local user (password automatically hashed)
local_user = LocalUser(email="user@example.com", password="secret")

# Create an external user (no password required)
external_user = ExternalUser(email="oauth@example.com")

# Query all users (returns both types)
users = session.query(User).all()

# Query specific type
local_users = session.query(LocalUser).all()
```

<a id="security-features"></a>

## 安全特性

1. **密码存储**
   - 绝不明文存储密码
   - 每名用户使用唯一盐值
   - 使用 bcrypt 安全哈希
   - 盐值与哈希分开存储

2. **类型安全**
   - 身份验证方法采用 Literal 类型
   - 数据库约束确保数据完整性
   - 不同用户类型清晰分离

3. **数据完整性**
   - 数据库级检查约束
   - 一致的 NULL 处理
   - 适当字段校验

<a id="educational-focus"></a>

## 教学重点

本示例旨在说明：
- 如何在 SQLAlchemy 中实现 STI
- 多态继承对数据库设计的收益
- 多种用户类型下如何保持代码组织整洁
- 密码存储安全最佳实践
- 数据库约束设计
- 使用 SQLAlchemy 实现 Python 类型安全

<a id="running-the-example"></a>

## 运行示例

1. 安装依赖：
   ```bash
   pip install sqlalchemy bcrypt
   ```

2. 运行示例：
   ```bash
   python users.py
   ```

<a id="note-on-security"></a>

## 安全说明

本示例为教学目的提供安全密码处理。生产环境还应实现其他安全措施，例如：
- 限流
- 密码复杂度要求
- 账户锁定策略
- 会话管理
- 额外身份验证因素
- `SECRET_KEY` 的安全密钥管理
- 适当数据库配置和访问控制
- 定期安全审计和更新
