from __future__ import annotations

from pathlib import Path

import pytest

from bible_reader.asv_sources import asv_book_records, convert_usfx_asv_to_bundle
from bible_reader.importers import ImportErrorDetail, import_translation_bundle
from bible_reader.repository import BibleRepository
from bible_reader.storage import connect_database


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "asv_tiny.usfx"


def test_asv_book_records_include_full_canonical_protestant_canon():
    books = asv_book_records()

    assert len(books) == 66
    assert books[0] == {"id": 1, "name": "Genesis", "testament": "OT", "order": 1}
    assert books[18] == {"id": 19, "name": "Psalms", "testament": "OT", "order": 19}
    assert books[-1] == {"id": 66, "name": "Revelation", "testament": "NT", "order": 66}


def test_convert_usfx_asv_to_bundle_preserves_basic_verse_and_poetry_text():
    bundle = convert_usfx_asv_to_bundle(FIXTURE_PATH)

    assert bundle["translation"]["code"] == "ASV"
    assert len(bundle["books"]) == 66
    psalm = bundle["verses"][0]
    john = bundle["verses"][2]

    assert psalm["book"] == "Psalms"
    assert psalm["chapter"] == 23
    assert psalm["verse"] == 1
    assert psalm["paragraph_break_before"] is True
    assert psalm["text"] == "Jehovah is my shepherd;\nI shall not want."
    assert john["book"] == "John"
    assert john["verse"] == 16
    assert "For God so loved the world" in john["text"]


def test_converted_usfx_bundle_imports_into_repository():
    bundle = convert_usfx_asv_to_bundle(FIXTURE_PATH)
    connection = connect_database()
    try:
        import_translation_bundle(connection, bundle)
        repository = BibleRepository(connection)
        verse = repository.get_verse(
            translation_code="ASV",
            book_name="John",
            chapter=3,
            verse=16,
        )
        psalm = repository.get_verse(
            translation_code="ASV",
            book_name="Psalms",
            chapter=23,
            verse=1,
        )
    finally:
        connection.close()

    assert verse is not None
    assert "For God so loved the world" in verse.text
    assert psalm is not None
    assert "\nI shall not want." in psalm.text


def test_convert_usfx_rejects_unknown_book_code(tmp_path: Path):
    source = tmp_path / "bad.usfx"
    source.write_text('<usfx><book id="XYZ" /><c id="1" /><v id="1" />Text.</usfx>', encoding="utf-8")

    with pytest.raises(ImportErrorDetail, match="Unsupported USFX book code"):
        convert_usfx_asv_to_bundle(source)
