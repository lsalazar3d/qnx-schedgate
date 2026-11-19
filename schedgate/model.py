from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Policy = Literal["SCHED_FIFO", "SCHED_RR", "SCHED_OTHER", "unknown"]


@dataclass(frozen=True)
class ThreadSpec:
    name: str
    policy: Policy
    priority: int
    period_ns: int
    wcet_ns: int
    source: str


@dataclass(frozen=True)
class Finding:
    severity: Literal["error", "warning", "note"]
    code: str
    message: str
    source: str = ""


@dataclass
class Report:
    title: str
    files: list[str] = field(default_factory=list)
    threads: list[ThreadSpec] = field(default_factory=list)
    utilization: float = 0.0
    liu_layland_bound: float = 0.0
    schedulable: bool | None = None
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: Literal["error", "warning", "note"], code: str, message: str, source: str = "") -> None:
        self.findings.append(Finding(severity=severity, code=code, message=message, source=source))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]
