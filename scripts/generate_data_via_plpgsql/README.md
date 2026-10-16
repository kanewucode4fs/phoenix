<a id="data-generation-scripts"></a>

# 数据生成脚本

此目录包含在 PostgreSQL 中生成合成追踪数据的脚本。

<a id="getting-started"></a>

## 开始使用

生成跨度：
```bash
python generate_spans.py --num-batches 10 --traces-per-batch 100
```

为跨度添加标注：
```bash
python generate_span_annotations.py
```

检查 `spans`、`traces` 和 `projects` 的表大小：
```bash
python report_spans_table_sizes.py
```

<a id="sample-queries-to-run-after-data-is-generated"></a>

## 数据生成后的示例查询

<a id="select-random-conversation-id"></a>

### 随机选择会话 ID
```sql
SELECT (attributes->'metadata'->>'conversation_id')::uuid as conversation_id
FROM spans TABLESAMPLE SYSTEM (1)
WHERE attributes->'metadata'->>'conversation_id' IS NOT NULL
LIMIT 1;
```

<a id="select-spans-by-conversation-id"></a>

### 按会话 ID 选择跨度
```sql
SELECT *
FROM spans
WHERE attributes->'metadata'->>'conversation_id' = '123e4567-e89b-12d3-a456-426614174000'
ORDER BY start_time;
```

<a id="show-spans-table-size-stats"></a>

### 查看跨度表大小统计
```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('spans')) as total_size,
    pg_size_pretty(pg_relation_size('spans')) as table_size,
    pg_size_pretty(pg_total_relation_size('spans') - pg_relation_size('spans')) as index_size,
    (SELECT count(*) FROM spans) as row_count,
    (SELECT last_value FROM spans_id_seq) as current_sequence;
```

<a id="files"></a>

## 文件说明

- `generate_spans.sql`：生成具有真实感时间信息和元数据的跨度
- `generate_spans.py`：批量运行 generate_spans.sql 的 Python 包装脚本
- `generate_span_annotations.sql`：为现有跨度添加标注
- `generate_span_annotations.py`：跨度标注的 Python 包装脚本
- `report_spans_table_sizes.sql`：报告表大小和行数
- `report_spans_table_sizes.py`：表大小报告的 Python 包装脚本
