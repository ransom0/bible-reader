"""Repository layer for Bible text stored in SQLite."""

from __future__ import annotations

import sqlite3

from .models import Book, Translation, Verse
from .search import SearchResult


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


    def list_chapters(self, *, book_name: str) -> list[int]:
        """Return chapter numbers available for a book in canonical order."""
        rows = self._connection.execute(
            """
            SELECT DISTINCT v.chapter
            FROM verses AS v
            JOIN books AS b ON b.id = v.book_id
            WHERE b.name = ?
            ORDER BY v.chapter
            """,
            (book_name,),
        ).fetchall()
        return [int(row["chapter"]) for row in rows]

    def chapter_exists(self, *, book_name: str, chapter: int) -> bool:
        """Return True when at least one verse exists for a chapter."""
        row = self._connection.execute(
            """
            SELECT 1
            FROM verses AS v
            JOIN books AS b ON b.id = v.book_id
            WHERE b.name = ?
              AND v.chapter = ?
            LIMIT 1
            """,
            (book_name, chapter),
        ).fetchone()
        return row is not None


    def adjacent_chapter(
        self,
        *,
        book_name: str,
        chapter: int,
        direction: str,
    ) -> tuple[str, int] | None:
        """Return the previous or next available chapter in canonical order.

        ``direction`` must be ``"previous"`` or ``"next"``. The lookup is
        based on chapters that actually exist in the selected database, so it
        works with both the tiny fixture and a full imported ASV database.
        """
        if direction not in {"previous", "next"}:
            raise ValueError("direction must be 'previous' or 'next'")

        rows = self._connection.execute(
            """
            SELECT b.name AS book_name, v.chapter
            FROM verses AS v
            JOIN books AS b ON b.id = v.book_id
            GROUP BY b.id, b.name, b.book_order, v.chapter
            ORDER BY b.book_order, v.chapter
            """
        ).fetchall()
        chapters = [(row["book_name"], int(row["chapter"])) for row in rows]
        try:
            index = chapters.index((book_name, chapter))
        except ValueError:
            return None

        target_index = index - 1 if direction == "previous" else index + 1
        if target_index < 0 or target_index >= len(chapters):
            return None
        return chapters[target_index]

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

    def search_verses(
        self,
        *,
        translation_code: str,
        query: str,
        book_name: str | None = None,
        limit: int = 25,
    ) -> list[SearchResult]:
        """Return verses matching a case-insensitive phrase query.

        The query is bound as a SQLite parameter; user search text is never
        interpolated into SQL. This keeps the first search implementation
        boring, safe, and adequate until a later FTS-backed pass.
        """
        normalized_query = " ".join(query.split())
        if not normalized_query:
            return []
        if limit < 1:
            return []

        like_query = f"%{normalized_query}%"
        params: list[object] = [translation_code, like_query]
        book_clause = ""
        if book_name is not None:
            book_clause = " AND b.name = ?"
            params.append(book_name)
        params.append(limit)

        rows = self._connection.execute(
            f"""
            SELECT v.translation_code, b.name AS book_name, v.chapter, v.verse, v.text, v.paragraph_break_before
            FROM verses AS v
            JOIN books AS b ON b.id = v.book_id
            WHERE v.translation_code = ?
              AND v.text LIKE ? COLLATE NOCASE
              {book_clause}
            ORDER BY b.book_order, v.chapter, v.verse
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [
            SearchResult(
                verse=Verse(
                    translation=row["translation_code"],
                    book=row["book_name"],
                    chapter=row["chapter"],
                    verse=row["verse"],
                    text=row["text"],
                    paragraph_break_before=bool(row["paragraph_break_before"]),
                ),
                query=normalized_query,
            )
            for row in rows
        ]
