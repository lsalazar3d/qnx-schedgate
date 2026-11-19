from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .analyze import inspect_tree
from .report import as_html, as_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schedgate",
        description="Lint QNX 8.0 IFS buildfiles, Makefiles, and thread timing specs on the host.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Project directory to inspect (default: current directory)")
    parser.add_argument("--html", metavar="FILE", help="Write an HTML report to FILE")
    parser.add_argument("--text", metavar="FILE", help="Write a text report to FILE")
    parser.add_argument("--version", action="version", version=f"schedgate {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"schedgate: path not found: {root}", file=sys.stderr)
        return 2
    report = inspect_tree(root)
    text = as_text(report)
    print(text)
    if args.text:
        Path(args.text).write_text(text, encoding="utf-8")
    if args.html:
        Path(args.html).write_text(as_html(report), encoding="utf-8")
    if report.errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
