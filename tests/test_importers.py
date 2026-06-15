from __future__ import annotations

from pathlib import Path

import pytest

from bible_reader.importers import (
    ImportErrorDetail,
    import_translation_bundle,
    load_translation_bundle,
    validate_translation_bundle,
)
from bible_reader.repository import BibleRepository
from bible_reader.storage import connect_database


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "asv_sample_bundle.json"


def test_load_translation_bundle_reads_valid_json_fixture():
    bundle = load_translation_bundle(FIXTURE_PATH)

    assert bundle["translation"]["code"] == "ASV"
    assert bundle["books"][0]["name"] == "Psalms"


def test_import_translation_bundle_loads_translation_books_and_verses():
    bundle = load_translation_bundle(FIXTURE_PATH)
    connection = connect_database()
    try:
        import_translation_bundle(connection, bundle)
        repository = BibleRepository(connection)

        translations = repository.list_translations()
        books = repository.list_books()
        verse = repository.get_verse(
            translation_code="ASV",
            book_name="John",
            chapter=3,
            verse=16,
        )

        assert [translation.code for translation in translations] == ["ASV"]
        assert [book.name for book in books] == ["Psalms", "John"]
        assert verse is not None
        assert verse.paragraph_break_before is True
        assert "For God so loved the world" in verse.text
    finally:
        connection.close()


def test_validate_translation_bundle_rejects_missing_translation_keys():
    bundle = load_translation_bundle(FIXTURE_PATH)
    del bundle["translation"]["copyright"]

    with pytest.raises(ImportErrorDetail, match="copyright"):
        validate_translation_bundle(bundle)


def test_validate_translation_bundle_rejects_unknown_book_reference():
    bundle = load_translation_bundle(FIXTURE_PATH)
    bundle["verses"][0]["book"] = "Tobit"

    with pytest.raises(ImportErrorDetail, match="unknown book"):
        validate_translation_bundle(bundle)


def test_validate_translation_bundle_rejects_duplicate_verse_reference():
    bundle = load_translation_bundle(FIXTURE_PATH)
    bundle["verses"].append(dict(bundle["verses"][0]))

    with pytest.raises(ImportErrorDetail, match="Duplicate verse reference"):
        validate_translation_bundle(bundle)
