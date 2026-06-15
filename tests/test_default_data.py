from __future__ import annotations

import json
from pathlib import Path

import pytest

from bible_reader.importers import ImportErrorDetail
from bible_reader.default_data import initialize_default_database, load_packaged_sample_bundle
from bible_reader.repository import BibleRepository
from bible_reader.storage import connect_database


def test_load_packaged_sample_bundle_contains_current_fixture_books():
    bundle = load_packaged_sample_bundle()

    assert bundle["translation"]["code"] == "ASV"
    assert [book["name"] for book in bundle["books"]] == ["Psalms", "John", "Romans"]
    assert any(verse["book"] == "Romans" for verse in bundle["verses"])


def test_initialize_default_database_imports_packaged_sample(tmp_path):
    db_path = tmp_path / "data" / "bible-reader.sqlite3"

    created_path = initialize_default_database(db_path=db_path)

    assert created_path == db_path
    assert db_path.exists()

    connection = connect_database(db_path)
    try:
        repository = BibleRepository(connection)
        books = repository.list_books()
        verses = repository.get_verse_range(
            translation_code="ASV",
            book_name="Romans",
            chapter=8,
            start_verse=28,
            end_verse=30,
        )
    finally:
        connection.close()

    assert [book.name for book in books] == ["Psalms", "John", "Romans"]
    assert [verse.verse for verse in verses] == [28, 29, 30]


def test_initialize_default_database_rejects_existing_without_force(tmp_path):
    db_path = tmp_path / "bible.sqlite3"
    initialize_default_database(db_path=db_path)

    try:
        initialize_default_database(db_path=db_path)
    except ImportErrorDetail as exc:
        assert "Use --force" in str(exc)
    else:
        raise AssertionError("Expected existing DB to require --force")


def test_initialize_default_database_can_import_explicit_bundle(tmp_path):
    source = tmp_path / "bundle.json"
    source.write_text(
        json.dumps(
            {
                "translation": {
                    "code": "ASV",
                    "name": "American Standard Version",
                    "language": "en",
                    "copyright": "Public domain: ASV 1901",
                },
                "books": [
                    {"id": 43, "name": "John", "testament": "NT", "order": 43},
                ],
                "verses": [
                    {
                        "book": "John",
                        "chapter": 1,
                        "verse": 1,
                        "text": "In the beginning was the Word.",
                        "paragraph_break_before": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    db_path = tmp_path / "custom.sqlite3"

    initialize_default_database(db_path=db_path, source_path=source)

    connection = connect_database(db_path)
    try:
        verse = BibleRepository(connection).get_verse(
            translation_code="ASV",
            book_name="John",
            chapter=1,
            verse=1,
        )
    finally:
        connection.close()

    assert verse is not None
    assert verse.text == "In the beginning was the Word."


def test_initialize_default_database_can_import_usfx_source(tmp_path):
    db_path = tmp_path / "bible.sqlite3"
    source_path = Path("tests/fixtures/asv_tiny.usfx")

    created = initialize_default_database(
        db_path=db_path,
        usfx_source_path=source_path,
        force=True,
    )

    assert created == db_path
    connection = connect_database(db_path)
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
    assert "For God so loved the world" in verse.text


def test_initialize_default_database_rejects_two_source_modes(tmp_path):
    with pytest.raises(ImportErrorDetail, match="either source_path or usfx_source_path"):
        initialize_default_database(
            db_path=tmp_path / "bible.sqlite3",
            source_path="tests/fixtures/asv_sample_bundle.json",
            usfx_source_path="tests/fixtures/asv_tiny.usfx",
            force=True,
        )
