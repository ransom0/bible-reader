"""Command-line interface for bible-reader."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import sys

from . import __version__
from .asv_sources import convert_usfx_asv_to_bundle
from .importers import ImportErrorDetail, import_translation_bundle, import_translation_bundle_file
from .models import Verse
from .references import BibleReference, ReferenceParseError, parse_reference
from .render import PassageRenderer, SearchRenderer
from .repository import BibleRepository
from .storage import connect_database, create_sample_connection, initialize_database


PROGRAM_NAME = "bible"
DEFAULT_TRANSLATION = "ASV"
KNOWN_COMMANDS = {"books", "read", "search", "import-bundle", "import-usfx"}
THEMES = {"classic", "plain"}


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """CLI formatting and runtime options."""

    color: bool = True
    theme: str = "classic"
    db_path: Path | None = None


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
    parser.add_argument(
        "--db",
        metavar="PATH",
        help="read from or write to a SQLite Bible database",
    )

    subparsers = parser.add_subparsers(dest="command")

    books_parser = subparsers.add_parser(
        "books",
        help="list books available in the current database",
        description="List books available in the current database.",
    )
    books_parser.set_defaults(func=show_books)

    read_parser = subparsers.add_parser(
        "read",
        help="read a chapter from the current database",
        description="Read a chapter from the current database.",
    )
    read_parser.add_argument("reference", nargs="+", help="chapter reference, such as 'John 3'")
    read_parser.set_defaults(func=read_reference_command)

    search_parser = subparsers.add_parser(
        "search",
        help="search the current database for a word or phrase",
        description="Search the current database for a word or phrase.",
    )
    search_parser.add_argument("query", nargs="+", help="word or phrase to search for")
    search_parser.add_argument("--book", help="limit search results to one canonical book")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="maximum number of results to show",
    )
    search_parser.set_defaults(func=search_command)

    import_bundle_parser = subparsers.add_parser(
        "import-bundle",
        help="import a normalized JSON translation bundle into SQLite",
        description="Import a normalized JSON translation bundle into SQLite.",
    )
    import_bundle_parser.add_argument("source", help="path to a normalized translation bundle JSON file")
    import_bundle_parser.set_defaults(func=import_bundle_command)

    import_usfx_parser = subparsers.add_parser(
        "import-usfx",
        help="convert and import a local ASV USFX XML source into SQLite",
        description="Convert and import a local ASV USFX XML source into SQLite.",
    )
    import_usfx_parser.add_argument("source", help="path to a local ASV USFX XML source file")
    import_usfx_parser.set_defaults(func=import_usfx_command)

    parser.set_defaults(func=show_placeholder)
    return parser


def show_placeholder(_args: argparse.Namespace) -> int:
    """Show a short placeholder until the full Bible import arrives."""
    print("bible-reader is installed with the ASV sample fixture.")
    print("Try: bible books")
    print("Try: bible John 3:16")
    print("Try: bible read John 3")
    print("Try: bible search shepherd")
    print("Try: bible import-usfx SOURCE.usfx --db bible.sqlite3")
    return 0


def show_books(args: argparse.Namespace) -> int:
    """Print books from the selected database."""
    options = getattr(args, "render_options", RenderOptions())
    connection = _open_read_connection(options.db_path)
    try:
        repository = BibleRepository(connection)
        heading = "Books available"
        if options.db_path is None:
            heading += " in the ASV sample fixture"
        print(f"{heading}:")
        for book in repository.list_books():
            print(f"{book.order:>2}. {book.name}")
    finally:
        connection.close()
    return 0


def render_verses(reference: BibleReference, verses: list[Verse], options: RenderOptions) -> None:
    """Render a passage using the CLI passage renderer."""
    renderer = PassageRenderer(color=options.color, theme=options.theme)
    print(renderer.render(reference, verses, translation=DEFAULT_TRANSLATION))


def _open_read_connection(db_path: Path | None):
    if db_path is None:
        return create_sample_connection()
    connection = connect_database(db_path)
    initialize_database(connection)
    return connection


def _lookup(reference: BibleReference, db_path: Path | None = None) -> list[Verse]:
    connection = _open_read_connection(db_path)
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

    verses = _lookup(reference, options.db_path)
    if not verses:
        location = "selected database" if options.db_path is not None else "ASV sample fixture"
        print(f"Reference not found in the {location}: {reference.label()}", file=sys.stderr)
        return 1

    render_verses(reference, verses, options)
    return 0


def read_reference_command(args: argparse.Namespace) -> int:
    """Read a whole chapter from the selected database."""
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

    verses = _lookup(reference, options.db_path)
    if not verses:
        location = "selected database" if options.db_path is not None else "ASV sample fixture"
        print(f"Chapter not found in the {location}: {reference.label()}", file=sys.stderr)
        return 1

    render_verses(reference, verses, options)
    return 0


def search_command(args: argparse.Namespace) -> int:
    """Search verses in the selected database."""
    options = getattr(args, "render_options", RenderOptions())
    query = " ".join(args.query)
    if args.limit < 1:
        print("Error: --limit must be 1 or greater.", file=sys.stderr)
        return 2

    book_name: str | None = None
    if args.book:
        try:
            # Reuse the book alias normalizer without requiring a verse reference.
            from .references import normalize_book_name

            book_name = normalize_book_name(args.book)
        except ReferenceParseError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    connection = _open_read_connection(options.db_path)
    try:
        repository = BibleRepository(connection)
        results = repository.search_verses(
            translation_code=DEFAULT_TRANSLATION,
            query=query,
            book_name=book_name,
            limit=args.limit,
        )
    finally:
        connection.close()

    renderer = SearchRenderer(color=options.color, theme=options.theme)
    print(renderer.render(query, results, translation=DEFAULT_TRANSLATION))
    return 0 if results else 1


def import_bundle_command(args: argparse.Namespace) -> int:
    """Import a normalized translation bundle into SQLite."""
    options = getattr(args, "render_options", RenderOptions())
    if options.db_path is None:
        print("Error: import-bundle requires --db PATH.", file=sys.stderr)
        return 2

    try:
        connection = connect_database(options.db_path)
        try:
            import_translation_bundle_file(connection, args.source)
        finally:
            connection.close()
    except ImportErrorDetail as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Imported translation bundle into {options.db_path}")
    return 0


def import_usfx_command(args: argparse.Namespace) -> int:
    """Convert a local ASV USFX source and import it into SQLite."""
    options = getattr(args, "render_options", RenderOptions())
    if options.db_path is None:
        print("Error: import-usfx requires --db PATH.", file=sys.stderr)
        return 2

    try:
        bundle = convert_usfx_asv_to_bundle(args.source)
        connection = connect_database(options.db_path)
        try:
            import_translation_bundle(connection, bundle)
        finally:
            connection.close()
    except ImportErrorDetail as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Imported ASV USFX source into {options.db_path}")
    return 0


def extract_render_options(args_list: list[str]) -> tuple[list[str], RenderOptions, str | None]:
    """Extract global runtime flags before dispatching direct reference lookups.

    This keeps commands like ``bible --no-color John 3:16``,
    ``bible John 3:16 --theme plain``, and ``bible --db app.sqlite3 John 3``
    working even before reference lookup becomes a formal subcommand.
    """
    cleaned: list[str] = []
    color = True
    theme = "classic"
    db_path: Path | None = None
    index = 0
    while index < len(args_list):
        item = args_list[index]
        if item == "--no-color":
            color = False
            index += 1
            continue
        if item == "--theme":
            if index + 1 >= len(args_list):
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path), "--theme requires a value."
            theme = args_list[index + 1]
            index += 2
            continue
        if item.startswith("--theme="):
            theme = item.split("=", 1)[1]
            index += 1
            continue
        if item == "--db":
            if index + 1 >= len(args_list):
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path), "--db requires a value."
            db_path = Path(args_list[index + 1]).expanduser()
            index += 2
            continue
        if item.startswith("--db="):
            db_path = Path(item.split("=", 1)[1]).expanduser()
            index += 1
            continue
        cleaned.append(item)
        index += 1

    if theme not in THEMES:
        return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path), (
            f"Unknown theme: {theme}. Choose one of: {', '.join(sorted(THEMES))}."
        )
    return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path), None


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
