"""Command-line entry point."""

import argparse

from irish_schools import build, sources, web


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="schools")
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch", help="download and verify the source files")
    fetch.add_argument("--force", action="store_true", help="download again")
    sub.add_parser("build", help="build the datasets in data/")
    sub.add_parser("web", help="write the web viewer data to site/public/")
    args = parser.parse_args(argv)

    if args.command == "fetch":
        for path in sources.fetch_all(force=args.force):
            print(path.relative_to(sources.ROOT))
    elif args.command == "build":
        for path in build.build_all():
            print(path.relative_to(sources.ROOT))
    elif args.command == "web":
        for path in web.build_site_data():
            print(path.relative_to(sources.ROOT))
