---
id: overwrite-and-undo
type: decision
status: active
summary: 允许 AI 覆盖；编辑器按题撤销，任务卡片整次撤销并保护后续人工差异。
tags: [ai, undo]
updated: 2026-10-24
supersedes: "[[decisions/authoring-safety]]"
---

# 覆盖与两种撤销

## Context and Scope

- 合成案例中，用户明确选择直接覆盖题稿，并通过不同入口分担撤销责任。适用于 AI 写题及两种撤销入口；不改变发布权限。

## Decision

- AI 可以覆盖当前题稿；提交事务保留本任务首次覆盖前的实际版本，而不只保留开始生成时的旧版本。
- 编辑器撤销只影响当前题目；任务卡片负责整次 AI 任务，包括任务产生的结构变更。
- 任务涉及题目出现后续人工差异时禁用卡片撤销，服务端事务再次核验；无关题目的修改不阻止该任务撤销。

## Rationale and Consequences

- 允许直接完成编辑，又让教师按题或按任务恢复；需分别检查快照时机和后续人工修改保护。
- 这些是目标语义；实现验收状态由 [[topics/editor]] 维护。

## Supersession

- 仅替代 [[decisions/authoring-safety]] 的“同题冲突保留教师版本”条款；服务端权限、参数验证和原子提交仍有效。

## Related

- [[topics/editor]]
