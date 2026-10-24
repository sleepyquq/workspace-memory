#!/usr/bin/env python3
"""Read-only exact-anchor audit for workspace-memory migrations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
ENV_RE = re.compile(r"^(?P<name>[A-Z][A-Z0-9_]{2,})(?:[ \t]*=[ \t]*.*)?$")
PACKAGE_RE = re.compile(r"^(?:com|org|io|net)\.[A-Za-z0-9_.-]+$")
PROTOCOL_RE = re.compile(r"(?:^|[-_/])v\d+(?:$|[-_/])", re.IGNORECASE)
API_RE = re.compile(r"^(?:(?:GET|POST|PUT|PATCH|DELETE)\s+)?/(?:api|admin|release|device|devices|sessions|content|classes|reports|games|store)(?:/|$)", re.IGNORECASE)
COMMAND_RE = re.compile(r"^(?:npm|pnpm|yarn|go|docker|git|bash|sh|make|cargo|python\d*|pytest|npx)\s+")
SNAKE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
SCHEMA_CONTEXT_RE = re.compile(
    r"table|schema|column|field|index|record|migration|数据库|数据表|表名|字段|索引|迁移",
    re.IGNORECASE,
)
OPEN_ITEM_RE = re.compile(
    r"TODO|FIXME|尚未|仍需|还需|待完成|待补|待修|未完成|未解决|阻塞|风险|"
    r"next action|next step|remains outstanding|not yet|unfinished|blocked",
    re.IGNORECASE,
)
SENSITIVE_RE = re.compile(r"KEY|TOKEN|PASSWORD|PASSWD|SECRET|CREDENTIAL", re.IGNORECASE)
# 引号内可有空格；未闭合引号遮蔽到行末，避免把剩余凭据当普通文本输出。
SECRET_VALUE = r'''(?:"(?:\\.|[^"\\\r\n])*(?:"|$)|'(?:\\.|[^'\\\r\n])*(?:'|$)|[^\s`"']+)'''
ASSIGNMENT_RE = re.compile(
    rf"(?<![A-Za-z0-9_.-])(?P<name>[A-Za-z_][A-Za-z0-9_.-]*)(?P<separator>[ \t]*=[ \t]*)(?P<value>{SECRET_VALUE})"
)
OPTION_RE = re.compile(
    # 只消费带值的敏感选项，不能让 --verbose 或 --password-stdin 吞掉后面的敏感选项。
    rf"(?<![A-Za-z0-9_-])(?!--[A-Za-z0-9_-]*-stdin(?:[ \t=]|$))"
    rf"(?P<name>--[A-Za-z0-9_-]*(?:{SENSITIVE_RE.pattern})[A-Za-z0-9_-]*)"
    rf"(?P<separator>=|[ \t]+)(?P<value>{SECRET_VALUE})", re.IGNORECASE,
)
PATH_PREFIXES = (
    "backend/",
    "dashboard/",
    "deploy/",
    "docs/",
    ".github/",
    ".codex/",
    "/home/",
    "/srv/",
    "/data/",
    "/mnt/",
    "C:\\",
    "D:\\",
)
PATH_SUFFIX_RE = re.compile(
    r"\.(?:go|ts|tsx|js|jsx|cs|css|less|py|md|json|ya?ml|toml|sh|sql|env|conf|Dockerfile)$",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="legacy source file, or '-' for standard input")
    parser.add_argument("memory_root", type=Path, help="destination memory root")
    parser.add_argument("--section", help="extract an exact level-2 heading from the source")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--category",
        action="append",
        choices=("api", "protocol", "environment", "constant", "package", "path", "command", "schema"),
        help="limit exact anchors to one or more categories",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="return exit code 2 when exact-anchor candidates remain missing",
    )
    return parser.parse_args()


def read_source(raw: str) -> str:
    if raw == "-":
        return sys.stdin.read()
    return Path(raw).read_text(encoding="utf-8")


def extract_section(text: str, heading: str | None) -> str:
    if not heading:
        return text
    pattern = re.compile(
        rf"^## {re.escape(heading)}\r?\n(?P<body>.*?)(?=^#{{1,2}} |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"expected one level-2 section {heading!r}, found {len(matches)}")
    return f"## {heading}\n{matches[0].group('body')}"


def read_destination(memory_root: Path) -> tuple[str, int]:
    root = memory_root.resolve(strict=True)
    texts: list[str] = []
    count = 0
    for path in sorted(root.rglob("*.md")):
        try:
            path.resolve(strict=True).relative_to(root)
        except (OSError, ValueError) as exc:
            raise ValueError(f"destination note escapes memory root: {path}") from exc
        texts.append(path.read_text(encoding="utf-8"))
        count += 1
    return "\n".join(texts), count


def is_path(token: str) -> bool:
    if token.startswith(PATH_PREFIXES):
        return True
    if PATH_SUFFIX_RE.search(token):
        return True
    return token.startswith("./") or token.startswith("../")


def redact_sensitive(text: str) -> str:
    """所有审计输出共用脱敏；保留变量名/参数名，不回显其凭据值。"""
    def assignment(match):
        value = match["value"]
        if len(value) > 1 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        # 引用环境变量不是回显凭据；这类安全命令仍应接受精确迁移覆盖检查。
        if re.fullmatch(r"\$(?:\{[A-Za-z_][A-Za-z0-9_]*\}|(?:env:)?[A-Za-z_][A-Za-z0-9_]*)|%[A-Za-z_][A-Za-z0-9_]*%", value):
            return match[0]
        if SENSITIVE_RE.search(match["name"]):
            return match["name"] + match["separator"] + "<redacted>"
        return match[0]

    return ASSIGNMENT_RE.sub(assignment, OPTION_RE.sub(assignment, text))


def redact_token(token: str) -> str | None:
    match = ENV_RE.fullmatch(token)
    if match:
        return match.group("name")
    if redact_sensitive(token) != token:
        # 含凭据的整条命令进入脱敏审查队列，不要求把它逐字迁入记忆。
        return None
    return token


def classify(token: str, line: str, source_count: int) -> set[str]:
    categories: set[str] = set()
    if API_RE.search(token):
        categories.add("api")
    if PROTOCOL_RE.search(token):
        categories.add("protocol")
    if ENV_RE.fullmatch(token):
        if token.startswith(("LLM_", "UMI_", "RELEASE_", "ALLOW_", "DATABASE_", "PUBLIC_PATH", "FRAMEWORK_", "GIT_SSH")) or re.search(
            r"env|environment|config|配置|环境变量", line, re.IGNORECASE
        ):
            categories.add("environment")
        else:
            categories.add("constant")
    if PACKAGE_RE.fullmatch(token):
        categories.add("package")
    if is_path(token):
        categories.add("path")
    if COMMAND_RE.search(token):
        categories.add("command")
    if SNAKE_RE.fullmatch(token) and (source_count > 1 or SCHEMA_CONTEXT_RE.search(line)):
        categories.add("schema")
    return categories


def normalized_open_item(line: str) -> str:
    value = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", line).strip()
    return redact_sensitive(value)[:500]


def anchor_present(value: str, destination: str, categories: set[str]) -> bool:
    """按技术标识符边界匹配，避免把相邻中文或句末标点当成标识符的一部分。"""
    literal = re.escape(value)
    if categories & {"api", "protocol", "package", "path", "command"}:
        # 路径、包名、协议和命令的连接符也能延长标识符。
        # 句末单独的点/冒号是标点，但 .bak、:unit 等是不同的完整标识符。
        pattern = (
            rf"(?<![A-Za-z0-9_./\\:+-]){literal}"
            r"(?![A-Za-z0-9_/\\+-])(?![.:][A-Za-z0-9_./\\:+-])"
        )
    else:
        # 字段、常量和环境变量允许限定写法 runs.task_id，但不接受 previous_task_id。
        pattern = rf"(?<![A-Za-z0-9_]){literal}(?![A-Za-z0-9_])"
    return re.search(pattern, destination) is not None


def build_report(source: str, destination: str, destination_files: int, selected: set[str] | None) -> dict[str, object]:
    raw_tokens = [match.group(1).strip() for match in INLINE_CODE_RE.finditer(source)]
    counts = Counter(token for token in raw_tokens if 2 < len(token) <= 240)
    anchors: dict[str, dict[str, object]] = {}
    sensitive: list[dict[str, object]] = []

    for line_number, line in enumerate(source.splitlines(), start=1):
        safe_line = redact_sensitive(line)
        if safe_line != line:
            sensitive.append({"source_line": line_number, "text": safe_line.strip()[:500]})
        for match in INLINE_CODE_RE.finditer(line):
            original = match.group(1).strip()
            if original not in counts:
                continue
            value = redact_token(original)
            if value is None:
                continue
            all_categories = classify(value, line, counts[original])
            categories = all_categories & selected if selected else all_categories
            if not categories:
                continue
            item = anchors.setdefault(
                value,
                {
                    "value": value,
                    "categories": set(),
                    "source_lines": [],
                    "source_count": 0,
                    "present": anchor_present(value, destination, all_categories),
                },
            )
            item["categories"].update(categories)
            item["source_lines"].append(line_number)
            item["source_count"] = int(item["source_count"]) + 1

    serializable: list[dict[str, object]] = []
    for item in anchors.values():
        serializable.append(
            {
                **item,
                "categories": sorted(item["categories"]),
                "source_lines": sorted(set(item["source_lines"])),
            }
        )
    serializable.sort(key=lambda item: (not bool(item["present"]), item["categories"], str(item["value"]).lower()))

    open_items: list[dict[str, object]] = []
    seen_open: set[str] = set()
    for line_number, line in enumerate(source.splitlines(), start=1):
        if not OPEN_ITEM_RE.search(line):
            continue
        value = normalized_open_item(line)
        if not value or value in seen_open:
            continue
        seen_open.add(value)
        open_items.append(
            {
                "source_line": line_number,
                "text": value,
                "verbatim_present": value in destination,
            }
        )

    missing = [item for item in serializable if not item["present"]]
    return {
        "source_lines": len(source.splitlines()),
        "destination_markdown_files": destination_files,
        "anchor_candidates": len(serializable),
        "anchors_present": len(serializable) - len(missing),
        "anchors_missing": len(missing),
        "missing": missing,
        "open_item_candidates": open_items,
        "sensitive_candidates": sensitive,
    }


def print_text(report: dict[str, object]) -> None:
    print(
        "Exact-anchor audit: "
        f"{report['anchors_present']}/{report['anchor_candidates']} present; "
        f"{report['anchors_missing']} require review; "
        f"{len(report['open_item_candidates'])} open-item candidates"
    )
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in report["missing"]:
        for category in item["categories"]:
            grouped[category].append(item)
    for category in sorted(grouped):
        print(f"\n[{category}]")
        for item in grouped[category]:
            lines = ",".join(str(value) for value in item["source_lines"])
            print(f"- {item['value']} (source lines {lines})")
    if report["open_item_candidates"]:
        print("\n[open-items: map or supersede each]")
        for item in report["open_item_candidates"]:
            marker = "present" if item["verbatim_present"] else "review"
            print(f"- L{item['source_line']} [{marker}] {item['text']}")
    if report["sensitive_candidates"]:
        print("\n[sensitive-items: keep credential values out of memory]")
        for item in report["sensitive_candidates"]:
            print(f"- L{item['source_line']} {item['text']}")


def main() -> int:
    # 管道输入与 JSON 输出统一使用 UTF-8，避免 Windows 系统编码吞掉中文候选。
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        source = extract_section(read_source(args.source), args.section)
        destination, destination_files = read_destination(args.memory_root)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    selected = set(args.category) if args.category else None
    report = build_report(source, destination, destination_files, selected)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    if args.fail_on_missing and report["anchors_missing"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
