"""Command-line interface for bible-reader."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__
from .repository import BibleRepository
from .storage import create_sample_connection


PROGRAM_NAME = "bible"


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Offline-first Bible reader, search, notes, and study tool.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    books_parser = subparsers.add_parser(
        "books",
        help="list books available in the current fixture database",
        description="List books available in the current fixture database.",
    )
    books_parser.set_defaults(func=show_books)

    parser.set_defaults(func=show_placeholder)
    return parser


def show_placeholder(_args: argparse.Namespace) -> int:
    """Show a short placeholder until reading commands are implemented."""
    print("bible-reader is installed. Reading commands arrive in the next stages.")
    print("Try: bible --help")
    print("Try: bible books")
    return 0


def show_books(_args: argparse.Namespace) -> int:
    """Print books from the temporary in-memory fixture database."""
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        print("Books available in the ASV sample fixture:")
        for book in repository.list_books():
            print(f"{book.order:>2}. {book.name}")
    finally:
        connection.close()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
