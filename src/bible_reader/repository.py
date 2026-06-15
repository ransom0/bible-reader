"""Repository layer for Bible text stored in SQLite."""

from __future__ import annotations

import sqlite3

from .models import Book, Translation, Verse


class BibleRepository:
    """Read Bible metadata and verses from a SQLite database."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_translations(self) -> list[Translation]:
        """Return available translations sorted by code."""
        rows = self._connection.execute(
            """
            SELECT code, name, language, copyright
            FROM translations
            ORDER BY code
            """
        ).fetchall()
        return [
            Translation(
                code=row["code"],
                name=row["name"],
                language=row["language"],
                copyright=row["copyright"],
            )
            for row in rows
        ]

    def list_books(self) -> list[Book]:
        """Return canonical books sorted by canonical order."""
        rows = self._connection.execute(
            """
            SELECT id, name, testament, book_order
            FROM books
            ORDER BY book_order
            """
        ).fetchall()
        return [
            Book(
                id=row["id"],
                name=row["name"],
                testament=row["testament"],
                order=row["book_order"],
            )
            for row in rows
        ]

    def get_verse(
        self,
        *,
        translation_code: str,
        book_name: str,
        chapter: int,
        verse: int,
    ) -> Verse | None:
        """Return one verse by reference, or None when it is not present."""
        row = self._connection.execute(
            """
            SELECT v.translation_code, b.name AS book_name, v.chapter, v.verse, v.text, v.paragraph_break_before
            FROM verses AS v
            JOIN books AS b ON b.id = v.book_id
            WHERE v.translation_code = ?
              AND b.name = ?
              AND v.chapter = ?
              AND v.verse = ?
            """,
            (translation_code, book_name, chapter, verse),
        ).fetchone()
        if row is None:
            return None
        return Verse(
            translation=row["translation_code"],
            book=row["book_name"],
            chapter=row["chapter"],
            verse=row["verse"],
            text=row["text"],
            paragraph_break_before=bool(row["paragraph_break_before"]),
        )

    def get_verse_range(
        self,
        *,
        translation_code: str,
        book_name: str,
        chapter: int,
        start_verse: int,
        end_verse: int,
    ) -> list[Verse]:
        """Return verses in an inclusive range sorted by verse number."""
        rows = self._connection.execute(
            """
            SELECT v.translation_code, b.name AS book_name, v.chapter, v.verse, v.text, v.paragraph_break_before
            FROM verses AS v
            JOIN books AS b ON b.id = v.book_id
            WHERE v.translation_code = ?
              AND b.name = ?
              AND v.chapter = ?
              AND v.verse BETWEEN ? AND ?
            ORDER BY v.verse
            """,
            (translation_code, book_name, chapter, start_verse, end_verse),
        ).fetchall()
        return [
            Verse(
                translation=row["translation_code"],
                book=row["book_name"],
                chapter=row["chapter"],
                verse=row["verse"],
                text=row["text"],
                paragraph_break_before=bool(row["paragraph_break_before"]),
            )
            for row in rows
        ]

    def get_chapter(
        self,
        *,
        translation_code: str,
        book_name: str,
        chapter: int,
    ) -> list[Verse]:
        """Return all fixture verses for a chapter sorted by verse number."""
        rows = self._connection.execute(
            """
            SELECT v.translation_code, b.name AS book_name, v.chapter, v.verse, v.text, v.paragraph_break_before
            FROM verses AS v
            JOIN books AS b ON b.id = v.book_id
            WHERE v.translation_code = ?
              AND b.name = ?
              AND v.chapter = ?
            ORDER BY v.verse
            """,
            (translation_code, book_name, chapter),
        ).fetchall()
        return [
            Verse(
                translation=row["translation_code"],
                book=row["book_name"],
                chapter=row["chapter"],
                verse=row["verse"],
                text=row["text"],
                paragraph_break_before=bool(row["paragraph_break_before"]),
            )
            for row in rows
        ]
