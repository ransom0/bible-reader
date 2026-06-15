from __future__ import annotations

from bible_reader.repository import BibleRepository
from bible_reader.storage import create_sample_connection


def test_repository_search_matches_phrase_case_insensitive():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        results = repository.search_verses(translation_code="ASV", query="GOOD")
    finally:
        connection.close()

    assert [result.reference_label for result in results] == ["Romans 8:28"]
    assert "work together for good" in results[0].verse.text


def test_repository_search_can_limit_by_book():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        results = repository.search_verses(
            translation_code="ASV",
            query="world",
            book_name="John",
            limit=10,
        )
    finally:
        connection.close()

    assert [result.reference_label for result in results] == ["John 3:16", "John 3:17"]


def test_repository_search_respects_limit():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        results = repository.search_verses(translation_code="ASV", query="he", limit=2)
    finally:
        connection.close()

    assert len(results) == 2


def test_repository_search_empty_query_returns_no_results():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        results = repository.search_verses(translation_code="ASV", query="   ")
    finally:
        connection.close()

    assert results == []
