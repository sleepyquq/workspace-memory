# Structural Validation

Run from the skill repository, passing the **target workspace** rather than its memory folder:

```sh
python scripts/validate_memory.py /path/to/workspace
```

The script uses only Python 3.10+ standard libraries and never writes to the workspace.

## Errors Stop Acceptance; Warnings Request Review

- Exit **1**: invalid enablement/index, unsafe or unresolved paths, invalid required metadata, broken/ambiguous links, missing reciprocal knowledge links, unreachable knowledge notes, or invalid typed decision replacements. Read/encoding errors also return 1 with a diagnostic.
- Exit **0**: structural checks passed. `WARNING` messages may still request state compaction, a date review, or gradual upgrade of a legacy superseded decision.

If the gate or any indexed path is invalid, the script stops before reading memory contents or enumerating the graph. An explicitly disabled workspace is reported as unavailable for validation, not implicitly enabled. To inspect a legacy source before enabling it, use the explicit migration procedure instead.

## Supported Formats

- UTF-8, optionally with BOM; LF or CRLF line endings. CLI diagnostics and migration-audit pipe input/output use UTF-8, including on Windows.
- One real `## Workspace Memory` section, exact `Status: enabled`, one backtick-wrapped `Root`, `Entry`, and `Router`. Fenced examples and HTML comments do not enable memory; an unclosed comment hides the rest of the file. Comment markers inside code examples remain literal. Paths use forward slashes; entry/router are distinct existing Markdown files inside the memory root. A non-default root is supported.
- Flat frontmatter with `id`, `type`, `status`, `summary`, and `updated`. Values may be plain or correctly paired quoted scalars; summaries also support folded plain text and indented YAML block scalars. Required fields reject lists, mappings, null values, and malformed quotes. IDs are lowercase kebab-case filename stems. Dates must be real ISO calendar dates. This is a reader for the skill's metadata subset, not a general YAML linter; use the templates rather than YAML aliases or custom tags. Optional fields such as `tags` can still contain lists.
- Topic statuses: `active`, `dormant`, `archived`. Decision statuses additionally distinguish `partially_superseded` and `superseded`, and do not accept `dormant`.
- Optional `supersedes` / `superseded_by`: a quoted wiki link, an inline list of quoted links, or an indented list of quoted links. Targets must be other decision notes, pairs must agree, and replacement chains must be acyclic. Full replacement fields are optional for older prose-only decisions; partial status is new and requires `superseded_by`.
- Explicit root-relative wiki paths resolve exactly. Unique short names and safe source-relative paths remain supported. `.md`, aliases, and fragments are accepted. Fragment existence is not checked. Links in code examples/comments do not count as graph edges.
- Reciprocal links and reachability are checked from the indexed entry and router. `Related` is a recommended section, not a required English heading. Note-file symlinks must resolve inside the memory root. Linked directories within the graph are rejected to avoid recursive aliases; use ordinary directories.

The script cannot establish semantic correctness, authority, completeness of a partial replacement, fresh runtime status, or whether an archived note is incorrectly presented as current prose. Apply the [maintenance procedure](maintenance.md) to those questions. It also does not prove that a runtime automatically loads or updates the skill.

## Regression Tests

```sh
python -m unittest discover -s tests -v
python scripts/validate_memory.py examples/editor-workspace
```

Tests build isolated temporary workspaces; they do not read or modify external projects or installed skills. The example workspace is synthetic and exercises current routing, partial replacement, reciprocal links, and a still-open production handoff.

For fresh-context behavioral validation, see [the continuation scenario and results](../tests/continuation.md). Its fixture generator creates a separate temporary project; generated application and memory outputs stay outside the skill repository.

The real symlink test skips when the host cannot create symlinks. Separate tests still verify that resolved external files are not read and external directories are not enumerated. Before claiming real symlink coverage on such a host, rerun that case where symlink creation is permitted.
