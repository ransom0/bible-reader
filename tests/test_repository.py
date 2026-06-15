from __future__ import annotations

from bible_reader.repository import BibleRepository
from bible_reader.storage import create_sample_connection


def test_sample_fixture_has_asv_translation():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        translations = repository.list_translations()
    finally:
        connection.close()

    assert [translation.code for translation in translations] == ["ASV"]
    assert translations[0].name == "American Standard Version"


def test_sample_fixture_lists_books_in_order():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        books = repository.list_books()
    finally:
        connection.close()

    assert [book.name for book in books] == ["John", "Romans"]
    assert [book.order for book in books] == [43, 45]


def test_repository_gets_single_verse_with_parameterized_lookup():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        verse = repository.get_verse(
            translation_code="ASV",
            book_name="John",
            chapter=3,
            verse=16,
        )
    finally:
        connection.close()

    assert verse is not None
    assert verse.book == "John"
    assert verse.chapter == 3
    assert verse.verse == 16
    assert "For God so loved the world" in verse.text


def test_repository_returns_none_for_missing_verse():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        verse = repository.get_verse(
            translation_code="ASV",
            book_name="John",
            chapter=99,
            verse=1,
        )
    finally:
        connection.close()

    assert verse is None


def test_repository_gets_chapter_verses_in_order():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        verses = repository.get_chapter(
            translation_code="ASV",
            book_name="Romans",
            chapter=8,
        )
    finally:
        connection.close()

    assert [verse.verse for verse in verses] == [28, 29, 30]


def test_repository_gets_verse_range_with_parameterized_lookup():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        verses = repository.get_verse_range(
            translation_code="ASV",
            book_name="Romans",
            chapter=8,
            start_verse=28,
            end_verse=30,
        )
    finally:
        connection.close()

    assert [verse.verse for verse in verses] == [28, 29, 30]
    assert "work together for good" in verses[0].text
