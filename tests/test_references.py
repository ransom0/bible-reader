from __future__ import annotations

import pytest

from bible_reader.references import ReferenceParseError, parse_reference


def test_parse_single_verse_reference():
    reference = parse_reference("John 3:16")

    assert reference.book == "John"
    assert reference.chapter == 3
    assert reference.start_verse == 16
    assert reference.end_verse == 16
    assert reference.label() == "John 3:16"


def test_parse_chapter_reference():
    reference = parse_reference("John 3")

    assert reference.book == "John"
    assert reference.chapter == 3
    assert reference.is_chapter is True
    assert reference.label() == "John 3"


def test_parse_verse_range_reference():
    reference = parse_reference("Romans 8:28-30")

    assert reference.book == "Romans"
    assert reference.chapter == 8
    assert reference.start_verse == 28
    assert reference.end_verse == 30
    assert reference.label() == "Romans 8:28-30"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Jn 3:16", "John 3:16"),
        ("Rom 8", "Romans 8"),
        ("1 Cor 13", "1 Corinthians 13"),
        ("I Cor 13", "1 Corinthians 13"),
    ],
)
def test_parse_common_book_aliases(raw, expected):
    assert parse_reference(raw).label() == expected


def test_parse_rejects_reversed_ranges():
    with pytest.raises(ReferenceParseError, match="end at or after"):
        parse_reference("Romans 8:30-28")


def test_parse_rejects_bad_input():
    with pytest.raises(ReferenceParseError, match="Could not parse"):
        parse_reference("not a reference")
