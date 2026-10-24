---
id: authoring-safety
type: decision
status: partially_superseded
summary: 服务端权限、参数验证和原子提交仍有效；同题冲突策略已被覆盖与撤销决定替代。
tags: [ai, safety]
updated: 2026-10-24
superseded_by: "[[decisions/overwrite-and-undo]]"
---

# AI 编辑安全边界

## Context and Scope

- 合成案例：模型通过受限服务端工具编辑草稿，不能直接写数据库或发布。

## Decision — Still Effective

- 服务端检查权限与工具参数；草稿及所需快照原子提交。

## Rationale

- 权限和事务边界避免越权与不完整提交。它们不依赖于采用哪种同题覆盖策略。

## Supersession

- 旧条款“同题冲突保留教师版本”已由 [[decisions/overwrite-and-undo]] 替代，不再约束当前覆盖行为。
- 旧条款旨在保护人工修改；当前通过覆盖前实际快照与任务撤销保护实现。其余安全边界保持有效。

## Related

- [[topics/editor]]
