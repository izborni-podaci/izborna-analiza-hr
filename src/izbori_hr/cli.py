"""Command line: fetch DIP's files, build the site."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from izbori_hr.elections import BY_ID, ELECTIONS


def cmd_fetch(args) -> int:
    from izbori_hr import fetch
    chosen = [BY_ID[i] for i in args.election] if args.election else list(ELECTIONS)
    changed = [e.id for e in chosen if fetch.fetch(e, Path(args.data))]
    print("changed: " + (", ".join(changed) if changed else "nothing"))
    return 0


def cmd_site(args) -> int:
    from izbori_hr.site import build
    build(Path(args.data), Path(args.out))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="izbori-hr")
    p.add_argument("--data", default="data", help="the archive's folder (default: data)")
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch", help="download elections' results from DIP's archive (only what changed is written)")
    f.add_argument("election", nargs="*", choices=sorted(BY_ID), help="elections to fetch (default: all)")
    f.set_defaults(func=cmd_fetch)
    s = sub.add_parser("site", help="build the static site")
    s.add_argument("--out", default="_site")
    s.set_defaults(func=cmd_site)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
