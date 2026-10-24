# Knowledge-Graph Schema

Read this reference when enabling memory, creating or restructuring notes, repairing links, or changing the graph schema.

## Routing Architecture

The graph has two navigation notes and any number of knowledge notes:

- `state.md` answers “what is active now?” and links directly to current topics.
- `index.md` answers “which note owns this area?” through a compact routing table.
- `topics/*.md` owns detailed facts for one retrieval intent.
- `decisions/*.md` owns one durable decision, including rationale and consequences.

Ordinary work reads `state.md`, then either follows its active links or consults `index.md`. It must not enumerate `topics/` or `decisions/` merely to discover what exists.

## Index Requirements

Keep `index.md` small. Its `Task Routing` table should use real terms a future request is likely to contain, including product areas, components, protocols, and operational names.

Each route contains only:

- an area/keyword cell;
- links to one or a few canonical notes;
- optionally a one-line distinction when neighboring notes are easy to confuse.

The `Topics` section lists every topic note once with its frontmatter summary. The `Decisions` section may list high-impact active decisions directly; other decisions must remain reachable through linked topics. Do not copy detailed facts into the index.

## State Requirements

Keep `state.md` focused on current work:

- `Current Focus`: the immediate outcome being pursued;
- `Active Topics`: wiki links to the smallest relevant set of topic notes;
- `Live Issues`: unresolved blockers or risks, linking to their owner notes;
- `Next Actions`: concrete next work, again linking instead of duplicating background.

Replace stale state by subject. Do not append dated updates or completed-work history here or move them wholesale into a topic. See [maintenance.md](maintenance.md) for compaction and preservation of unresolved work. `Last updated` is the date of this state edit, not proof that every linked fact was reverified.

## Topic Notes

Use one topic note per retrieval intent. A topic is appropriately scoped when a future task can read it without also loading unrelated subsystems.

Required frontmatter:

```yaml
---
id: device-runtime
type: topic
status: active
summary: Server-mediated device activation, control, heartbeat, and task delivery.
tags: [device, runtime]
updated: 2026-08-20
---
```

- `id` must equal the lowercase kebab-case filename stem and remain stable.
- `type` is `topic`.
- `status` is `active`, `dormant`, or `archived`.
- `summary` is a routing sentence, not a second body summary.
- `updated` records the actual update date; never invent an unknown historical date.

Recommended sections are `Current Model`, `Durable Details`, `Constraints`, `Open Issues`, and `Related`. Adapt them when the topic needs a clearer domain-specific structure.

Split a topic when it contains two independently retrieved domains, when most tasks need only one half, or when its links form distinct clusters. Merge notes only when they cannot be understood or maintained independently.

## Decision Notes

Use a decision note when forgetting the choice or its rationale could cause rework or inconsistency. Required frontmatter mirrors topic notes, with `type: decision` and status:

- `active`: all current decision clauses apply within their recorded scope;
- `partially_superseded`: some clauses were replaced; remaining clauses still apply;
- `superseded`: the whole decision was replaced;
- `archived`: retained history outside current use, not a synonym for replacement.

Record the applicable scope, triggering problem or stage, decision, rationale, consequences, and available evidence. Record reconsideration conditions when known. `updated` is the note edit date, not the decision's original date or a blanket verification date. Use source references or observations with their actual scope; unknown rationale remains unknown.

For new or reconciled replacements, add paired optional frontmatter fields:

```yaml
# Old decision (use superseded for full replacement)
status: partially_superseded
superseded_by: "[[decisions/overwrite-and-undo]]"
```

```yaml
# Replacement decision
status: active
supersedes: "[[decisions/authoring-safety]]"
```

Multiple targets use quoted-link lists, for example:

```yaml
supersedes:
  - "[[decisions/authoring-safety]]"
  - "[[decisions/editor-history]]"
```

These links provide reciprocal graph edges; also explain the exact replaced clauses and still-effective constraints in both notes' prose. `partially_superseded` requires `superseded_by`; an older `superseded` note without typed fields receives a review warning, not a new migration prerequisite. Paired fields, when present, must agree and form no cycle. Fields are omitted when no replacement exists; do not add empty lists to every note.

When a decision is partially replaced, rewrite its summary and current decision clauses to describe the effective remainder. Keep the retired clause under `Supersession`, clearly marked historical. Update the affected topic body, not just a new “read this first” notice. See [maintenance.md](maintenance.md) for the worked example.

## Wiki Links and Explicit Backlinks

Use vault-root paths without the `.md` suffix:

```markdown
[[topics/classroom-runtime|Classroom runtime]]
[[decisions/game-direct-runtime|Game-direct runtime decision]]
```

For every durable link between two topic/decision notes, add a reciprocal link in the target note's `Related` or `Supersession` section. This explicit backlink lets agents traverse either direction without scanning the vault; Obsidian will also compute its own backlinks.

Navigation links originating from `state.md` or `index.md` do not require reciprocal links. Do not link outside the memory root with wiki links.

Prefer explicit vault-root paths. Existing unique short links such as `[[device-runtime]]` and source-relative links such as `[[../decisions/runtime-policy]]` remain supported inside the memory root. An explicit path must resolve exactly; a missing directory never falls back to a same-named note. Aliases and fragments are allowed; the validator checks the target note, not the existence of the heading/block fragment. Wiki links in fenced code, inline code, and HTML comments are examples rather than graph edges.

## Canonical Ownership

Store each detailed fact in one canonical note. Other notes should link to it and explain only the relationship. Repetition is allowed only for a short safety invariant whose omission would make the local note misleading; keep one note clearly authoritative.

Fine-grained durable facts are not “noise.” Keep exact protocol names, status transitions, ownership rules, compatibility boundaries, paths, commands, or version constraints when they pass the importance test. Exclude raw logs and conversational chronology.

## Automatic Update Routing

For ordinary workspace work, keep track of which canonical notes were actually read or created. At handoff, update only that affected set:

- durable implementation/resulting-state changes go to the owning topic;
- a new durable choice goes to a decision note linked from its owning topics; list behavior-governing decisions where a future reviewer can find them before proposing changes;
- changed focus, live blockers, or next actions update `state.md` with links rather than duplicated detail;
- new or changed retrieval vocabulary updates the relevant `index.md` route;
- new topic/decision relationships are written in both notes.

Do not discover update targets by scanning the entire graph. Follow affected decisions' backlinks to consumers that need reconciliation. If the task exposes an unrecorded durable area, consult `index.md`; create a new topic only when no existing note has that retrieval intent.
