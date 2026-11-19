from __future__ import annotations

import re
from pathlib import Path

from .model import Finding

ATTR_RE = re.compile(r"\[([^\]]+)\]")
PERM_RE = re.compile(r"(?:perms?|mode)\s*=\s*([0-7]{3,4})")


def parse_ifs(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    has_bootstrap = False
    has_startup = False
    waitfor = 0
    display_msg = 0

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        loc = f"{path}:{lineno}"
        lower = line.lower()
        if line.startswith("[") and "bootstrap" in lower:
            has_bootstrap = True
        if "startup" in lower and not line.startswith("#"):
            has_startup = True
        if "waitfor" in lower:
            waitfor += 1
        if lower.startswith("display_msg") or "display_msg" in lower:
            display_msg += 1
        attrs = ",".join(ATTR_RE.findall(line))
        perm_match = PERM_RE.search(attrs) or PERM_RE.search(line)
        if perm_match:
            mode = perm_match.group(1)[-3:]
            if mode[1] in "237" or mode[2] in "237":  # group/world writable
                findings.append(
                    Finding(
                        "error",
                        "ifs-world-writable",
                        f"IFS entry looks group/world writable (mode {perm_match.group(1)}): {line}",
                        loc,
                    )
                )
        if re.search(r"\s/tmp/|\s/dev/shmem/.+\s", line) and "type=link" not in line.lower():
            findings.append(
                Finding(
                    "warning",
                    "ifs-tmp-copy",
                    f"IFS copies a file into a volatile path without a documented link: {line}",
                    loc,
                )
            )
        if line.endswith("&") and "reopen" not in lower and "waitfor" not in lower:
            # backgrounded start without a nearby wait is flagged later if waitfor==0
            pass

    if not has_bootstrap and not has_startup:
        findings.append(
            Finding(
                "warning",
                "ifs-no-startup",
                "No [bootstrap] or startup stanza was found in the buildfile.",
                str(path),
            )
        )
    if display_msg == 0:
        findings.append(
            Finding(
                "note",
                "ifs-no-display-msg",
                "No display_msg lines were found. A short boot banner makes QEMU demos easier to judge.",
                str(path),
            )
        )
    if waitfor == 0:
        findings.append(
            Finding(
                "warning",
                "ifs-no-waitfor",
                "No waitfor lines were found. QNX startup scripts usually wait for /dev or service paths before launching dependents.",
                str(path),
            )
        )
    return findings
