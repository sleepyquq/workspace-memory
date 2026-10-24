# 手动安装 Workspace Memory

[English](manual-installation.en.md)

通常只需按 [README 的提示词](../README.md#安装)让 Agent 完成安装。下面的步骤适合无法让 Agent 安装，或希望自己管理安装文件的情况。

## 1. 准备源码

下载或克隆本仓库，找到根目录的 `SKILL.md`。安装时保留以下文件和目录及其相对路径：

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

`examples/` 和 `tests/` 提供示例与验证材料。源码仓库根目录的 `AGENTS.md` 用于维护这个 skill，不要把它作为使用者项目的 `AGENTS.md`。

## 2. 放入 skill 目录

以下以 Codex 的用户级安装为例，目标为 `~/.agents/skills/workspace-memory/`，依据 [Codex 官方文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。使用其他支持 skills 的 Agent 时，按其文档选择安装目录，保持上述文件结构。

在包含 `SKILL.md` 的源码仓库根目录执行对应命令。已有同名目标目录时，命令会停止；先比较并备份现有版本，再决定是否替换。

### Windows：PowerShell 7

```powershell
$destination = Join-Path $HOME '.agents/skills/workspace-memory'
if (Test-Path -LiteralPath $destination) {
    throw '目标目录已存在，请先比较现有版本。'
}
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item -LiteralPath 'SKILL.md', 'LICENSE', 'references', 'assets', 'scripts', 'examples', 'tests' `
    -Destination $destination -Recurse
```

### macOS / Linux：Bash

```bash
(
  set -eu
  destination="$HOME/.agents/skills/workspace-memory"
  if [ -e "$destination" ]; then
    printf '%s\n' '目标目录已存在，请先比较现有版本。' >&2
    exit 1
  fi
  mkdir -p "$destination"
  cp -R SKILL.md LICENSE references assets scripts examples tests "$destination/"
)
```

## 3. 确认可用，再启用工作区记忆

确认安装目录下直接包含 `SKILL.md`，而不是多嵌套了一层同名文件夹。然后让 Agent 检查：

```text
请确认你能找到 workspace-memory 并读取它的 SKILL.md，暂不启用工作区记忆。
```

Codex CLI 或 IDE 扩展也可以用 `/skills` 查看。如果未出现，重启后再检查。[调用与发现机制见官方文档](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills)。

目标工作区需要由 Agent 读取根目录的 `AGENTS.md`。如果 Agent 使用另一种项目指令入口，从那里明确指向 `AGENTS.md`。校验和迁移审计脚本需要 Python 3.10+，无需额外 Python 包。

安装完成后，进入要持续工作的目录，按 [README 的开始使用步骤](../README.md#开始使用)启用记忆。安装 skill 本身不会创建工作区记忆，也不会启用其他项目。
