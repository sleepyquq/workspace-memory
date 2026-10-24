# Install Workspace Memory manually

[简体中文](manual-installation.md)

Usually, you can ask your agent to install the skill using the [README's installation prompt](../README.en.md#install). Use these steps if your agent can't install it or you prefer to manage the files yourself.

## 1. Get the source

Download or clone this repository and locate `SKILL.md` at its root. Keep these files and directories together, preserving their relative paths:

```text
workspace-memory/
├── SKILL.md
├── LICENSE
├── references/
├── assets/
├── scripts/
├── examples/
└── tests/
```

`examples/` and `tests/` contain examples and validation materials. The source repository's root `AGENTS.md` is for developing this skill. Don't use it as your own project's `AGENTS.md`.

## 2. Copy it into a skills directory

The examples below install it for your user account in Codex, at `~/.agents/skills/workspace-memory/`, following the [official Codex documentation](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills). For another agent that supports skills, use the directory specified in its documentation and keep the same file structure.

Run the appropriate command from the source repository root, where `SKILL.md` lives. The commands stop if the destination already exists. Compare and back up the existing version before deciding whether to replace it.

### Windows: PowerShell 7

```powershell
$destination = Join-Path $HOME '.agents/skills/workspace-memory'
if (Test-Path -LiteralPath $destination) {
    throw 'The destination already exists. Compare the installed version first.'
}
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item -LiteralPath 'SKILL.md', 'LICENSE', 'references', 'assets', 'scripts', 'examples', 'tests' `
    -Destination $destination -Recurse
```

### macOS / Linux: Bash

```bash
(
  set -eu
  destination="$HOME/.agents/skills/workspace-memory"
  if [ -e "$destination" ]; then
    printf '%s\n' 'The destination already exists. Compare the installed version first.' >&2
    exit 1
  fi
  mkdir -p "$destination"
  cp -R SKILL.md LICENSE references assets scripts examples tests "$destination/"
)
```

## 3. Check availability, then enable workspace memory

Check that the installation directory contains `SKILL.md` directly, rather than another nested `workspace-memory/` folder. Then ask your agent:

```text
Confirm that you can find workspace-memory and read its SKILL.md. Don't enable workspace memory yet.
```

In the Codex CLI or IDE extension, you can also check with `/skills`. If the skill doesn't appear, restart and check again. See the [official documentation on skill invocation and discovery](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills).

The agent needs to read the target workspace's root `AGENTS.md`. If it uses a different project instruction entry point, link to `AGENTS.md` from there. The validation and migration audit scripts require Python 3.10+, with no extra Python packages.

Once installed, open the folder you want to work in and follow [Get started](../README.en.md#get-started). Installing the skill doesn't create workspace memory or enable it in other projects.
