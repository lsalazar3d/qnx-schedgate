from __future__ import annotations

from pathlib import Path

from .model import Report, ThreadSpec
from .parse_ifs import parse_ifs
from .parse_make import parse_make
from .parse_spec import load_threads
from .sched import rate_monotonic_ok, utilization


def analyze_threads(report: Report, threads: list[ThreadSpec]) -> None:
    report.threads.extend(threads)
    for thread in threads:
        if thread.period_ns < 0 or thread.wcet_ns < 0:
            report.add("error", "bad-timing", f"{thread.name} has a negative period or WCET.", thread.source)
        if thread.period_ns > 0 and thread.wcet_ns > thread.period_ns:
            report.add(
                "error",
                "wcet-exceeds-period",
                f"{thread.name} WCET {thread.wcet_ns} ns is longer than its period {thread.period_ns} ns.",
                thread.source,
            )
        if thread.period_ns > 0 and thread.period_ns < 10_000_000 and thread.priority < 10:
            report.add(
                "warning",
                "low-priority-tight-period",
                f"{thread.name} claims a period under 10 ms but only priority {thread.priority}. QNX 8.0 realtime work usually needs an explicit high priority.",
                thread.source,
            )
        if thread.period_ns > 0 and thread.policy == "SCHED_OTHER":
            report.add(
                "error",
                "other-on-deadline",
                f"{thread.name} has a periodic deadline but uses SCHED_OTHER. Use SCHED_FIFO or SCHED_RR on QNX 8.0.",
                thread.source,
            )
        if thread.period_ns > 0 and thread.policy == "unknown":
            report.add(
                "warning",
                "missing-policy",
                f"{thread.name} has no scheduling policy. Name SCHED_FIFO or SCHED_RR explicitly.",
                thread.source,
            )
        if thread.priority < 0 or thread.priority > 255:
            report.add("error", "bad-priority", f"{thread.name} priority {thread.priority} is outside 0–255.", thread.source)

    ok, u, bound = rate_monotonic_ok(threads)
    report.utilization = u
    report.liu_layland_bound = bound
    report.schedulable = ok
    periodic = [t for t in threads if t.period_ns > 0]
    if ok is True:
        report.add(
            "note",
            "schedulable",
            f"Periodic utilization is {u:.3f} with a Liu-Layland bound of {bound:.3f} for {len(periodic)} threads. The set is schedulable under rate-monotonic assumptions.",
        )
    elif ok is False:
        report.add(
            "error",
            "unschedulable",
            f"Periodic utilization is {u:.3f}, above the Liu-Layland bound of {bound:.3f}, and it also fails the hyperbolic bound. This set is not provably schedulable as written.",
        )


def inspect_tree(root: Path) -> Report:
    report = Report(title=f"schedgate report for {root}")
    threads: list[ThreadSpec] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", "__pycache__", ".venv"} for part in path.parts):
            continue
        suffix = path.suffix.lower()
        name = path.name.lower()
        if name in {"schedgate.yml", "schedgate.yaml"} or name.endswith(".schedgate.json"):
            report.files.append(str(path))
            threads.extend(load_threads(path))
        elif name in {"buildfile", "ifs.noecho", "ifs.build"} or suffix == ".build" or name.endswith(".buildfile"):
            report.files.append(str(path))
            for finding in parse_ifs(path):
                report.findings.append(finding)
        elif name in {"makefile", "common.mk", "recursively.mk"} or suffix == ".mk":
            report.files.append(str(path))
            for finding in parse_make(path):
                report.findings.append(finding)

    analyze_threads(report, threads)
    if not threads:
        report.add(
            "warning",
            "no-thread-spec",
            "No schedgate.yml or .schedgate.json was found. Add one so the host tool can check periods, WCETs, and policies even before you boot QEMU.",
        )
    return report
