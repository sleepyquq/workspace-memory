# Memory Graph Migration

Read this reference completely before migrating legacy memory into the routed graph.

## Source Authority

Use the user-designated original memory as the migration source. If the user identifies a pre-migration inline section, that section remains authoritative even when a partial destination graph already exists. Treat previously generated summaries as comparison material, not as permission to drop original facts.

Do not replace, delete, or deactivate the source until semantic coverage and structural validation both pass.

## Supported Legacy Shapes

- Inline `AGENTS.md` memory containing sections such as Background, Current Goals, Progress, Key Decisions, Known Issues, Next Steps, Relevant Files, and dated updates.
- Earlier three-file layouts such as `context.md`, `state.md`, and `decisions.md`.
- An existing topic graph that needs restructuring or link repair.

Migration is an explicit exhaustive mode, so reading the complete source and destination is allowed.

## Semantic Coverage Pass

Process every source entry and classify it in working context as one of:

1. **Current durable fact** — migrate to a canonical topic.
2. **Active decision** — migrate to a decision note and link its owning topics.
3. **Superseded but explanatory** — preserve in a fully or partially superseded decision or a short `Evolution` section, linked to the replacement; retain still-effective clauses as current.
4. **Current focus, issue, or next action** — migrate to its owner topic and link it from `state.md`.
5. **Workspace-specific constraint or preference** — migrate to the relevant topic; use a foundation topic only when no narrower owner exists.
6. **Transient or obsolete** — exclude only when it is a raw log, temporary process observation, fully solved incident with no remaining consequence, rejected idea with no useful rationale, duplicated fact, or obsolete skill mechanic.

For each exclusion, be able to state which rule applies. A permanent line-by-line migration ledger is not required, but do not declare coverage complete while an unreviewed durable anchor or open item remains.

## Exact-Anchor Coverage Pass

Semantic summaries must retain the exact literals that a future agent would otherwise have to rediscover. After the ordinary semantic pass, separately review:

- database tables, fields, indexes, and stable status values;
- API methods and routes;
- protocol names and version identifiers;
- environment/configuration variable names;
- application/package identities;
- repository file and directory paths;
- commands whose exact spelling is part of the durable workflow;
- unresolved blockers, risks, TODOs, and next actions.

Run `scripts/audit_migration.py <source> <memory-root>` to extract high-signal candidates and report literals not present verbatim in the destination graph. Use `-` as the source to read from standard input and `--section "Workspace Memory"` when the source is a full `AGENTS.md` file. The report is a review queue, not a semantic verdict.

Presence checks match case-sensitive literal text with technical-token boundaries. A field `task_id` is retained in `runs.task_id` or ordinary prose, but not in `previous_task_id` or `task_id_backup`. Paths, package names, protocols, and commands also check their connecting punctuation: `backend/store.py.bak` does not preserve the path `backend/store.py`. Normal sentence punctuation remains supported. This check does not establish that a literal is still current or used with its original meaning.

Credential assignments and long options whose names contain `KEY`, `TOKEN`, `PASSWORD`, `PASSWD`, `SECRET`, or `CREDENTIAL` have their values masked in text and JSON output, including spaced assignments and quoted values. Standalone environment-variable anchors retain only the variable name. Commands that reference a shell variable, such as `docker login --password "$REGISTRY_TOKEN"`, remain eligible for exact matching because they contain no credential value.

Commands containing recognized credentials go to `sensitive_candidates` with a source line and masked excerpt instead of the exact-anchor queue: never copy the credential value into memory to satisfy coverage. Review these candidates alongside unresolved items. `--fail-on-missing` still applies only to missing exact anchors; a zero exit code does not clear the review queues. These patterns cover named assignments/options, not arbitrary unlabeled secrets.

Review each reported candidate:

1. Preserve a missing literal in its canonical note when it is current, explanatory, or still needed for compatibility.
2. Exclude it only after confirming that a later source entry supersedes it, it is transient/secret, or its exact spelling is no longer useful.
3. Map every reported unresolved item to `state.md` and its owner topic, or confirm that a later source entry resolves/supersedes it.
4. Re-run the audit after edits. Any remaining missing candidate must be consciously classified before replacing the source.

Keep the audit output transient unless the user asks for a durable migration record. The routed graph remains the authoritative result and ordinary Resume must not load a migration ledger.

Later source entries supersede older status only when they address the same object and environment with adequate evidence or authority. A newer note edit, local implementation, or passing test does not revoke a product decision or prove production deployment. Reconcile conflicting clauses using [maintenance.md](maintenance.md); preserve unresolved contradictions as issues rather than picking the last paragraph. Preserve exact undated decisions as written; never invent dates or causal explanations.

## Topic Decomposition

Group by future retrieval intent rather than legacy headings or dates. Typical domains may include project foundation, frontend UX, authentication, classes/students, content IDE, AI authoring, material lifecycle, device runtime, app release, classroom runtime, reports, deployment, and CI/security. These are examples, not a required taxonomy.

Create the smallest stable set that lets ordinary tasks open only relevant notes. Avoid both extremes:

- one giant “project history” topic;
- hundreds of one-fact notes with no useful routing boundary.

## Build Order

1. Read and preserve the complete source.
2. Inspect any existing destination graph for conflicts or ambiguous files.
3. Draft topic IDs and task routes.
4. Migrate current facts and active decisions into canonical notes.
5. Preserve useful supersession relationships.
6. Add reciprocal topic/decision links.
7. Build `index.md` from the resulting canonical notes.
8. Build `state.md` from only the current focus, live issues, and next actions.
9. Re-read the original source and perform a second coverage pass for unmapped durable details.
10. Run `scripts/audit_migration.py <source> <memory-root>` and classify every missing exact anchor and unresolved-item candidate.
11. Validate without prematurely enabling or replacing the source: create an isolated temporary workspace containing the candidate compact `AGENTS.md` index and a copy of the candidate graph at its indexed paths. Run `scripts/validate_memory.py <temporary-workspace-root>`, repair the candidate, and revalidate. The temporary copy must contain only the candidate memory/index, not a copy of the repository. Remove it after validation. For an already enabled graph whose index remains unchanged, validate the real workspace directly.
12. Re-read the generated graph selectively through the same routes an ordinary agent will use.
13. Only after all checks pass, install the compact AGENTS index while retaining a recoverable copy of the original source. Run the validator on the effective workspace to check final path wiring. Remove obsolete legacy memory files only after that succeeds; restore the source if the final wiring cannot be repaired.

Preserve unrelated `AGENTS.md` content byte-for-byte where practical. Do not initialize Git, commit, run project tests, install dependencies, or modify project files as part of memory migration.

## Validation Limits

The graph validator checks paths, IDs, links, reciprocity, and reachability. The migration auditor finds high-signal exact literals and unresolved-item candidates that need review. Neither tool can decide whether a subtle fact is current or whether a paraphrase is sufficient; semantic completeness still requires the source-to-graph coverage passes.
