"""Command-line entry point."""

import argparse

from irish_schools import sources


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="schools")
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch", help="download and verify the source files")
    fetch.add_argument("--force", action="store_true", help="download again")
    args = parser.parse_args(argv)

    if args.command == "fetch":
        for path in sources.fetch_all(force=args.force):
            print(path.relative_to(sources.ROOT))
