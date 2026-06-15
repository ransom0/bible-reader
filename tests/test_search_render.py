from __future__ import annotations

from bible_reader.render import SearchRenderer
from bible_reader.repository import BibleRepository
from bible_reader.storage import create_sample_connection


def test_search_renderer_outputs_reference_first_lines():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        results = repository.search_verses(translation_code="ASV", query="shepherd")
    finally:
        connection.close()

    output = SearchRenderer(color=False).render("shepherd", results, translation="ASV")

    assert "Search: shepherd (ASV)" in output
    assert "Showing 1 result." in output
    assert "Psalms 23:1" in output
    assert "  Jehovah is my shepherd; / I shall not want." in output
    assert "\033" not in output


def test_search_renderer_reports_no_matches():
    output = SearchRenderer(color=False).render("zzzz", [], translation="ASV")

    assert "Search: zzzz (ASV)" in output
    assert "No matches found." in output
    assert "Try a shorter phrase" in output


def test_search_renderer_wraps_under_reference():
    connection = create_sample_connection()
    try:
        repository = BibleRepository(connection)
        results = repository.search_verses(translation_code="ASV", query="world", book_name="John")
    finally:
        connection.close()

    output = SearchRenderer(color=False, width=44).render("world", results, translation="ASV")

    assert "Showing 2 results." in output
    assert "John 3:16" in output
    assert "  For God so loved the world," in output
    assert "  his only begotten Son" in output
