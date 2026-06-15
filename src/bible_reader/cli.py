"""Command-line interface for bible-reader."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
import sys

from . import __version__
from .models import Verse
from .references import BibleReference, ReferenceParseError, parse_reference
from .render import PassageRenderer
from .repository import BibleRepository
from .storage import create_sample_connection


PROGRAM_NAME = "bible"
DEFAULT_TRANSLATION = "ASV"
KNOWN_COMMANDS = {"books", "read"}
THEMES = {"classic", "plain"}


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """CLI formatting options."""

    color: bool = True
    theme: str = "classic"



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
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI color and emphasis",
    )
    parser.add_argument(
        "--theme",
        choices=sorted(THEMES),
        default="classic",
        help="terminal formatting theme",
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


def render_verses(reference: BibleReference, verses: list[Verse], options: RenderOptions) -> None:
    """Render a passage using the CLI passage renderer."""
    renderer = PassageRenderer(color=options.color, theme=options.theme)
    print(renderer.render(reference, verses, translation=DEFAULT_TRANSLATION))


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


def lookup_reference_text(raw_reference: str, options: RenderOptions | None = None) -> int:
    """Parse, look up, and print a Bible reference from user text."""
    options = options or RenderOptions()
    try:
        reference = parse_reference(raw_reference)
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    verses = _lookup(reference)
    if not verses:
        print(f"Reference not found in the ASV sample fixture: {reference.label()}", file=sys.stderr)
        return 1

    render_verses(reference, verses, options)
    return 0


def read_reference_command(args: argparse.Namespace) -> int:
    """Read a whole chapter from the fixture database."""
    options = getattr(args, "render_options", RenderOptions())
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

    render_verses(reference, verses, options)
    return 0


def extract_render_options(args_list: list[str]) -> tuple[list[str], RenderOptions, str | None]:
    """Extract formatting flags before dispatching direct reference lookups.

    This keeps commands like ``bible --no-color John 3:16`` and
    ``bible John 3:16 --theme plain`` working even before the CLI has a full
    subcommand for reference lookup.
    """
    cleaned: list[str] = []
    color = True
    theme = "classic"
    index = 0
    while index < len(args_list):
        item = args_list[index]
        if item == "--no-color":
            color = False
            index += 1
            continue
        if item == "--theme":
            if index + 1 >= len(args_list):
                return cleaned, RenderOptions(color=color, theme=theme), "--theme requires a value."
            theme = args_list[index + 1]
            index += 2
            continue
        if item.startswith("--theme="):
            theme = item.split("=", 1)[1]
            index += 1
            continue
        cleaned.append(item)
        index += 1

    if theme not in THEMES:
        return cleaned, RenderOptions(color=color, theme=theme), (
            f"Unknown theme: {theme}. Choose one of: {', '.join(sorted(THEMES))}."
        )
    return cleaned, RenderOptions(color=color, theme=theme), None


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    args_list, render_options, render_error = extract_render_options(raw_args)
    if render_error is not None:
        print(f"Error: {render_error}", file=sys.stderr)
        return 2

    if args_list and not args_list[0].startswith("-") and args_list[0] not in KNOWN_COMMANDS:
        return lookup_reference_text(" ".join(args_list), render_options)

    parser = build_parser()
    args = parser.parse_args(args_list)
    args.render_options = render_options
    return int(args.func(args))
