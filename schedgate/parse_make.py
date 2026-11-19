from __future__ import annotations

import re
from pathlib import Path

from .model import Finding

QNX_HINTS = (
    "qcc",
    "ntoaarch64",
    "ntox86_64",
    "qnx_target",
    "qnx_host",
    "qnx_configuration",
    "recursively.mk",
    "common.mk",
    "hinstall",
    "usr/include",
)


def parse_make(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    hints = [hint for hint in QNX_HINTS if hint in lower]
    if not hints:
        findings.append(
            Finding(
                "warning",
                "make-no-qnx-hint",
                "Makefile does not mention qcc, QNX_TARGET, recursively.mk, or another QNX 8.0 hint. Judges need evidence the project builds for QNX.",
                str(path),
            )
        )
    if "qnx_target" not in lower and "qcc" in lower:
        findings.append(
            Finding(
                "note",
                "make-qcc-without-target",
                "qcc is used but QNX_TARGET is never referenced. Document the QNX SDP 8.0 environment in the Makefile or README.",
                str(path),
            )
        )
    if re.search(r"\bgcc\b", lower) and "qcc" not in lower and "host" not in lower:
        findings.append(
            Finding(
                "warning",
                "make-host-gcc-only",
                "The Makefile appears to use host gcc without a QNX qcc path. Add a qcc target for QNX 8.0, and keep the host build only as a smoke test.",
                str(path),
            )
        )
    if "cflags" in lower and "-fno-common" not in lower and "qcc" in lower:
        findings.append(
            Finding(
                "note",
                "make-missing-fno-common",
                "Consider passing -fno-common on qcc builds so multiple-definition surprises appear at link time.",
                str(path),
            )
        )
    return findings
