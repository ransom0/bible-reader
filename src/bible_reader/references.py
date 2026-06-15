"""Bible reference parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re


class ReferenceParseError(ValueError):
    """Raised when user input cannot be parsed as a Bible reference."""


@dataclass(frozen=True, slots=True)
class BibleReference:
    """A normalized Bible reference.

    ``start_verse`` and ``end_verse`` are ``None`` for whole-chapter references.
    """

    book: str
    chapter: int
    start_verse: int | None = None
    end_verse: int | None = None

    @property
    def is_chapter(self) -> bool:
        """Return True when this reference points to a whole chapter."""
        return self.start_verse is None

    def label(self) -> str:
        """Return a human-readable normalized label."""
        if self.start_verse is None:
            return f"{self.book} {self.chapter}"
        if self.end_verse is None or self.end_verse == self.start_verse:
            return f"{self.book} {self.chapter}:{self.start_verse}"
        return f"{self.book} {self.chapter}:{self.start_verse}-{self.end_verse}"


_BOOK_ALIASES = {
    "psalms": "Psalms",
    "psalm": "Psalms",
    "ps": "Psalms",
    "psa": "Psalms",
    "john": "John",
    "jn": "John",
    "jhn": "John",
    "romans": "Romans",
    "roman": "Romans",
    "rom": "Romans",
    "ro": "Romans",
    "1 corinthians": "1 Corinthians",
    "1 corinthian": "1 Corinthians",
    "1 cor": "1 Corinthians",
    "1 co": "1 Corinthians",
    "i corinthians": "1 Corinthians",
    "i cor": "1 Corinthians",
    "first corinthians": "1 Corinthians",
    "first cor": "1 Corinthians",
}

_REFERENCE_PATTERN = re.compile(
    r"^\s*(?P<book>[1-3]?\s*[A-Za-z][A-Za-z .]*?)\s+"
    r"(?P<chapter>\d+)"
    r"(?:\s*:\s*(?P<start_verse>\d+)"
    r"(?:\s*-\s*(?P<end_verse>\d+))?"
    r")?\s*$"
)


def normalize_book_name(raw_book: str) -> str:
    """Return the canonical book name for a supported book alias."""
    compact = " ".join(raw_book.lower().replace(".", " ").split())
    compact = re.sub(r"^(\d)([a-z])", r"\1 \2", compact)
    if compact in _BOOK_ALIASES:
        return _BOOK_ALIASES[compact]
    title = " ".join(part.capitalize() for part in compact.split())
    if title:
        return title
    raise ReferenceParseError("Book name is required.")


def parse_reference(raw_reference: str) -> BibleReference:
    """Parse a user-entered Bible reference.

    Supported forms include ``John 3``, ``John 3:16``, ``Romans 8:28-30``,
    ``Jn 3:16``, ``Rom 8``, ``Ps 23``, and ``1 Cor 13``.
    """
    text = " ".join(raw_reference.strip().split())
    if not text:
        raise ReferenceParseError("Reference is required.")

    match = _REFERENCE_PATTERN.match(text)
    if match is None:
        raise ReferenceParseError(
            "Could not parse reference. Try forms like 'John 3:16', 'John 3', or 'Romans 8:28-30'."
        )

    book = normalize_book_name(match.group("book"))
    chapter = int(match.group("chapter"))
    start_verse_text = match.group("start_verse")
    end_verse_text = match.group("end_verse")

    if chapter < 1:
        raise ReferenceParseError("Chapter must be 1 or greater.")

    if start_verse_text is None:
        return BibleReference(book=book, chapter=chapter)

    start_verse = int(start_verse_text)
    end_verse = int(end_verse_text) if end_verse_text is not None else start_verse
    if start_verse < 1:
        raise ReferenceParseError("Verse must be 1 or greater.")
    if end_verse < start_verse:
        raise ReferenceParseError("Verse range must end at or after the starting verse.")

    return BibleReference(
        book=book,
        chapter=chapter,
        start_verse=start_verse,
        end_verse=end_verse,
    )
