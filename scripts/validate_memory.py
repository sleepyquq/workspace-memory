#!/usr/bin/env python3
"""Read-only structural validation for a routed workspace-memory graph (Python 3.10+)."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from datetime import date
import os
from pathlib import Path
import re
import sys


SECTION_RE = re.compile(r"^## Workspace Memory\n(.*?)(?=^#{1,2} |\Z)", re.M | re.S)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.S)
WIKI_RE = re.compile(r"\[\[([^\]\n]+)\]\]")
QUOTED_RE = re.compile(r"'(?:[^'\n]|'')*'" r'|"(?:[^"\\\n]|\\[^\n])*"')
INLINE_OR_COMMENT_RE = re.compile(r"(?P<code>(?P<ticks>`+)(?!`)[^\n]+?(?<!`)(?P=ticks)(?!`))|<!--")
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
STATUSES = {"topic": {"active", "dormant", "archived"},
            "decision": {"active", "partially_superseded", "superseded", "archived"}}
REQUIRED = {"id", "type", "status", "summary", "updated"}
RELATIONS = {"supersedes", "superseded_by"}
STATE_MAX_LINES = 80
STATE_MAX_CHARS = 6000


def visible_markdown(text: str, *, inline: bool = False) -> str:
    """示例代码和注释不参与门禁或图边判断；保持行数便于诊断。"""
    def mask(value: str) -> str:
        # 用空白而非拼接两侧正文，不能把 Status: <!--...-->enabled 拼成有效门禁。
        return re.sub(r"[^\n]", " ", value)

    result = []
    fence = None
    comment = False
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\n"))
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            result.append(mask(line))
            continue
        if not comment and match and (match[1][0] == "~" or "`" not in match[2]):
            fence = match[1]
            result.append(mask(line))
            continue
        position = 0
        while position < len(line):
            if comment:
                end = line.find("-->", position)
                stop = len(line) if end == -1 else end + 3
                result.append(mask(line[position:stop]))
                comment = end == -1
            else:
                token = INLINE_OR_COMMENT_RE.search(line, position)
                if not token:
                    result.append(line[position:])
                    break
                result.append(line[position:token.start()])
                stop = token.end()
                if token.group("code"):
                    result.append(mask(token[0]) if inline else token[0])
                else:
                    result.append(mask(token[0]))
                    comment = True
            position = stop
    return "".join(result)


def safe_path(root: Path, raw: str, *, indexed: bool = False) -> Path | None:
    # 同时拒绝 POSIX、Windows/UNC 和 URI 形式，不能依赖宿主平台的 Path 判定。
    if not raw or raw != raw.strip() or raw.startswith("/") or any(c in raw for c in "\\:\x00"):
        return None
    parts = raw.rstrip("/").split("/")
    # 既有 AGENTS 索引允许 ./ 等归一化写法；解析后的边界仍必须通过。
    forbidden = {""} if indexed else {"", ".", ".."}
    if any(part in forbidden for part in parts):
        return None
    try:
        path = (root / raw).resolve()
        path.relative_to(root)
    except (OSError, ValueError, RuntimeError):
        return None
    return path


def valid_date(value: str) -> bool:
    try:
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and bool(date.fromisoformat(value))
    except ValueError:
        return False


def scalar_value(value: str) -> str:
    """只解析字段需要的字符串标量；不把集合、对象或损坏引号当作普通文字。"""
    value = value.strip()
    if not value:
        return ""
    if value[0] in "\"'":
        quoted = QUOTED_RE.match(value)
        if not quoted or (value[quoted.end():].strip() and not value[quoted.end():].lstrip().startswith("#")):
            raise ValueError("unclosed quote or text after quoted scalar")
        body = quoted[0][1:-1]
        if value[0] == "'":
            return body.replace("''", "'")
        escapes = {"0": "\0", "a": "\a", "b": "\b", "t": "\t", "n": "\n", "v": "\v",
                   "f": "\f", "r": "\r", "e": "\x1b", " ": " ", '"': '"', "/": "/",
                   "\\": "\\", "N": "\x85", "_": "\xa0", "L": "\u2028", "P": "\u2029"}

        def unescape(match):
            code = match[0][1:]
            if code[0] in "xuU":
                return chr(int(code[1:], 16))
            if code not in escapes:
                raise ValueError("invalid quoted scalar escape")
            return escapes[code]

        return re.sub(r"\\(?:x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|.)", unescape, body)
    value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
    if value.startswith("#") or value.lower() in {"null", "~"}:
        return ""
    if value[0] in "[{&*!|>" or re.match(r"[-?:](?:\s|$)", value) or re.search(r":(?:\s|$)", value):
        raise ValueError("expected a scalar, not a collection or YAML directive")
    return value


def relation_links(value: str) -> list[str]:
    """关系只接受带配对引号的链接或列表；检查分隔符后再解析目标。"""
    items = []
    if value.startswith("["):
        if not value.endswith("]"):
            raise ValueError("unclosed list")
        remaining = value[1:-1].strip()
        while remaining:
            match = QUOTED_RE.match(remaining)
            if not match:
                raise ValueError("expected quoted list item")
            items.append(match[0])
            remaining = remaining[match.end():].strip()
            if remaining:
                if not remaining.startswith(","):
                    raise ValueError("expected comma")
                remaining = remaining[1:].strip()
    elif value.startswith("- "):
        for line in value.splitlines():
            if not line.startswith("- "):
                raise ValueError("expected list item")
            items.append(line[2:].strip())
    else:
        items = [value]
    links = []
    for item in items:
        if not item.startswith(('"', "'")):
            raise ValueError("expected quoted link")
        match = WIKI_RE.fullmatch(scalar_value(item))
        if not match:
            raise ValueError("expected one wiki link")
        links.append(match[1])
    if not links:
        raise ValueError("empty relation")
    return links


def parse_frontmatter(label: str, text: str, errors: list[str]) -> dict[str, str]:
    """读取本技能的扁平字段子集，不解释任意 YAML 对象。未知字段保留给使用者。"""
    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append(f"{label}: missing YAML frontmatter")
        return {}
    values: dict[str, list[str]] = {}
    current = None
    for line in match[1].splitlines():
        field = re.match(r"^([a-z_]+):(?:[ \t]+(.*))?$", line)
        if field:
            current, value = field.groups()
            if current in values:
                errors.append(f"{label}: duplicate frontmatter field {current}")
            values[current] = [value or ""]
        elif line[:1].isspace() and current:
            values[current].append(line.strip())
        elif line.strip() and not line.startswith("#"):
            errors.append(f"{label}: unsupported frontmatter line {line!r}")
            current = None
    data = {}
    for key, parts in values.items():
        value = "\n".join(parts).strip()
        if key in REQUIRED:
            try:
                if parts[0] in {">", ">-", ">+", "|", "|-", "|+"}:
                    if key != "summary":
                        raise ValueError("block scalar is supported only for summary")
                    value = " ".join(parts[1:]).strip()
                else:
                    if key != "summary" and len(parts) > 1:
                        raise ValueError("expected a single-line scalar")
                    # 多行摘要可折叠，但每行不能偷偷引入列表或映射。
                    if len(parts) > 1 and not value.startswith(('"', "'")):
                        for part in parts:
                            scalar_value(part)
                    value = scalar_value(" ".join(parts))
            except ValueError as exc:
                errors.append(f"{label}: {key} must be a valid scalar: {exc}")
                value = ""
        data[key] = value
    for key in REQUIRED:
        if not data.get(key):
            errors.append(f"{label}: missing frontmatter field {key}")
        elif key != "summary" and "\n" in data[key]:
            errors.append(f"{label}: {key} must be a scalar")
    return data


def note_files(root: Path, errors: list[str]):
    """先检查目录边界，再遍历；拒绝链接目录，避免循环或重复别名。"""
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            items = sorted(entries, key=lambda entry: entry.name)
        for item in items:
            path = Path(item.path)
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(root)
            except (OSError, ValueError, RuntimeError):
                errors.append(f"{path.relative_to(root)}: path escapes memory Root or cannot be resolved")
                continue
            if item.is_dir():
                if resolved != path or item.is_symlink():
                    errors.append(f"{path.relative_to(root)}: linked directories are not supported")
                else:
                    pending.append(path)
            elif path.suffix == ".md":
                # 保留既有的根内文件链接；上方已在读取前检查真实目标边界。
                yield path


def validate(workspace: Path) -> tuple[list[str], list[str], str]:
    errors: list[str] = []
    warnings: list[str] = []
    workspace = workspace.resolve()
    agents = workspace / "AGENTS.md"
    if not agents.is_file() or not agents.resolve().is_relative_to(workspace):
        return ["AGENTS.md not found inside workspace"], warnings, ""
    text = agents.read_text(encoding="utf-8-sig")
    sections = list(SECTION_RE.finditer(visible_markdown(text)))
    if len(sections) != 1:
        return [f"expected one Workspace Memory section, found {len(sections)}"], warnings, ""
    body = sections[0][1]

    def lines(name: str) -> list[str]:
        return re.findall(rf"^[ \t]*{name}[ \t]*:.*$", body, re.M)

    # 门禁失败立刻返回：不解析路径、不枚举目录、不读取任何记忆内容。
    if lines("Status") != ["Status: enabled"]:
        return ["AGENTS.md: expected exactly 'Status: enabled'; memory not read"], warnings, ""
    indexed = {}
    for key in ("Root", "Entry", "Router"):
        found = lines(key)
        match = re.fullmatch(rf"{key}: `([^`]+)`", found[0]) if len(found) == 1 else None
        path = safe_path(workspace, match[1], indexed=True) if match else None
        if path is None:
            errors.append(f"AGENTS.md: expected one safe backtick-wrapped {key} path")
        else:
            indexed[key] = path
    if errors:
        return errors, warnings, ""
    root, entry, router = (indexed[key] for key in ("Root", "Entry", "Router"))
    if not root.is_dir():
        errors.append("Root does not exist as a directory")
    for key, path in (("Entry", entry), ("Router", router)):
        if not path.is_relative_to(root) or not path.is_file() or path.suffix != ".md":
            errors.append(f"{key} must be an existing .md file inside memory Root")
    if entry == router:
        errors.append("Entry and Router must be distinct notes")
    if errors:
        return errors, warnings, ""

    contents: dict[Path, str] = {}
    metadata: dict[Path, dict[str, str]] = {}
    by_rel: dict[str, Path] = {}
    by_stem: dict[str, list[Path]] = defaultdict(list)
    ids: dict[str, Path] = {}
    for path in sorted(note_files(root, errors)):
        rel = path.relative_to(root).as_posix()
        contents[path] = path.read_text(encoding="utf-8-sig")
        by_rel[rel[:-3]] = path
        by_stem[path.stem].append(path)
        folder = rel.split("/")[0]
        if folder not in {"topics", "decisions"}:
            continue
        data = parse_frontmatter(rel, contents[path], errors)
        metadata[path] = data
        kind = "topic" if folder == "topics" else "decision"
        if data.get("type") != kind:
            errors.append(f"{rel}: type must be {kind}")
        if not ID_RE.fullmatch(path.stem) or data.get("id") != path.stem:
            errors.append(f"{rel}: id must equal lowercase kebab-case filename stem")
        identifier = data.get("id")
        if identifier in ids:
            errors.append(f"{rel}: duplicate id {identifier!r}")
        elif identifier:
            ids[identifier] = path
        if data.get("status") not in STATUSES[kind]:
            errors.append(f"{rel}: unsupported {kind} status {data.get('status')!r}")
        if not valid_date(data.get("updated", "")):
            errors.append(f"{rel}: updated must be a real YYYY-MM-DD date")
        # Related 一直是推荐标题；图关系由真实链接决定，不强制英文标题。

    def resolve(source: Path, raw: str) -> Path | None:
        label = source.relative_to(root).as_posix()
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if not target and raw.startswith("#"):
            return source
        if target.endswith(".md"):
            target = target[:-3]
        if not target or target.startswith("/") or any(c in target for c in "\\:\x00"):
            errors.append(f"{label}: unsafe wiki link [[{raw}]]")
            return None
        if target.startswith(("./", "../")):
            # 兼容既有源笔记相对路径，但不允许逃逸，且绝不按同名回退。
            try:
                candidate = (source.parent / (target + ".md")).resolve()
                candidate.relative_to(root)
            except (OSError, ValueError, RuntimeError):
                errors.append(f"{label}: unsafe wiki link [[{raw}]]")
                return None
            matches = [candidate] if candidate in contents else []
        elif "/" in target:
            candidate = safe_path(root, target + ".md")
            if candidate is None:
                errors.append(f"{label}: unsafe wiki link [[{raw}]]")
                return None
            matches = [by_rel[target]] if target in by_rel else []
        else:
            # 只有真正的无路径简称允许按文件名消歧。
            matches = by_stem.get(target, [])
        if len(matches) != 1:
            reason = "ambiguous" if len(matches) > 1 else "broken"
            errors.append(f"{label}: {reason} wiki link [[{raw}]]")
            return None
        return matches[0]

    edges: dict[Path, set[Path]] = defaultdict(set)
    for source, content in contents.items():
        for raw in WIKI_RE.findall(visible_markdown(content, inline=True)):
            target = resolve(source, raw)
            if target is not None:
                edges[source].add(target)
    for source in metadata:
        for target in edges[source]:
            if target in metadata and source not in edges[target]:
                errors.append(f"non-reciprocal knowledge link: {source.relative_to(root)} -> {target.relative_to(root)}")

    # 新字段可选：旧决策的正文关系继续有效，只有采用类型化关系时才要求成对。
    relations: dict[tuple[Path, str], set[Path]] = defaultdict(set)
    for source, data in metadata.items():
        label = source.relative_to(root).as_posix()
        for field in sorted(RELATIONS & data.keys()):
            try:
                links = relation_links(data[field])
            except ValueError:
                errors.append(f"{label}: {field} must contain only quoted wiki links")
                links = []
            if data.get("type") != "decision":
                errors.append(f"{label}: {field} is decision-only")
            for raw in links:
                target = resolve(source, raw)
                if target is None:
                    continue
                if target == source or metadata.get(target, {}).get("type") != "decision":
                    errors.append(f"{label}: {field} must target another decision")
                else:
                    relations[source, field].add(target)
        outgoing = relations[source, "superseded_by"]
        status = data.get("status")
        if outgoing and status not in {"partially_superseded", "superseded", "archived"}:
            errors.append(f"{label}: superseded_by conflicts with status {status!r}")
        if status == "partially_superseded" and not outgoing:
            errors.append(f"{label}: partially_superseded requires superseded_by")
        if status == "superseded" and not outgoing:
            warnings.append(f"{label}: legacy superseded decision; add typed superseded_by when reconciling")
    for (source, field), targets in list(relations.items()):
        inverse = "supersedes" if field == "superseded_by" else "superseded_by"
        for target in targets:
            if source not in relations[target, inverse]:
                errors.append(f"{source.relative_to(root)}: {field} lacks reciprocal {inverse} in {target.relative_to(root)}")

    # 拓扑消除检查替代环；不按 updated 日期猜测哪个决定更权威。
    successors = {path: relations[path, "superseded_by"] for path in metadata}
    indegree = dict.fromkeys(metadata, 0)
    for targets in successors.values():
        for target in targets:
            indegree[target] += 1
    queue = deque(path for path, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        source = queue.popleft()
        visited += 1
        for target in successors[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(metadata):
        errors.append("decision supersession cycle detected")

    reachable = set()
    queue = deque(path for path in (entry, router) if path in contents)
    while queue:
        source = queue.popleft()
        if source not in reachable:
            reachable.add(source)
            queue.extend(edges[source] - reachable)
    for path in sorted(metadata.keys() - reachable):
        errors.append(f"orphaned note: {path.relative_to(root)}")

    state = contents.get(entry, "")
    if len(state.splitlines()) > STATE_MAX_LINES or len(state) > STATE_MAX_CHARS:
        warnings.append(f"{entry.relative_to(root)}: state is {len(state.splitlines())} lines / {len(state)} chars; "
                        f"review current-state compaction (soft limits {STATE_MAX_LINES} / {STATE_MAX_CHARS})")
    state_visible = visible_markdown(state, inline=True)
    updated = re.findall(r"^Last updated: (.*)$", state_visible, re.M)
    if len(updated) != 1 or not valid_date(updated[0]):
        warnings.append(f"{entry.relative_to(root)}: missing or invalid Last updated date")
    else:
        dates = [d for d in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", state_visible) if valid_date(d)]
        if any(d > updated[0] for d in dates):
            warnings.append(f"{entry.relative_to(root)}: body contains a date newer than Last updated; review whether future plan or stale header")
    summary = (f"{len(contents)} notes, {len(metadata)} knowledge notes, "
               f"{sum(map(len, edges.values()))} resolved links")
    return errors, warnings, summary


def main() -> int:
    # Windows 管道默认可能是 GBK；文件和 CLI 输出统一使用 UTF-8。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_root", type=Path)
    args = parser.parse_args()
    try:
        errors, warnings, summary = validate(args.workspace_root)
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        print(f"ERROR: cannot validate graph: {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"OK: {summary}" + (f"; {len(warnings)} review warning(s)" if warnings else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
