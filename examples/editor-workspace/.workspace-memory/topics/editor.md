---
id: editor
type: topic
status: active
summary: AI 编辑的当前行为、约束与验收缺口。
tags: [editor, ai, undo]
updated: 2026-10-24
---

# 编辑与撤销

## Current Model

- AI 覆盖与撤销以 [[decisions/overwrite-and-undo]] 为准；不要恢复整包编辑器撤销，也不要把允许覆盖本身当成缺陷。
- 权限、参数验证和原子提交仍遵守 [[decisions/authoring-safety]] 的有效条款。

## Governing Decisions

- [[decisions/overwrite-and-undo]]
- [[decisions/authoring-safety]]（部分替代，安全条款仍有效）

## Open Issues

- 任务卡片的浏览器验收尚未完成。编辑器负责人下一步核对本地人工修改能否及时禁用卡片撤销；不能由规则确认推断实现已通过。

## Related

- [[topics/release]] — 发布状态单独维护。
