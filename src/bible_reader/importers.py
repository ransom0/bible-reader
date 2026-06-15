"""Import helpers for Bible translation source bundles."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .storage import initialize_database


class ImportErrorDetail(ValueError):
    """Raised when a translation bundle cannot be imported safely."""


@dataclass(frozen=True, slots=True)
class VerseImportRecord:
    """A normalized verse record ready for insertion into SQLite."""

    translation_code: str
    book_id: int
    chapter: int
    verse: int
    text: str
    paragraph_break_before: bool = False


REQUIRED_TRANSLATION_KEYS = {"code", "name", "language", "copyright"}
REQUIRED_BOOK_KEYS = {"id", "name", "testament", "order"}
REQUIRED_VERSE_KEYS = {"book", "chapter", "verse", "text"}
VALID_TESTAMENTS = {"OT", "NT"}


def load_translation_bundle(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate a JSON translation bundle from disk."""
    bundle_path = Path(path)
    try:
        with bundle_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ImportErrorDetail(f"Invalid JSON in translation bundle: {bundle_path}") from exc
    except OSError as exc:
        raise ImportErrorDetail(f"Could not read translation bundle: {bundle_path}") from exc

    if not isinstance(raw, dict):
        raise ImportErrorDetail("Translation bundle must be a JSON object.")
    validate_translation_bundle(raw)
    return raw


def validate_translation_bundle(bundle: Mapping[str, Any]) -> None:
    """Validate the import bundle shape before any database writes happen."""
    translation = bundle.get("translation")
    books = bundle.get("books")
    verses = bundle.get("verses")

    if not isinstance(translation, dict):
        raise ImportErrorDetail("Bundle must contain a translation object.")
    missing_translation = REQUIRED_TRANSLATION_KEYS - set(translation)
    if missing_translation:
        raise ImportErrorDetail(
            "Translation is missing required keys: " + ", ".join(sorted(missing_translation))
        )

    code = str(translation["code"]).strip()
    if not code:
        raise ImportErrorDetail("Translation code must not be blank.")

    if not isinstance(books, list) or not books:
        raise ImportErrorDetail("Bundle must contain a non-empty books list.")
    if not isinstance(verses, list) or not verses:
        raise ImportErrorDetail("Bundle must contain a non-empty verses list.")

    seen_book_ids: set[int] = set()
    seen_book_names: set[str] = set()
    for book in books:
        if not isinstance(book, dict):
            raise ImportErrorDetail("Each book must be an object.")
        missing_book = REQUIRED_BOOK_KEYS - set(book)
        if missing_book:
            raise ImportErrorDetail("Book is missing required keys: " + ", ".join(sorted(missing_book)))

        book_id = _positive_int(book["id"], "book id")
        order = _positive_int(book["order"], "book order")
        name = str(book["name"]).strip()
        testament = str(book["testament"]).strip().upper()
        if not name:
            raise ImportErrorDetail("Book name must not be blank.")
        if testament not in VALID_TESTAMENTS:
            raise ImportErrorDetail(f"Book {name!r} has invalid testament: {testament!r}.")
        if book_id in seen_book_ids:
            raise ImportErrorDetail(f"Duplicate book id: {book_id}.")
        if name in seen_book_names:
            raise ImportErrorDetail(f"Duplicate book name: {name}.")
        seen_book_ids.add(book_id)
        seen_book_names.add(name)
        _positive_int(order, "book order")

    if len(seen_book_ids) != len(books):
        raise ImportErrorDetail("Book ids must be unique.")

    seen_references: set[tuple[str, int, int]] = set()
    for verse in verses:
        if not isinstance(verse, dict):
            raise ImportErrorDetail("Each verse must be an object.")
        missing_verse = REQUIRED_VERSE_KEYS - set(verse)
        if missing_verse:
            raise ImportErrorDetail("Verse is missing required keys: " + ", ".join(sorted(missing_verse)))

        book_name = str(verse["book"]).strip()
        if book_name not in seen_book_names:
            raise ImportErrorDetail(f"Verse references unknown book: {book_name}.")
        chapter = _positive_int(verse["chapter"], "chapter")
        verse_number = _positive_int(verse["verse"], "verse")
        text = str(verse["text"]).strip()
        if not text:
            raise ImportErrorDetail(f"Verse text must not be blank: {book_name} {chapter}:{verse_number}.")
        reference_key = (book_name, chapter, verse_number)
        if reference_key in seen_references:
            raise ImportErrorDetail(f"Duplicate verse reference: {book_name} {chapter}:{verse_number}.")
        seen_references.add(reference_key)


def import_translation_bundle(connection: sqlite3.Connection, bundle: Mapping[str, Any]) -> None:
    """Import a validated translation bundle into the application database."""
    validate_translation_bundle(bundle)
    initialize_database(connection)

    translation = bundle["translation"]
    books = bundle["books"]
    verses = bundle["verses"]
    code = str(translation["code"]).strip()

    with connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO translations (code, name, language, copyright)
            VALUES (?, ?, ?, ?)
            """,
            (
                code,
                str(translation["name"]).strip(),
                str(translation["language"]).strip(),
                str(translation["copyright"]).strip(),
            ),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO books (id, name, testament, book_order)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    _positive_int(book["id"], "book id"),
                    str(book["name"]).strip(),
                    str(book["testament"]).strip().upper(),
                    _positive_int(book["order"], "book order"),
                )
                for book in books
            ],
        )

        book_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM books").fetchall()
        }
        connection.executemany(
            """
            INSERT OR REPLACE INTO verses
                (translation_code, book_id, chapter, verse, text, paragraph_break_before)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    code,
                    book_ids[str(verse["book"]).strip()],
                    _positive_int(verse["chapter"], "chapter"),
                    _positive_int(verse["verse"], "verse"),
                    str(verse["text"]).strip(),
                    1 if bool(verse.get("paragraph_break_before", False)) else 0,
                )
                for verse in verses
            ],
        )


def _positive_int(value: Any, field_name: str) -> int:
    """Return a positive integer or raise a clear import validation error."""
    if isinstance(value, bool):
        raise ImportErrorDetail(f"{field_name} must be a positive integer.")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ImportErrorDetail(f"{field_name} must be a positive integer.") from exc
    if number <= 0:
        raise ImportErrorDetail(f"{field_name} must be a positive integer.")
    return number
