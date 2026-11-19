from __future__ import annotations

import json
import re
from pathlib import Path

from .model import Policy, ThreadSpec

POLICIES = {"SCHED_FIFO", "SCHED_RR", "SCHED_OTHER"}


def _policy(value: str) -> Policy:
    text = value.strip().upper().replace(" ", "_")
    if text in POLICIES:
        return text  # type: ignore[return-value]
    return "unknown"


def parse_yaml_lite_threads(text: str, source: str) -> list[ThreadSpec]:
    """Parse a narrow YAML subset used by schedgate.yml, without a YAML dependency."""
    threads: list[ThreadSpec] = []
    current: dict[str, str] = {}

    def flush() -> None:
        if not current:
            return
        name = current.get("name", f"thread{len(threads)+1}")
        threads.append(
            ThreadSpec(
                name=name,
                policy=_policy(current.get("policy", "unknown")),
                priority=int(current.get("priority", "0")),
                period_ns=int(current.get("period_ns", "0")),
                wcet_ns=int(current.get("wcet_ns", "0")),
                source=source,
            )
        )
        current.clear()

    in_threads = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^threads:\s*$", line):
            in_threads = True
            continue
        if in_threads and re.match(r"^[A-Za-z0-9_-]+:", line) and not line.startswith(" "):
            flush()
            in_threads = False
            continue
        if not in_threads:
            continue
        if re.match(r"^\s*-\s+name:", line) or re.match(r"^\s*-\s*$", line):
            flush()
        match = re.search(r"(name|policy|priority|period_ns|wcet_ns)\s*:\s*(.+)$", line)
        if match:
            if line.strip().startswith("-") and current:
                flush()
            current[match.group(1)] = match.group(2).strip().strip("\"'")
    flush()
    return threads


def parse_json_threads(text: str, source: str) -> list[ThreadSpec]:
    data = json.loads(text)
    rows = data["threads"] if isinstance(data, dict) else data
    threads: list[ThreadSpec] = []
    for row in rows:
        threads.append(
            ThreadSpec(
                name=str(row["name"]),
                policy=_policy(str(row.get("policy", "unknown"))),
                priority=int(row.get("priority", 0)),
                period_ns=int(row.get("period_ns", 0)),
                wcet_ns=int(row.get("wcet_ns", 0)),
                source=source,
            )
        )
    return threads


def load_threads(path: Path) -> list[ThreadSpec]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return parse_json_threads(text, str(path))
    return parse_yaml_lite_threads(text, str(path))
