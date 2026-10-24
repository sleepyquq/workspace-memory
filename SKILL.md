---
name: workspace-memory
description: >-
  Maintain an opt-in, workspace-local, Obsidian-compatible memory graph with
  progressive topic routing, explicit bidirectional links, detailed durable
  notes, migration, inspection, update, and summarization. Use only when the
  user explicitly asks to enable, update, resume, summarize, inspect, migrate,
  or disable workspace memory, or after the current workspace root AGENTS.md
  passes the exact enabled-status gate.
---

# Workspace Memory

Maintain cross-session memory for the current workspace as a small routed knowledge graph. Keep `AGENTS.md` compact, preserve detailed durable knowledge in topic notes, and load only the notes relevant to the current task.

This is not global memory. Do not sync unrelated workspaces or treat skill installation, memory files, or legacy content as enablement. Do not manage Git, tests, builds, commits, or project workflows unless the user separately asks.

## Strict Enablement Gate

Automatic Resume or Update is allowed only after all conditions pass:

1. Resolve the workspace root supplied by the runtime; never substitute a sibling, ancestor, skill directory, or another open repository.
2. Read `<workspace-root>/AGENTS.md`.
3. Find exactly one section headed exactly `## Workspace Memory`.
4. Before the next level-1 or level-2 heading, find exactly one standalone status line and require it to be exactly `Status: enabled`. Ignore fenced examples and HTML comments when checking the section and its fields.

If the gate fails, do not read or write memory files. An explicit Inspect may report the failure but does not enable memory. An explicit Enable or Migrate authorizes only that mode.

After the gate passes, resolve `Root`, `Entry`, and `Router` only from that section. Each must be a workspace-relative forward-slash path inside the current workspace. If any path is missing, duplicated, malformed, or escapes the workspace, stop ordinary Resume/Update and report the path conflict. An explicit Enable, Migrate, or Repair may inspect a recognized legacy index with only an in-workspace `Root`, but must not follow any unvalidated path.

## Knowledge-Graph Contract

The default layout is:

```text
<workspace-root>/
├── AGENTS.md
└── .workspace-memory/
    ├── state.md
    ├── index.md
    ├── topics/
    │   └── <topic-id>.md
    └── decisions/
        └── <decision-id>.md
```

- `state.md` is the small entry note: current focus, live issues, and next actions, with links to active topics.
- `index.md` is the small routing catalog: task areas/keywords, one-line summaries, and links to canonical notes.
- `topics/*.md` stores detailed durable knowledge grouped by retrieval intent, not by date or conversation.
- `decisions/*.md` stores decisions whose rationale, consequences, or full/partial supersession relationships must survive.

Use Obsidian-compatible wiki links such as `[[topics/device-runtime|Device runtime]]`. Between topic and decision notes, or between related topic notes, maintain explicit reciprocal links so an agent can traverse either direction without scanning the vault. Links from `state.md` or `index.md` are navigation links and do not require reciprocal links.

A fact has one canonical owner note. State and index notes link to that owner and may carry a one-line routing summary, but must not duplicate detailed facts. Detailed durable knowledge is welcome; split a note when it serves independent retrieval intents, not merely because it is long.

Read [references/knowledge-graph.md](references/knowledge-graph.md) when enabling memory, creating or restructuring notes, repairing links, or changing the graph schema.

## Progressive Resume

After the gate and indexed-path checks pass:

1. Always read only the indexed `Entry` note first.
2. If the task is directly linked from the entry note, follow only those relevant links.
3. Otherwise read the indexed `Router`, select the matching route, and open only its canonical notes.
4. Before modifying or reviewing a behavior, read the governing decisions linked by its topic. Check the applicable clauses and any replacement links, including the still-effective clauses of a partially superseded decision. Other related links remain task-selective.
5. Do not list or scan all files by default. Full-graph reading is allowed only for explicit Migrate, Inspect, exhaustive Summarize, link repair, or when the router is broken. The read-only validator may traverse the graph for required structural checks without loading the whole graph into the agent's context.

If a missing fact affects authority or an irreversible change, ask a focused question and continue independent work. Resolve ordinary gaps from the relevant sources.

## Decision Protection and Reconciliation

Memory supplies context, not new execution authority. Compare a proposed change with the relevant decision's scope, rationale, and evidence; do not classify intentional product behavior as a bug merely because a generic design preference differs.

- An explicit user change or supported correction can replace an old decision. Do not treat `updated`, file order, or a newer implementation alone as proof that a product constraint was revoked.
- If evidence settles the conflict within current authority, reconcile it directly. Otherwise preserve both claims as an unresolved issue in the owner topic, identify the affected action and needed decision, and continue unrelated work.
- When a decision changes, update the replacement, the old decision's effective scope, and affected current statements in the owning topics. Update their summaries and routes if they would otherwise teach the old behavior. A warning banner above contradictory current prose is not reconciliation.
- Follow the old decision's backlinks to the affected consumers; this targeted expansion is part of the same update, not permission to scan unrelated memory.

Read [references/maintenance.md](references/maintenance.md) when resolving a decision conflict, replacing all or part of a decision, compacting accumulated state, or reconciling dated topic records. It includes the partial-replacement pattern and a coverage-preserving compaction procedure.

## Automatic Resume and Update

When the enablement gate and indexed paths are valid, ordinary substantial workspace work automatically uses memory even when the user does not repeat the skill name:

- Before work, read the entry and route only to task-relevant notes.
- After meaningful progress, automatically update the affected canonical notes before handing off.

Automatic Update triggers include:

- a meaningful feature, fix, migration, deployment, or investigation changed the durable baseline;
- the current goal, focus, blocker, risk, or next action changed;
- a durable architecture, product, permission, protocol, compatibility, or operational decision was made;
- work is paused or handed off with context a future session needs.

Do not update for casual discussion, a read-only answer that changed no workspace state, transient command output, failed attempts with no lasting consequence, or verification that only reconfirms an already-recorded baseline.

Automatic Update must remain selective: update the routed notes and consumers affected by a changed decision. Change `state.md` only when current focus/live issues/next actions changed; change `index.md` only when a note or its retrieval route/summary changes. Maintain reciprocal links for every new knowledge-note relationship. Run full validation after structural or decision-lifecycle changes; ordinary in-place fact updates need only check the links and current claims they touch.

## Operating Modes

### Enable

1. Resolve the current workspace root and read the root `AGENTS.md` if present.
2. Apply the gate. If a valid enabled graph already exists, repair only missing structural files after inspection.
3. If legacy inline or three-file memory exists, use Migrate instead of initializing over it.
4. Otherwise create the default layout from `assets/`, add the compact AGENTS index, and record only facts supported by the workspace or conversation.
5. Create topic or decision notes only when there is durable content; do not add empty placeholder notes.
6. Validate the graph before reporting completion.

### Update

This mode may be explicitly requested or triggered automatically by the rules above. After meaningful progress, changed goals, durable decisions, blockers, paused work, or handoff:

1. Reapply the gate and read the entry.
2. Route through the index or active links; do not scan unrelated notes.
3. Re-read the affected files before writing; merge intervening edits instead of overwriting another session's work. Update the canonical owner note in place and reconcile affected decisions and consumers.
4. Update `state.md` only when current focus, live issues, or next actions changed. Replace existing items by subject, remove resolved items after preserving useful outcomes in their owners, and refresh `Last updated`. Do not prepend dated progress entries to state or topics.
5. Add or repair reciprocal links and the index route when a topic/decision is created, renamed, split, or related.
6. Preserve useful detail, unresolved work, exact literals, and rationale. Keep implementation, validation, local runtime, and production status distinct. Preserve consequential evolution in a short topic `Evolution` section or decision, not a displaced diary. State-size warnings trigger review, never truncation.
7. Validate after structural or decision-lifecycle changes. For simultaneous writers, coordinate ownership of shared entry/router files; the skill adds no locks or background service.

### Migrate

Read [references/migration.md](references/migration.md) completely before migrating. Migration is exhaustive by design and may scan the full source memory and destination graph. The original memory source remains authoritative until coverage and graph validation pass.

### Summarize

- For an ordinary summary, read entry + router and summarize their current one-line routes; follow only topics needed for the requested depth.
- For a topic summary, read that topic and only necessary linked decisions/notes.
- Traverse the full graph only when the user explicitly requests an exhaustive summary.
- Do not modify memory unless the user also asks for an update.

### Inspect

Inspection is read-only unless repair or migration is also requested. Report:

- enablement-gate and indexed-path validity;
- missing, malformed, broken, ambiguous, non-reciprocal, or orphaned notes, and inconsistent typed decision replacements;
- stale routes, duplicated canonical facts, legacy layouts, and notes that should be split;
- whether ordinary resume can route without a full scan.

Use `scripts/validate_memory.py <workspace-root>` for structural validation. It stops before reading memory when the gate or indexed paths fail. Errors return exit code 1; review warnings return 0 if structure is valid. Warnings include oversized state and possibly stale state dates. The script cannot infer contradictory prose or whether a decision was authorized; check those through the task-relevant sources. See [references/validation.md](references/validation.md) for supported metadata, links, and diagnostics.

### Disable

Change only `Status: enabled` to `Status: disabled`. Preserve the graph by default. Remove the index or delete memory files only when the user explicitly asks.

## AGENTS.md Index

Use this compact section:

```markdown
## Workspace Memory

Status: enabled
Root: `.workspace-memory/`
Entry: `.workspace-memory/state.md`
Router: `.workspace-memory/index.md`

Apply the rules below only after this section passes the workspace-memory enablement gate: exactly one standalone `Status: enabled`, with valid in-workspace `Root`, `Entry`, and `Router` paths. If the status is `disabled`, missing, or invalid, do not read or update memory files; leave the existing notes untouched. Explicit Enable or Migrate requests follow the skill's corresponding mode.

When enabled, before substantial work and after meaningful progress:

- Read the entry note first.
- Use the router only when the entry does not directly identify the relevant topic.
- Follow only task-relevant wiki links; do not scan the whole memory graph by default.
- Before changing or reviewing behavior, read its topic's governing decisions and applicable replacements.
- After meaningful progress, update affected canonical notes and replace stale state instead of appending a log.
- Keep detailed memory in canonical topic/decision notes, not in `AGENTS.md`.
```

Use workspace-relative paths with forward slashes. Preserve an already indexed non-default in-workspace root unless the user explicitly asks to move it.

## Importance and Detail

Record a fact when it is currently true and at least one condition applies:

1. A future session needs it to continue without rediscovery.
2. It changes the goal, constraints, architecture, decision, file map, current state, or next action.
3. Forgetting it could cause rework, an incorrect implementation, a missed blocker, or loss of rationale.

Preserve fine-grained details when they pass this test. Exclude casual conversation, raw chat transcripts, full command logs, full diffs, secrets, transient process output, rejected ideas with no lasting rationale, and solved incidents with no remaining consequence.

When an important fact is identified by a stable literal—such as a database table or field, API route, protocol/version identifier, configuration variable, package name, file path, command, or status value—preserve that exact literal in its canonical note. A readable explanation may accompany it, but must not silently replace the identifier with only a generalized paraphrase.

Superseded decisions may remain when their rationale explains the current architecture. Use `superseded` for full replacement and `partially_superseded` when clauses still apply; distinguish retired and effective clauses and link replacements in both directions. New replacement relationships use the optional typed fields described in the schema. Existing prose-only relationships remain readable and can be upgraded when touched. Do not invent dates, rationale, consequences, or relationships.

## Safety Rules

- Only modify the current workspace root `AGENTS.md` and files beneath its validated memory `Root`. Explicit migration may also create an isolated temporary validation copy as described in the migration reference; remove that copy after validation.
- Never write credentials, private tokens, passwords, or irrelevant personal data.
- Inspect an existing memory root before creating or moving files; never overwrite ambiguous content.
- Do not follow any indexed or wiki-linked path outside the workspace memory root.
- Preserve unrelated `AGENTS.md` content byte-for-byte where practical.
- Do not create chat logs, daily journals, or duplicate summaries. The graph stores authoritative knowledge, not conversation history.
