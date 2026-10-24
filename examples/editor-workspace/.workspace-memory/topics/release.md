---
id: release
type: topic
status: active
summary: 导出开关的环境状态及下一步授权。
tags: [release]
updated: 2026-10-24
---

# 发布与验收

## Current Model

- 合成案例设定：导出开关修复已在本地候选 `editor-r2` 实现，针对开关的回归检查通过。
- 生产仍为 `editor-r1`，未包含该修复。生产问题保持开放，不用本地测试结果代替生产核验。

## Open Issues

- 发布负责人需要用户确认发布窗口；获准后发布候选并核验开关，失败时恢复 `editor-r1`。此示例不授予实际部署权限。
- 编辑器撤销的浏览器验收由 [[topics/editor]] 维护，不因导出开关测试通过而关闭。

## Related

- [[topics/editor]]
