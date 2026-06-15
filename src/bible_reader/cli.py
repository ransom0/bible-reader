"""Command-line interface for bible-reader."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys

from . import __version__
from .models import Verse
from .references import BibleReference, ReferenceParseError, parse_reference
from .repository import BibleRepository
from .storage import create_sample_connection


PROGRAM_NAME = "bible"
DEFAULT_TRANSLATION = "ASV"
KNOWN_COMMANDS = {"books", "read"}


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

    read_parser = subparsers.add_parser(
        "read",
        help="read a chapter from the current fixture database",
        description="Read a chapter from the current fixture database.",
    )
    read_parser.add_argument("reference", nargs="+", help="chapter reference, such as 'John 3'")
    read_parser.set_defaults(func=read_reference_command)

    parser.set_defaults(func=show_placeholder)
    return parser


def show_placeholder(_args: argparse.Namespace) -> int:
    """Show a short placeholder until the full Bible import arrives."""
    print("bible-reader is installed with the ASV sample fixture.")
    print("Try: bible books")
    print("Try: bible John 3:16")
    print("Try: bible read John 3")
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


def render_verses(reference: BibleReference, verses: list[Verse]) -> None:
    """Render a passage in a simple readable format."""
    print(f"{reference.label()} ({DEFAULT_TRANSLATION})")
    print()
    for verse in verses:
        print(f"{verse.verse:>3}  {verse.text}")


def _lookup(reference: BibleReference) -> list[Verse]:
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        if reference.is_chapter:
            return repository.get_chapter(
                translation_code=DEFAULT_TRANSLATION,
                book_name=reference.book,
                chapter=reference.chapter,
            )
        return repository.get_verse_range(
            translation_code=DEFAULT_TRANSLATION,
            book_name=reference.book,
            chapter=reference.chapter,
            start_verse=reference.start_verse or 1,
            end_verse=reference.end_verse or reference.start_verse or 1,
        )
    finally:
        connection.close()


def lookup_reference_text(raw_reference: str) -> int:
    """Parse, look up, and print a Bible reference from user text."""
    try:
        reference = parse_reference(raw_reference)
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    verses = _lookup(reference)
    if not verses:
        print(f"Reference not found in the ASV sample fixture: {reference.label()}", file=sys.stderr)
        return 1

    render_verses(reference, verses)
    return 0


def read_reference_command(args: argparse.Namespace) -> int:
    """Read a whole chapter from the fixture database."""
    raw_reference = " ".join(args.reference)
    try:
        reference = parse_reference(raw_reference)
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not reference.is_chapter:
        print("Error: read expects a chapter reference, such as 'John 3'.", file=sys.stderr)
        return 2

    verses = _lookup(reference)
    if not verses:
        print(f"Chapter not found in the ASV sample fixture: {reference.label()}", file=sys.stderr)
        return 1

    render_verses(reference, verses)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""
    args_list = list(argv) if argv is not None else sys.argv[1:]
    if args_list and not args_list[0].startswith("-") and args_list[0] not in KNOWN_COMMANDS:
        return lookup_reference_text(" ".join(args_list))

    parser = build_parser()
    args = parser.parse_args(args_list)
    return int(args.func(args))
