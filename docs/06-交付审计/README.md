# 06 · 交付审计 — Delivery Check 报告归档

本目录归档 `dev-delivery-check` 产出的 final report，按时间累积，**永不删除**。Claude Code 调用 `/dev-delivery-check`；Codex 调用 `$dev-delivery-check`。

## 文件命名规则

```
delivery-check-<YYYY-MM-DD>[-suffix].md
```

`suffix` 用于同一天多次跑区分（如 `-full` / `-init` / `-incremental`）。例：

- `delivery-check-2026-06-13.md` — 首次基线跑
- `delivery-check-2026-06-14.md` — 第二天增量验证
- `delivery-check-2026-06-14-full.md` — 同日全量 audit
- `delivery-check-2026-06-14-init.md` — 同日 init-to-HEAD 跑

## 每份 final report 含

以当前宿主对应 `dev-delivery-check.md` 的报告步骤为准，不硬编码可能变化的步骤号：

- **Verdict**（DELIVER / FIX-BEFORE-DELIVER / BLOCK）
- delta 起点 + 涵盖 spec/plan/code commits
- 4-artifact 主链 6 check 完整结果（含 ID mapping：REQ-N / PLAN-§N / TASK-N / CODE-X）
- 5 ref 文档影响清单（P0 必修 / P1 建议 / P2 nitpick + apply 状态）
- Hop health summary 表
- Recommended actions（按 P 级别）

## 配套 git tag

仅满足命令文档中的通过、复验及标签条件后，才创建 annotated tag `delivery-check-<YYYYMMDD>-<HHMMSS>`；失败或阻塞不能打通过标签。下次检查按命令文档选取有效起点，推送标签需单独获得授权。

## 与 docs/ 其他视图关系

| 视图 | 关系 |
|---|---|
| 01-05 | **被审计对象**（每次 dc 跑检查 ref doc 是否跟 spec/plan/code 一致） |
| superpowers/specs + plans | **审计输入**（dc 主链对账起点） |
| **06 (本目录)** | **审计输出**（每次 dc verdict 的存档） |
