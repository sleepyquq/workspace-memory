# Synthetic Editor Workspace

This is a fictional fixture for memory routing and reconciliation, not an application to deploy.

## Workspace Memory

Status: enabled
Root: `.workspace-memory/`
Entry: `.workspace-memory/state.md`
Router: `.workspace-memory/index.md`

Apply the rules below only after this section passes the workspace-memory enablement gate: exactly one standalone `Status: enabled`, with valid in-workspace `Root`, `Entry`, and `Router` paths. If the status is `disabled`, missing, or invalid, do not read or update memory files; leave the existing notes untouched. Explicit Enable or Migrate requests follow the skill's corresponding mode.

- Read the entry first; use the router when the task is not linked there.
- Before changing or reviewing behavior, read the topic's governing decisions and applicable replacements.
- After meaningful progress, update affected canonical notes and replace stale state; do not append a log.
- Follow task-relevant links only; keep detailed knowledge out of this file.
