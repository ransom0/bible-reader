"""Command-line interface for bible-reader."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from . import __version__
from .asv_sources import convert_asv_source_to_bundle, summarize_bundle
from .default_data import initialize_default_database
from .importers import ImportErrorDetail, import_translation_bundle, import_translation_bundle_file
from .models import Verse
from .references import BibleReference, ReferenceParseError, parse_reference
from .render import ComparisonRenderer, PassageRenderer, SearchRenderer
from .repository import BibleRepository
from .storage import connect_database, create_sample_connection, default_database_path, initialize_database
from .study import StudyStore, StudyStoreError, default_study_path
from .tui import render_tui_plan


PROGRAM_NAME = "bible"
DEFAULT_TRANSLATION = "ASV"
KNOWN_COMMANDS = {"books", "chapters", "read", "next", "previous", "search", "compare", "tui", "doctor", "bookmark", "bookmarks", "note", "notes", "init-db", "import-bundle", "import-usfx"}
THEMES = {"classic", "plain"}


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """CLI formatting and runtime options."""

    color: bool = True
    theme: str = "classic"
    db_path: Path | None = None
    study_path: Path | None = None
    width: int | None = None


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
    parser.add_argument(
        "--study",
        metavar="PATH",
        help="read/write bookmarks and notes from this JSON study-data file",
    )
    parser.add_argument(
        "--width",
        type=int,
        metavar="COLS",
        help="wrap passage/search output to this terminal width",
    )

    subparsers = parser.add_subparsers(dest="command")

    books_parser = subparsers.add_parser(
        "books",
        help="list books available in the current database",
        description="List books available in the current database.",
    )
    books_parser.set_defaults(func=show_books)

    chapters_parser = subparsers.add_parser(
        "chapters",
        help="list chapters available for a book",
        description="List chapters available for a book in the current database.",
    )
    chapters_parser.add_argument("book", nargs="+", help="book name or abbreviation, such as 'John' or 'Ps'")
    chapters_parser.set_defaults(func=show_chapters)

    read_parser = subparsers.add_parser(
        "read",
        help="read a chapter from the current database",
        description="Read a chapter from the current database.",
    )
    read_parser.add_argument("reference", nargs="+", help="chapter reference, such as 'John 3'")
    read_parser.set_defaults(func=read_reference_command)

    next_parser = subparsers.add_parser(
        "next",
        help="read the next available chapter",
        description="Read the next available chapter after a chapter reference.",
    )
    next_parser.add_argument("reference", nargs="+", help="chapter reference, such as 'John 3'")
    next_parser.set_defaults(func=next_chapter_command)

    previous_parser = subparsers.add_parser(
        "previous",
        help="read the previous available chapter",
        description="Read the previous available chapter before a chapter reference.",
    )
    previous_parser.add_argument("reference", nargs="+", help="chapter reference, such as 'John 3'")
    previous_parser.set_defaults(func=previous_chapter_command)

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

    compare_parser = subparsers.add_parser(
        "compare",
        help="compare a passage across available translations",
        description="Compare one passage across available translations in the current database.",
    )
    compare_parser.add_argument("reference", nargs="+", help="passage reference, such as 'John 3:16'")
    compare_parser.add_argument(
        "--versions",
        help="comma-separated translation codes to compare; defaults to all available translations",
    )
    compare_parser.set_defaults(func=compare_command)

    tui_parser = subparsers.add_parser(
        "tui",
        help="show the planned terminal UI foundation",
        description="Show the planned terminal UI foundation before the interactive TUI is implemented.",
    )
    tui_parser.set_defaults(func=tui_plan_command)


    doctor_parser = subparsers.add_parser(
        "doctor",
        help="show install and runtime diagnostics",
        description="Show install, runtime, and local data diagnostics for release smoke tests.",
    )
    doctor_parser.set_defaults(func=doctor_command)


    bookmark_parser = subparsers.add_parser(
        "bookmark",
        help="add, list, or remove local bookmarks",
        description="Add, list, or remove local bookmarks stored outside Bible text.",
    )
    bookmark_subparsers = bookmark_parser.add_subparsers(dest="bookmark_command")

    bookmark_add_parser = bookmark_subparsers.add_parser("add", help="bookmark a Bible reference")
    bookmark_add_parser.add_argument("reference", nargs="+", help="reference to bookmark, such as 'John 3:16'")
    bookmark_add_parser.add_argument("--label", default="", help="optional short label for the bookmark")
    bookmark_add_parser.set_defaults(func=bookmark_add_command)

    bookmark_list_parser = bookmark_subparsers.add_parser("list", help="list bookmarks")
    bookmark_list_parser.set_defaults(func=bookmark_list_command)

    bookmark_remove_parser = bookmark_subparsers.add_parser("remove", help="remove a bookmark")
    bookmark_remove_parser.add_argument("reference", nargs="+", help="reference to remove, such as 'John 3:16'")
    bookmark_remove_parser.set_defaults(func=bookmark_remove_command)
    bookmark_parser.set_defaults(func=bookmark_list_command)

    bookmarks_parser = subparsers.add_parser(
        "bookmarks",
        help="list local bookmarks",
        description="List local bookmarks stored outside Bible text.",
    )
    bookmarks_parser.set_defaults(func=bookmark_list_command)

    note_parser = subparsers.add_parser(
        "note",
        help="add or list local notes",
        description="Add or list local notes stored outside Bible text.",
    )
    note_subparsers = note_parser.add_subparsers(dest="note_command")

    note_add_parser = note_subparsers.add_parser("add", help="add a note to a Bible reference")
    note_add_parser.add_argument("reference", help="reference to annotate, such as 'John 3:16'")
    note_add_parser.add_argument("text", nargs="+", help="note text")
    note_add_parser.set_defaults(func=note_add_command)

    note_list_parser = note_subparsers.add_parser("list", help="list notes")
    note_list_parser.set_defaults(func=note_list_command)
    note_parser.set_defaults(func=note_list_command)

    notes_parser = subparsers.add_parser(
        "notes",
        help="list local notes",
        description="List local notes stored outside Bible text.",
    )
    notes_parser.set_defaults(func=note_list_command)

    import_bundle_parser = subparsers.add_parser(
        "import-bundle",
        help="import a normalized JSON translation bundle into SQLite",
        description="Import a normalized JSON translation bundle into SQLite.",
    )
    import_bundle_parser.add_argument("source", help="path to a normalized translation bundle JSON file")
    import_bundle_parser.set_defaults(func=import_bundle_command)

    import_usfx_parser = subparsers.add_parser(
        "import-usfx",
        help="convert and import a local ASV USFX XML/zip source into SQLite",
        description="Convert and import a local ASV USFX XML file or eBible USFX zip into SQLite.",
    )
    import_usfx_parser.add_argument("source", help="path to a local ASV USFX XML file or eBible USFX zip")
    import_usfx_parser.set_defaults(func=import_usfx_command)

    init_db_parser = subparsers.add_parser(
        "init-db",
        help="create the default local Bible database",
        description="Create the default local SQLite Bible database from packaged sample data or a bundle.",
    )
    init_db_parser.add_argument(
        "--source",
        help="optional normalized translation bundle JSON file to import instead of packaged sample data",
    )
    init_db_parser.add_argument(
        "--usfx-source",
        help="optional local ASV USFX XML file or eBible USFX zip to convert/import",
    )
    init_db_parser.add_argument(
        "--force",
        action="store_true",
        help="replace the target database if it already exists",
    )
    init_db_parser.set_defaults(func=init_db_command)

    parser.set_defaults(func=show_placeholder)
    return parser


def show_placeholder(_args: argparse.Namespace) -> int:
    """Show a short placeholder until the full Bible import arrives."""
    print("bible-reader is installed with the ASV sample fixture.")
    print("Try: bible books")
    print("Try: bible John 3:16")
    print("Try: bible read John 3")
    print("Try: bible next John 3")
    print("Try: bible previous John 3")
    print("Try: bible search shepherd")
    print("Try: bible compare John 3:16")
    print("Try: bible doctor")
    print("Try: bible tui")
    print("Try: bible chapters John")
    print("Try: bible bookmark add John 3:16")
    print("Try: bible note add John 3:16 \"study note\"")
    print("Try: bible init-db")
    print("Try: bible import-usfx SOURCE.usfx-or-zip --db bible.sqlite3")
    return 0


def tui_plan_command(_args: argparse.Namespace) -> int:
    """Print the TUI foundation plan without launching an unfinished interface."""
    print(render_tui_plan())
    return 0




def doctor_command(args: argparse.Namespace) -> int:
    """Print lightweight runtime diagnostics for install checks."""
    options = getattr(args, "render_options", RenderOptions())
    default_db = default_database_path()
    if options.db_path is not None:
        db_label = str(options.db_path)
    elif default_db.exists():
        db_label = f"{default_db} (default local database)"
    else:
        db_label = f"sample fixture; default database not initialized at {default_db}"
    study_label = str(options.study_path or default_study_path())
    print("bible-reader doctor")
    print(f"version: {__version__}")
    print(f"command: {PROGRAM_NAME}")
    print(f"database: {db_label}")
    print(f"study file: {study_label}")
    print(f"theme: {options.theme}")
    print(f"width: {options.width or 'auto'}")
    print(f"color: {'on' if options.color else 'off'}")
    print("status: ok")
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


def show_chapters(args: argparse.Namespace) -> int:
    """Print chapters available for a book from the selected database."""
    options = getattr(args, "render_options", RenderOptions())
    raw_book = " ".join(args.book)
    try:
        from .references import normalize_book_name

        book_name = normalize_book_name(raw_book)
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    connection = _open_read_connection(options.db_path)
    try:
        repository = BibleRepository(connection)
        chapters = repository.list_chapters(book_name=book_name)
    finally:
        connection.close()

    if not chapters:
        location = "selected database" if options.db_path is not None else "ASV sample fixture"
        print(f"Book not found in the {location}: {book_name}", file=sys.stderr)
        return 1

    chapter_text = ", ".join(str(chapter) for chapter in chapters)
    print(f"{book_name} chapters: {chapter_text}")
    return 0


def render_verses(
    reference: BibleReference,
    verses: list[Verse],
    options: RenderOptions,
    *,
    translation: str = DEFAULT_TRANSLATION,
) -> None:
    """Render a passage using the CLI passage renderer."""
    renderer = PassageRenderer(color=options.color, theme=options.theme, width=options.width)
    print(renderer.render(reference, verses, translation=translation))


def _open_read_connection(db_path: Path | None):
    if db_path is None:
        if os.environ.get("BIBLE_READER_TEST_FORCE_SAMPLE") == "1":
            return create_sample_connection()
        default_db = default_database_path()
        if default_db.exists():
            connection = connect_database(default_db)
            initialize_database(connection)
            return connection
        return create_sample_connection()
    connection = connect_database(db_path)
    initialize_database(connection)
    return connection


def _lookup(
    reference: BibleReference,
    db_path: Path | None = None,
    *,
    translation_code: str = DEFAULT_TRANSLATION,
) -> list[Verse]:
    connection = _open_read_connection(db_path)
    try:
        repository = BibleRepository(connection)
        if reference.is_chapter:
            return repository.get_chapter(
                translation_code=translation_code,
                book_name=reference.book,
                chapter=reference.chapter,
            )
        return repository.get_verse_range(
            translation_code=translation_code,
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
        reference = _parse_chapter_reference(raw_reference, command="read")
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    return _read_chapter(reference, options, show_navigation=True)


def next_chapter_command(args: argparse.Namespace) -> int:
    """Read the next available chapter after a chapter reference."""
    options = getattr(args, "render_options", RenderOptions())
    raw_reference = " ".join(args.reference)
    try:
        reference = _parse_chapter_reference(raw_reference, command="next")
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    target = _adjacent_chapter(reference, options.db_path, direction="next")
    if target is None:
        print(f"No next chapter is available after {reference.label()}.", file=sys.stderr)
        return 1
    return _read_chapter(target, options, show_navigation=True)


def previous_chapter_command(args: argparse.Namespace) -> int:
    """Read the previous available chapter before a chapter reference."""
    options = getattr(args, "render_options", RenderOptions())
    raw_reference = " ".join(args.reference)
    try:
        reference = _parse_chapter_reference(raw_reference, command="previous")
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    target = _adjacent_chapter(reference, options.db_path, direction="previous")
    if target is None:
        print(f"No previous chapter is available before {reference.label()}.", file=sys.stderr)
        return 1
    return _read_chapter(target, options, show_navigation=True)


def _parse_chapter_reference(raw_reference: str, *, command: str) -> BibleReference:
    reference = parse_reference(raw_reference)
    if not reference.is_chapter:
        raise ReferenceParseError(f"{command} expects a chapter reference, such as 'John 3'.")
    return reference


def _adjacent_chapter(reference: BibleReference, db_path: Path | None, *, direction: str) -> BibleReference | None:
    connection = _open_read_connection(db_path)
    try:
        repository = BibleRepository(connection)
        adjacent = repository.adjacent_chapter(
            book_name=reference.book,
            chapter=reference.chapter,
            direction=direction,
        )
    finally:
        connection.close()

    if adjacent is None:
        return None
    book_name, chapter = adjacent
    return BibleReference(book=book_name, chapter=chapter)


def _read_chapter(reference: BibleReference, options: RenderOptions, *, show_navigation: bool) -> int:
    verses = _lookup(reference, options.db_path)
    if not verses:
        location = "selected database" if options.db_path is not None else "ASV sample fixture"
        print(f"Chapter not found in the {location}: {reference.label()}", file=sys.stderr)
        return 1

    render_verses(reference, verses, options)
    if show_navigation:
        hints = _navigation_hints(reference, options.db_path)
        if hints:
            print()
            print(hints)
    return 0


def _navigation_hints(reference: BibleReference, db_path: Path | None) -> str:
    previous_ref = _adjacent_chapter(reference, db_path, direction="previous")
    next_ref = _adjacent_chapter(reference, db_path, direction="next")
    parts: list[str] = []
    if previous_ref is not None:
        parts.append(f"Previous: bible read {previous_ref.label()}")
    if next_ref is not None:
        parts.append(f"Next: bible read {next_ref.label()}")
    return " | ".join(parts)


def compare_command(args: argparse.Namespace) -> int:
    """Compare a passage across translations in the selected database."""
    options = getattr(args, "render_options", RenderOptions())
    raw_reference = " ".join(args.reference)
    try:
        reference = parse_reference(raw_reference)
    except ReferenceParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    connection = _open_read_connection(options.db_path)
    try:
        repository = BibleRepository(connection)
        available_codes = [translation.code for translation in repository.list_translations()]
    finally:
        connection.close()

    requested_codes = _parse_requested_versions(args.versions, available_codes)
    if not requested_codes:
        print("Error: no translations are available to compare.", file=sys.stderr)
        return 1

    unknown_codes = [code for code in requested_codes if code not in available_codes]
    if unknown_codes:
        print("Error: unknown translation code(s): " + ", ".join(unknown_codes), file=sys.stderr)
        return 2

    passages = {
        code: _lookup(reference, options.db_path, translation_code=code)
        for code in requested_codes
    }
    if not any(passages.values()):
        location = "selected database" if options.db_path is not None else "ASV sample fixture"
        print(f"Reference not found in the {location}: {reference.label()}", file=sys.stderr)
        return 1

    renderer = ComparisonRenderer(color=options.color, theme=options.theme, width=options.width)
    print(renderer.render(reference, passages))
    return 0


def _parse_requested_versions(raw_versions: str | None, available_codes: list[str]) -> list[str]:
    """Return requested translation codes, preserving user order."""
    if raw_versions is None:
        return available_codes
    codes = [code.strip().upper() for code in raw_versions.split(",") if code.strip()]
    deduped: list[str] = []
    for code in codes:
        if code not in deduped:
            deduped.append(code)
    return deduped


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

    renderer = SearchRenderer(color=options.color, theme=options.theme, width=options.width)
    print(renderer.render(query, results, translation=DEFAULT_TRANSLATION))
    return 0 if results else 1


def _study_store(options: RenderOptions) -> StudyStore:
    return StudyStore(options.study_path)


def _normalize_reference_for_study(raw_reference: str) -> tuple[BibleReference | None, str | None]:
    try:
        reference = parse_reference(raw_reference)
    except ReferenceParseError as exc:
        return None, str(exc)
    return reference, None


def bookmark_add_command(args: argparse.Namespace) -> int:
    """Add a local bookmark."""
    options = getattr(args, "render_options", RenderOptions())
    raw_reference = " ".join(args.reference)
    reference, error = _normalize_reference_for_study(raw_reference)
    if error is not None or reference is None:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    try:
        bookmark = _study_store(options).add_bookmark(reference.label(), label=args.label)
    except StudyStoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    suffix = f" — {bookmark.label}" if bookmark.label else ""
    print(f"Bookmarked {bookmark.reference}{suffix}")
    return 0


def bookmark_list_command(args: argparse.Namespace) -> int:
    """List local bookmarks."""
    options = getattr(args, "render_options", RenderOptions())
    try:
        bookmarks = _study_store(options).list_bookmarks()
    except StudyStoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print("Bookmarks:")
    if not bookmarks:
        print("  No bookmarks yet.")
        return 0
    for index, bookmark in enumerate(bookmarks, start=1):
        suffix = f" — {bookmark.label}" if bookmark.label else ""
        print(f"{index:>2}. {bookmark.reference}{suffix}")
    return 0


def bookmark_remove_command(args: argparse.Namespace) -> int:
    """Remove a local bookmark."""
    options = getattr(args, "render_options", RenderOptions())
    raw_reference = " ".join(args.reference)
    reference, error = _normalize_reference_for_study(raw_reference)
    if error is not None or reference is None:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    try:
        removed = _study_store(options).remove_bookmark(reference.label())
    except StudyStoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if not removed:
        print(f"Bookmark not found: {reference.label()}", file=sys.stderr)
        return 1
    print(f"Removed bookmark: {reference.label()}")
    return 0


def note_add_command(args: argparse.Namespace) -> int:
    """Add a local note."""
    options = getattr(args, "render_options", RenderOptions())
    reference, error = _normalize_reference_for_study(args.reference)
    if error is not None or reference is None:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    text = " ".join(args.text).strip()
    if not text:
        print("Error: note text is required.", file=sys.stderr)
        return 2
    try:
        note = _study_store(options).add_note(reference.label(), text)
    except StudyStoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Added note for {note.reference}")
    return 0


def note_list_command(args: argparse.Namespace) -> int:
    """List local notes."""
    options = getattr(args, "render_options", RenderOptions())
    try:
        notes = _study_store(options).list_notes()
    except StudyStoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print("Notes:")
    if not notes:
        print("  No notes yet.")
        return 0
    for index, note in enumerate(notes, start=1):
        print(f"{index:>2}. {note.reference} — {note.text}")
    return 0



def init_db_command(args: argparse.Namespace) -> int:
    """Create the default or selected local Bible database."""
    options = getattr(args, "render_options", RenderOptions())
    target = options.db_path or default_database_path()
    try:
        if args.source and args.usfx_source:
            print("Error: choose either --source or --usfx-source, not both.", file=sys.stderr)
            return 2
        created_path = initialize_default_database(
            db_path=target,
            source_path=args.source,
            usfx_source_path=args.usfx_source,
            force=args.force,
        )
    except ImportErrorDetail as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.source:
        print(f"Initialized Bible database from {args.source}: {created_path}")
    elif args.usfx_source:
        print(f"Initialized Bible database from ASV USFX source {args.usfx_source}: {created_path}")
    else:
        print(f"Initialized Bible database from packaged ASV sample data: {created_path}")
    return 0

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
        bundle = convert_asv_source_to_bundle(args.source)
        summary = summarize_bundle(bundle)
        connection = connect_database(options.db_path)
        try:
            import_translation_bundle(connection, bundle)
        finally:
            connection.close()
    except ImportErrorDetail as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(
        f"Imported ASV USFX source into {options.db_path} "
        f"({summary['books']} books, {summary['verses']} verses)"
    )
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
    study_path: Path | None = None
    width: int | None = None
    index = 0
    while index < len(args_list):
        item = args_list[index]
        if item == "--no-color":
            color = False
            index += 1
            continue
        if item == "--theme":
            if index + 1 >= len(args_list):
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), "--theme requires a value."
            theme = args_list[index + 1]
            index += 2
            continue
        if item.startswith("--theme="):
            theme = item.split("=", 1)[1]
            index += 1
            continue
        if item == "--study":
            if index + 1 >= len(args_list):
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), "--study requires a value."
            study_path = Path(args_list[index + 1]).expanduser()
            index += 2
            continue
        if item.startswith("--study="):
            study_path = Path(item.split("=", 1)[1]).expanduser()
            index += 1
            continue
        if item == "--db":
            if index + 1 >= len(args_list):
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), "--db requires a value."
            db_path = Path(args_list[index + 1]).expanduser()
            index += 2
            continue
        if item.startswith("--db="):
            db_path = Path(item.split("=", 1)[1]).expanduser()
            index += 1
            continue
        if item == "--width":
            if index + 1 >= len(args_list):
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), "--width requires a value."
            try:
                width = int(args_list[index + 1])
            except ValueError:
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), "--width must be an integer."
            index += 2
            continue
        if item.startswith("--width="):
            try:
                width = int(item.split("=", 1)[1])
            except ValueError:
                return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), "--width must be an integer."
            index += 1
            continue
        cleaned.append(item)
        index += 1

    if theme not in THEMES:
        return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), (
            f"Unknown theme: {theme}. Choose one of: {', '.join(sorted(THEMES))}."
        )
    if width is not None and width < 20:
        return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), "--width must be 20 or greater."
    return cleaned, RenderOptions(color=color, theme=theme, db_path=db_path, study_path=study_path, width=width), None


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
