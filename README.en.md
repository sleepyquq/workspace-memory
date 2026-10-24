![Workspace Memory](docs/images/readme-cover.svg)

[简体中文](README.md) · **English**

Start a new chat and keep working, without a manual handoff.

Workspace Memory is a Markdown-based skill that keeps context in your workspace. Once enabled, the agent records important background, decisions, and progress as it works. A new chat in the same workspace reads the notes relevant to its task. You can ask for the next piece of work without going back to the old chat, generating a summary, and pasting it into the new one.

Use it for coding, server maintenance, research, writing, or ongoing learning. Memory lives in ordinary Markdown files with Obsidian-compatible wiki links. You don't need Obsidian, an MCP service, or a vector database.

[Use cases](#use-cases) · [Install](#install) · [Get started](#get-started) · [Usage examples](#usage-examples) · [Validation](#validation-and-examples)

## The problem it solves

When you work with an AI over time, the files are usually still there. The context behind them often stays in an old chat:

- A new session doesn't know what's finished, what still needs checking, or what hasn't been delivered.
- The agent suggests changing an approach without knowing why you chose it.
- Handoff summaries accumulate, leaving old and new conclusions side by side.
- Switching agents means explaining the same background, operating constraints, and unfinished work again.

Workspace Memory keeps that context in workspace files and gives the agent rules for reading it, updating it, and reconciling old decisions. The context stays with the work when you change chats.

## Use cases

A workspace can be an ordinary folder. It doesn't need code or Git. Memory is useful when work spans several sessions and the next session needs facts, decisions, or progress from the last one.

- Software development: keep architecture and API constraints, product decisions, test results, and work awaiting deployment or acceptance.
- Server maintenance: maintain a folder for a server's services, configuration locations, backup and recovery procedures, troubleshooting knowledge, and open tasks.
- Research: retain sources, research questions, experimental conditions, evidence, and untested hypotheses so preliminary findings don't become settled facts.
- Writing: carry forward the intended audience, style choices, source material, editorial decisions, and review status.
- Ongoing learning: record concepts you've learned, recurring mistakes, and exercise progress so the next session starts at the right level.

Organize topics around the task; you don't need a software project structure. One-off questions rarely need this skill, and a few stable instructions in `AGENTS.md` may be enough for simple work. The skill doesn't provide cross-project semantic search, cloud sync, or automatic chat transcript collection.

## Why you don't need a manual handoff

### Update during work, read what the next task needs

After meaningful progress, the agent updates the relevant notes instead of waiting for an end-of-chat summary. A new session reads the current state, then follows the topics it needs. A change to authentication logic doesn't require loading deployment records and device protocols too. Exact API paths, field names, versions, and compatibility conditions stay in their own topics.

### Keep the reasons behind decisions

Before changing or reviewing behavior, the agent reads the decisions that govern it. When a decision changes, it updates the old conclusion and the topics that rely on it. If only part of a decision has changed, the remaining requirements stay in effect.

### Keep current state short without losing open work

Completed items leave the current task list; useful results stay in their topics. Items awaiting verification, delivery, or an external dependency remain, with a next step. The next session doesn't have to reconstruct the current situation from a long progress log.

### Inspect the files and take them with you

Memory is ordinary Markdown. You can search it, edit it, review diffs, or put it under version control. To switch to another agent that supports the skill, keep the workspace files and install the skill there. There is no database to migrate.

## Install

The recommended approach is to ask your agent to install it. If you've downloaded the source, you can replace the repository URL with its absolute local path:

```text
Install workspace-memory from https://github.com/sleepyquq/workspace-memory so I can use it across my workspaces.
Keep the repository's LICENSE file in the installed copy.
Confirm that the skill can be loaded after installation. If a version with the same name already exists, ask me before replacing it.
Only install the skill for now; don't enable memory in any workspace yet.
```

The agent handles the installation location and file operations. If it asks you to refresh or restart, do that and confirm the skill is available before enabling memory in a workspace.

Your agent needs to support skills, read the workspace root's `AGENTS.md`, and read and write workspace files. If you prefer to manage the files yourself, use the [manual installation guide](docs/manual-installation.en.md).

## Get started

### 1. Enable memory in a workspace

Open the folder you want to work in and ask:

```text
Use workspace-memory to enable memory for this workspace.
If project memory already exists, inspect and migrate it, preserving the useful content.
```

The agent checks existing files, creates or migrates memory, and registers the entry in the workspace root's `AGENTS.md`. The default folder is `.workspace-memory/`, with `Status: enabled` in the entry. An existing valid custom memory path is preserved.

Installing the skill doesn't enable it in every project. The presence of a `.workspace-memory/` folder alone doesn't enable it either.

### 2. Give the agent work as usual

```text
Continue the research report and fill the gaps in the evidence. Don't publish it yet.
```

In an enabled workspace, the skill tells the agent to read relevant memory before substantial work and update affected notes after meaningful progress. You don't need to mention the skill each time or ask for handoff material before ending the chat.

### 3. Start a new chat with the next task

Open the same workspace in a new chat and ask:

```text
Add a risk analysis section to the report, keeping the agreed research scope.
```

The agent finds the recorded scope, decisions, and current progress before starting. You don't need to paste the previous summary or send a separate request to restore memory. Notes distinguish verified facts, tentative interpretations, and unfinished reviews so a draft isn't treated as a final result.

## Usage examples

In a workspace with memory enabled, a new chat can start like this.

### Software development: keep existing constraints while adding a feature

An export feature has passed local tests but hasn't been deployed. It still needs to support the old file format. Ask:

```text
Add retries to the export feature. Run local tests, but don't deploy it.
```

The agent finds the compatibility requirements and existing test results in the relevant topics. After the work, it records progress on retries while keeping the pending deployment visible.

### Server maintenance: build up knowledge in one folder

Create a folder such as `server-ops/` and open it in your agent. Provide the server's alias, purpose, OS version, and any maintenance notes you already have. Then ask:

```text
This folder is for maintaining my server. Enable workspace-memory here.
Use the basic information and maintenance notes I provide to record services, configuration locations, operating constraints, and open tasks.
Mark unconfirmed information as needing verification. Only organize memory for now; don't connect to or modify the server.
```

Information confirmed during troubleshooting, configuration changes, and recovery drills accumulates in that folder. In a later chat, ask:

```text
Continue investigating the backup alert.
```

The agent reads the existing findings and open tasks without asking you to explain the server again.

Service state, configuration, and backup results can change, so recheck relevant live information before taking action. Keep passwords, private keys, and access tokens in your credential manager, not in memory.

### Research: carry experimental conditions into the next question

The workspace already contains sources, sample selection criteria, and an initial analysis. One group of outliers remains unexplained.

```text
Analyze the outliers we found last time separately and check whether they change the conclusion.
```

The agent can reuse the recorded experimental conditions, trace the original sources, and keep new observations separate from explanations that still need testing.

### Writing: continue a series without repeating the style brief

The audience, tone, and terminology for an article series are settled. The first two articles have been reviewed.

```text
Continue with the third article. Give me the outline and opening first.
```

The agent writes for the agreed audience and follows the recorded style, with the source material already at hand.

### Ongoing learning: work on the gaps from last time

Your learning folder records concepts you've mastered, mistakes in exercises, and unfinished topics.

```text
Let's continue practicing conditional probability. Give me three questions without the answers yet.
```

The agent can choose questions based on those notes and update them as your understanding changes, rather than starting over at chapter one.

## Everyday maintenance requests

| What you need | What to ask |
| --- | --- |
| Read-only inspection | Check this workspace's memory structure, links, and conflicting claims. Don't change anything yet. |
| Shorter current state | Consolidate old progress records while preserving unfinished work and the reasons behind decisions. |
| Migration | Migrate the project memory in AGENTS.md to workspace-memory. Preserve useful detail and exact identifiers. |
| A topic summary | Summarize the current authentication design and why its decisions were made. |
| Disable memory | Disable workspace-memory for this workspace, keeping the existing notes. |

Disabling changes the entry to `Status: disabled`; it doesn't delete the notes. Inspection and summaries are read-only by default. Repairs, restructuring, and migration need authorization to make those changes.

## How the files fit together

```text
your-project/
├── AGENTS.md
└── .workspace-memory/
    ├── state.md        Current focus, open issues, and next steps
    ├── index.md        Topic routes and lookup keywords
    ├── topics/         Facts, sources, methods, and constraints
    └── decisions/      Decisions, rationale, scope, and replacements
```

The entry contains current state and pointers; details stay in their own topics. Ordinary tasks read what they need. Migration, full inspections, and structural validation can traverse the graph. Obsidian can display the wiki links, but the agent reads Markdown directly.

For example, an editor may use its top undo button for the current item and a task card to undo a whole AI task. Before reviewing that behavior, the agent reads the decision and checks the implementation against it. If the user changes the decision, memory marks the replaced clauses so the old and new rules don't remain active together.

Commits, publishing, remote operations, and data changes still require the user's authorization. Memory doesn't grant it. The skill adds no separate cloud storage service; content the agent reads remains subject to the data handling rules of its runtime and model provider.

## Validation and examples

Read the [synthetic example workspace](examples/editor-workspace/AGENTS.md) before enabling memory in your own project. It shows a partially replaced decision alongside a local fix that still awaits production deployment.

The validation scripts require Python 3.10+ and use only the standard library. Run these commands from the skill repository root:

```sh
python -m unittest discover -s tests -v
python scripts/validate_memory.py examples/editor-workspace
```

To check your own project, replace the last path with its workspace root. The validator is read-only. It checks the entry, paths, metadata, links, reachability, and decision replacement relationships. Exit code `1` means a structural error; `0` means structural checks passed, though review warnings may remain. The agent still needs to judge whether a decision applies.

The [fresh-session continuation test](tests/continuation.md), documented in Chinese, includes reproduction inputs, acceptance criteria, and results. One session modified a synthetic editor and updated its memory. A second session, without the first session's chat history, recovered the product decisions and unfinished work from project files. Checks covered accidental reversal of agreed behavior and preservation of pending deployment, acceptance, and external dependencies after state cleanup. The test used two independent contexts in the same execution environment; other runtimes and automatic skill discovery were not tested.

## Further reading

- [SKILL.md](SKILL.md): the instructions the agent follows.
- [Maintenance rules](references/maintenance.md): decision conflicts, partial replacements, and state cleanup.
- [Graph structure](references/knowledge-graph.md): note fields, routing, and reciprocal links.
- [Migration procedure](references/migration.md): coverage checks and exact-identifier auditing.
- [Validation reference](references/validation.md): supported formats, diagnostics, and validation limits.
- [MIT license](LICENSE): terms for use, modification, and redistribution.
