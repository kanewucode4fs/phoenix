# Agent Instructions

## 项目阶段

`iteration`

## 测试 Agent

用户的测试 Agent 项目位于 `/Users/kanewu/Documents/TechSet/FirstAgent`，后续 Phoenix 接入与评测测试参考该项目。

## Vault 工作流入口

本项目「可信评测平台」的 Vault 公共规则与工作流分工见 `/Users/kanewu/Documents/Obsidian/dev-vault/VAULT.md`。
Codex 开发工作流通过对应的 `dev-*` 独立技能执行；执行约定见 `/Users/kanewu/Documents/Obsidian/dev-vault/.codex/workflows/execution.md`，业务步骤见 `/Users/kanewu/Documents/Obsidian/dev-vault/.codex/skills/dev-*/SKILL.md`。

## Build & Development

This repo uses a **Makefile** for all build, test, lint, and dev commands. Run `make help` to see all available targets.

- Python packages are managed with `uv`
- TypeScript packages are managed with `pnpm`

## Python Dependency Version Policy

**Never add pre-release versions to production dependencies in `pyproject.toml` files.** Pre-release suffixes (`aN`, `bN`, `rcN`, `.devN` per [PEP 440](https://peps.python.org/pep-0440/)) are implicitly excluded from pip's dependency resolution by default — they are only installed if explicitly requested via `--pre` or a pinned pre-release specifier. Adding a pre-release pin to a production dependency forces users to opt into unstable software or causes resolution failures. Dev/test dependency groups may use pre-release versions when necessary.
