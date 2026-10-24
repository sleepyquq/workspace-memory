# Keep Current Knowledge Coherent

Use this reference when a decision changes, two records disagree, or current-state notes have accumulated progress history.

## Check the Decision Before Changing the Behavior

Read the routed topic and the decisions governing the behavior under review. Match the decision to the actual object, environment, lifecycle stage, and clause. Follow replacement links for that scope; a partially replaced decision still governs its unaffected clauses.

Distinguish product intent from implementation evidence. An explicit user choice establishes intended behavior; source code and tests establish what was implemented and checked. Neither a newer `updated` value nor code that contradicts a decision silently revokes the decision. Memory does not authorize a deployment, data change, or other action outside the current request.

When a conflict appears:

1. Identify the conflicting claim and the source or observation that changes it.
2. If scope explains the difference, state the distinct scopes in their existing owner notes.
3. If the user has authorized a replacement or evidence clearly corrects a factual mistake, update the affected knowledge directly.
4. If intended behavior or authority remains unresolved, retain the alternatives as an open issue, with its owner, affected action, and the confirmation needed. Pause that action, not unrelated work. Do not silently choose the newer paragraph.

## Replace Clauses, Not Whole Documents by Default

A decision can bundle independent constraints. If only one changes, use `partially_superseded` rather than dropping the rest or leaving the entire old decision marked active.

For the replacement, record the new choice, its scope, known evidence/rationale, consequences, and `supersedes`. In the old decision:

- use `partially_superseded` or `superseded` as appropriate and add `superseded_by`;
- rewrite its summary and current clauses to describe what still applies;
- move retired claims to `Supersession`, naming the replacement and the affected scope;
- retain explanatory rationale without presenting the old behavior as current.

Follow the affected topic links and backlinks. Rewrite their current model, constraints, open issues, and routing summaries where necessary. Also check the entry/router if they repeat the old claim. This is a bounded consumer update; do not scan every unrelated note. Re-read this small set as a new agent would, then run structural validation.

### Example: Overwrite Policy Changes, Permission Checks Do Not

An old authoring-safety decision bundled server-side permissions, atomic commits, and “same-item conflicts preserve the teacher version.” A later explicit product decision allows AI overwrite, but requires an actual pre-overwrite snapshot and two separate undo controls.

The correct reconciliation is:

- **Old safety decision:** `partially_superseded`; keep permission, validation, and atomicity constraints current. Mark only the same-item conflict policy historical and link to the new decision.
- **New overwrite/undo decision:** `active`; AI may overwrite; the editor undoes only the current item; the task card undoes the whole task and protects later human changes. Add the reverse `supersedes` link.
- **Owning topics:** replace “preserve the teacher version on conflict” and “editor undo stores the whole document” wherever presented as current behavior. Preserve actual implementation/verification gaps separately.
- **Future review:** test snapshot timing, permission checks, and each undo control's scope. Do not propose banning overwrite or enlarging editor undo merely to match a generic preference.

The runnable [example workspace](../examples/editor-workspace/) demonstrates these relationships with synthetic content. The example contains no production state or private project data.

## Keep State a Working Set, Not a Timeline

For an ordinary update, locate the existing item by subject and replace it. Add a new item only for a new live subject. Remove resolved items from `Live Issues` and `Next Actions`; retain their durable result in the owning topic if it passes the importance test. Once an outcome no longer changes the next action, it leaves `Current Focus` too.

Each state item should answer a current question: what outcome matters now, what is blocked, who owns it, or what happens next? Put detailed baselines, exact commands, implementation facts, and evidence in the owning topic. The entry keeps a short link and any condition needed to avoid a wrong next action.

For accumulated history, use this compaction procedure:

1. Read the complete affected state/topic section and its linked owners. Group statements by subject, not date.
2. Separate implementation, verification, local runtime, and production status. Match revisions/environments before concluding that an older open item is resolved. Keep “not tested,” “not deployed,” and unresolved risks where they still affect action.
3. Resolve contradictions using sources already available or a targeted check within the task's authority. If a consequential status cannot be confirmed, keep it explicitly unverified with the next responsible action. Do not reconnect to production merely to tidy notes.
4. Put current detailed facts and exact literals in their canonical topics. Preserve only useful turning points in a short `Evolution` section or a decision: previous constraint → accepted change → lasting consequence. Do not move the entire diary into another file or create daily archives.
5. Rewrite the entry from the current working set, linking to owners. Keep every unresolved item either directly in the entry when it affects current work or in a router-reachable topic when dormant. Record why an item is parked when that affects resumption.
6. Compare the original content with the result before replacing it: unresolved items, constraints, exact identifiers, useful rationale, validation gaps, and recovery requirements must still have owners. Use `audit_migration.py` for substantial restructuring; classify its candidates rather than blindly copying them.
7. Refresh the edited notes' dates and check the affected links. A date update records this edit, not a new verification of every claim.

The validator warns above **80 lines or 6,000 characters** in the entry note. These are review triggers, not acceptance limits. Keep necessary detail even if a legitimate working set exceeds them. No automatic truncation or age-based deletion is allowed. There is no fixed size limit on durable topic notes; split by retrieval intent, and consolidate dated progress in place.

### Example: Local Fix Is Not a Production Fix

Suppose the entry says “export toggle broken in production,” followed by “fix implemented locally; tests pass; not deployed.” Replace those dated entries with one live item: “Production export toggle awaits deployment; local fix validated — see the release owner.” The topic owns the actual source revision, test scope, current production baseline, and next authorized action. Do not mark the issue solved or keep every intermediate test run.

## Handoff Without Lost Updates

Re-read the current target before writing, especially entry/router files shared by sessions. Merge current edits and keep distinct parallel goals rather than replacing them with only this session's work. If multiple agents are already writing memory, assign one owner for shared navigation and let topic owners supply deltas. This is a writing convention, not a lock service or an instruction to start agents.
