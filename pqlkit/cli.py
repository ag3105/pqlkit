"""Command line interface for pqlkit."""

from __future__ import annotations

import argparse
import sys

from .explain import explain
from .formatter import format_pql


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pqlkit",
        description="Format and explain Adobe Experience Platform PQL.",
    )
    parser.add_argument("query", nargs="?", help="PQL expression. Omit to read stdin.")
    parser.add_argument("-e", "--explain", action="store_true",
                        help="Also print a plain-English explanation.")
    parser.add_argument("-o", "--only-explain", action="store_true",
                        help="Print the explanation only.")
    args = parser.parse_args(argv)

    src = args.query if args.query else sys.stdin.read()
    src = src.strip()
    if not src:
        parser.error("no PQL provided")

    if args.only_explain:
        print(explain(src))
        return 0

    print(format_pql(src))
    if args.explain:
        print()
        print(explain(src))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
