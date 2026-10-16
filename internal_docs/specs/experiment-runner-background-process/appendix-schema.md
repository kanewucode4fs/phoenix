<a id="appendix-schema-design-decisions"></a>
# 附录：数据库结构设计决策

本文说明 `experiment_execution_configs` 表的设计理由。当前结构见 `src/phoenix/db/models.py` 和 `src/phoenix/db/types/experiment_config.py`。

---

<a id="running-state-detection"></a>
## 运行状态检测

`status` 列是权威生命周期状态：

| `status` | 含义 | 设置方式 |
|----------|---------|-------------|
| `RUNNING` | 正在处理 | `start_experiment`、恢复变更操作、孤立实验恢复 |
| `COMPLETED` | 全部工作已完成 | `_set_experiment_stopped`（无错误） |
| `STOPPED` | 用户主动停止 | 停止变更操作 |
| `ERROR` | 熔断器触发 | `_set_experiment_stopped`（有错误） |

`claimed_at` / `claimed_by` 列跟踪副本所有权（心跳存活状态）：

| `claimed_at` 值 | 含义 | 说明 |
|--------------------|---------|-------|
| `NULL` | 没有副本拥有它 | 可以恢复 |
| 最近时间（心跳有效期内） | 归 `claimed_by` 所有 | 正在处理 |
| 过期时间（超过 10 分钟） | 已孤立 | 副本已崩溃，将自动恢复 |

---

<a id="design-decisions"></a>
## 设计决策

<a id="why-pydantic-models-for-json-columns"></a>
### 为什么 JSON 列使用 Pydantic 模型？

1. **类型安全**：运行时验证模型。
2. **序列化**：通过 SQLAlchemy TypeDecorator 自动转换 JSON。
3. **文档**：代码中的结构本身即可说明设计。
4. **不可变性**：`frozen=True` 防止意外修改。

<a id="why-no-version-field-in-json"></a>
### 为什么 JSON 中没有版本字段？

原设计包含用于结构演进的 `version` 字段，省略原因如下：

1. **Pydantic 处理演进**：带默认值的可选字段支持向后兼容。
2. **数据库迁移**：必要时可通过 Alembic 处理结构变更。
3. **简单性**：减少一个需要维护的字段。

<a id="why-custom_provider_id-reference-instead-of-credential-snapshot"></a>
### 为什么引用 `custom_provider_id`，而不保存凭证快照？

自定义提供商凭证加密存储在 `generative_model_custom_providers` 中。这里只保存 ID 引用：

- 不会将凭证复制到实验配置中（安全考虑）。
- 提供商被删除时，实验恢复将失败（可接受的取舍）。
- 运行时从提供商表获取凭证。

<a id="why-separate-task_config-and-evaluator_configs"></a>
### 为什么分离 `task_config` 和 `evaluator_configs`？

1. **生命周期不同**：任务配置固定，评估器可以稍后添加。
2. **复杂度不同**：评估器有自己的提供商和模型配置。
3. **查询模式**：可能需要单独查询评估器。

---

<a id="table-relationships"></a>
## 表关系

```
experiments
    ├── id (PK)
    ├── dataset_id (FK)
    ├── dataset_version_id (FK)
    └── repetitions

experiment_execution_configs
    └── id (PK, FK → experiments.id)
        ├── task_config (JSONB)
        ├── status (RUNNING/COMPLETED/STOPPED/ERROR)
        ├── claimed_at, claimed_by (ownership)
        ├── cooldown_until (earliest next toggle allowed)
        └── last_error

experiment_runs
    ├── experiment_id (FK → experiments.id)
    ├── dataset_example_id
    ├── repetition_number
    └── output, error, etc.
```

**要点：**
- `experiment_execution_configs` 与 `experiments` 为一对一关系。
- `status` 是权威生命周期状态，与 `claimed_at` 的变化原子设置。
- `claimed_at` / `claimed_by` 跟踪副本所有权，用于心跳和孤立检测。
- `cooldown_until` 保存未来的绝对时间戳；在 `cooldown_until <= now` 之前阻止下一次停止或恢复。
- 进度根据 `experiment_runs` 计算，不存储在配置中。
