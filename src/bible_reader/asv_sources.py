"""ASV source-file converters.

The app imports normalized JSON bundles into SQLite. This module converts
public-domain ASV source files into that internal bundle shape without executing
or trusting downloaded data as code.
"""

from __future__ import annotations

from io import BytesIO
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from .importers import ImportErrorDetail, validate_translation_bundle


ASV_TRANSLATION = {
    "code": "ASV",
    "name": "American Standard Version",
    "language": "en",
    "copyright": "Public domain: ASV 1901",
}

CANONICAL_BOOKS: tuple[tuple[str, int, str, str, int], ...] = (
    ("GEN", 1, "Genesis", "OT", 1),
    ("EXO", 2, "Exodus", "OT", 2),
    ("LEV", 3, "Leviticus", "OT", 3),
    ("NUM", 4, "Numbers", "OT", 4),
    ("DEU", 5, "Deuteronomy", "OT", 5),
    ("JOS", 6, "Joshua", "OT", 6),
    ("JDG", 7, "Judges", "OT", 7),
    ("RUT", 8, "Ruth", "OT", 8),
    ("1SA", 9, "1 Samuel", "OT", 9),
    ("2SA", 10, "2 Samuel", "OT", 10),
    ("1KI", 11, "1 Kings", "OT", 11),
    ("2KI", 12, "2 Kings", "OT", 12),
    ("1CH", 13, "1 Chronicles", "OT", 13),
    ("2CH", 14, "2 Chronicles", "OT", 14),
    ("EZR", 15, "Ezra", "OT", 15),
    ("NEH", 16, "Nehemiah", "OT", 16),
    ("EST", 17, "Esther", "OT", 17),
    ("JOB", 18, "Job", "OT", 18),
    ("PSA", 19, "Psalms", "OT", 19),
    ("PRO", 20, "Proverbs", "OT", 20),
    ("ECC", 21, "Ecclesiastes", "OT", 21),
    ("SNG", 22, "Song of Solomon", "OT", 22),
    ("ISA", 23, "Isaiah", "OT", 23),
    ("JER", 24, "Jeremiah", "OT", 24),
    ("LAM", 25, "Lamentations", "OT", 25),
    ("EZK", 26, "Ezekiel", "OT", 26),
    ("DAN", 27, "Daniel", "OT", 27),
    ("HOS", 28, "Hosea", "OT", 28),
    ("JOL", 29, "Joel", "OT", 29),
    ("AMO", 30, "Amos", "OT", 30),
    ("OBA", 31, "Obadiah", "OT", 31),
    ("JON", 32, "Jonah", "OT", 32),
    ("MIC", 33, "Micah", "OT", 33),
    ("NAM", 34, "Nahum", "OT", 34),
    ("HAB", 35, "Habakkuk", "OT", 35),
    ("ZEP", 36, "Zephaniah", "OT", 36),
    ("HAG", 37, "Haggai", "OT", 37),
    ("ZEC", 38, "Zechariah", "OT", 38),
    ("MAL", 39, "Malachi", "OT", 39),
    ("MAT", 40, "Matthew", "NT", 40),
    ("MRK", 41, "Mark", "NT", 41),
    ("LUK", 42, "Luke", "NT", 42),
    ("JHN", 43, "John", "NT", 43),
    ("ACT", 44, "Acts", "NT", 44),
    ("ROM", 45, "Romans", "NT", 45),
    ("1CO", 46, "1 Corinthians", "NT", 46),
    ("2CO", 47, "2 Corinthians", "NT", 47),
    ("GAL", 48, "Galatians", "NT", 48),
    ("EPH", 49, "Ephesians", "NT", 49),
    ("PHP", 50, "Philippians", "NT", 50),
    ("COL", 51, "Colossians", "NT", 51),
    ("1TH", 52, "1 Thessalonians", "NT", 52),
    ("2TH", 53, "2 Thessalonians", "NT", 53),
    ("1TI", 54, "1 Timothy", "NT", 54),
    ("2TI", 55, "2 Timothy", "NT", 55),
    ("TIT", 56, "Titus", "NT", 56),
    ("PHM", 57, "Philemon", "NT", 57),
    ("HEB", 58, "Hebrews", "NT", 58),
    ("JAS", 59, "James", "NT", 59),
    ("1PE", 60, "1 Peter", "NT", 60),
    ("2PE", 61, "2 Peter", "NT", 61),
    ("1JN", 62, "1 John", "NT", 62),
    ("2JN", 63, "2 John", "NT", 63),
    ("3JN", 64, "3 John", "NT", 64),
    ("JUD", 65, "Jude", "NT", 65),
    ("REV", 66, "Revelation", "NT", 66),
)

BOOK_BY_USFM = {code: (book_id, name, testament, order) for code, book_id, name, testament, order in CANONICAL_BOOKS}
IGNORED_USFX_BOOK_CODES = {"FRT", "INT", "BAK", "OTH", "GLO", "TDX", "NDX", "XXA"}
POETRY_BOOKS = {"Job", "Psalms", "Proverbs", "Song of Solomon", "Lamentations"}


def asv_book_records() -> list[dict[str, Any]]:
    """Return canonical book records for the ASV import bundle."""
    return [
        {"id": book_id, "name": name, "testament": testament, "order": order}
        for _code, book_id, name, testament, order in CANONICAL_BOOKS
    ]


def convert_asv_source_to_bundle(path: str | Path) -> dict[str, Any]:
    """Convert a local ASV USFX XML file or eBible USFX zip into a bundle.

    This helper keeps the full-ASV import path local/offline. It reads data as
    XML/text only, never executes imported content, and accepts the common
    eBible ``eng-asv_usfx.zip`` distribution without requiring the user to unzip
    it by hand.
    """
    source_path = Path(path).expanduser()
    if source_path.suffix.lower() == ".zip":
        root = _parse_usfx_zip(source_path)
    else:
        root = _parse_usfx_xml_file(source_path)
    return _convert_usfx_root_to_bundle(root)


def convert_usfx_asv_to_bundle(path: str | Path) -> dict[str, Any]:
    """Convert an ASV USFX XML source file into the internal bundle shape.

    Kept as a compatibility alias for the original Stage 6 command/tests. New
    code should call :func:`convert_asv_source_to_bundle`, which also supports
    eBible USFX zip archives.
    """
    return convert_asv_source_to_bundle(path)


def summarize_bundle(bundle: dict[str, Any]) -> dict[str, int | str]:
    """Return a small summary for import success messages and smoke tests."""
    validate_translation_bundle(bundle)
    verses = bundle["verses"]
    books_with_verses = {str(verse["book"]) for verse in verses}
    return {
        "translation": str(bundle["translation"]["code"]),
        "books": len(books_with_verses),
        "verses": len(verses),
    }


def _convert_usfx_root_to_bundle(root: ET.Element) -> dict[str, Any]:
    state = _UsfxState()
    _walk_usfx(root, state)
    state.flush_verse()

    bundle: dict[str, Any] = {
        "translation": dict(ASV_TRANSLATION),
        "books": asv_book_records(),
        "verses": state.verses,
    }
    validate_translation_bundle(bundle)
    return bundle


def _parse_usfx_xml_file(source_path: Path) -> ET.Element:
    try:
        return ET.parse(source_path).getroot()
    except ET.ParseError as exc:
        raise ImportErrorDetail(f"Invalid USFX XML source: {source_path}") from exc
    except OSError as exc:
        raise ImportErrorDetail(f"Could not read USFX source: {source_path}") from exc


def _parse_usfx_zip(source_path: Path) -> ET.Element:
    try:
        with ZipFile(source_path) as archive:
            candidates = [
                name
                for name in archive.namelist()
                if not name.endswith("/") and Path(name).suffix.lower() in {".usfx", ".xml"}
            ]
            if not candidates:
                raise ImportErrorDetail(f"No USFX XML file found inside zip archive: {source_path}")
            source_name = _choose_usfx_member(candidates)
            with archive.open(source_name) as handle:
                data = handle.read()
    except BadZipFile as exc:
        raise ImportErrorDetail(f"Invalid zip archive: {source_path}") from exc
    except OSError as exc:
        raise ImportErrorDetail(f"Could not read zip archive: {source_path}") from exc

    try:
        return ET.parse(BytesIO(data)).getroot()
    except ET.ParseError as exc:
        raise ImportErrorDetail(f"Invalid USFX XML inside zip archive: {source_path}") from exc


def _choose_usfx_member(candidates: list[str]) -> str:
    """Choose the actual USFX Scripture document from an eBible-style zip.

    eBible source zips include support XML files such as BookNames.xml,
    metadata, and vernacular parameter files alongside the Scripture source.
    Prefer filenames that clearly identify the USFX source.
    """

    def score(name: str) -> tuple[int, int, int, str]:
        base = Path(name).name.lower()
        explicit_usfx = 0 if "usfx" in base else 1
        scripture_name = 0 if base.endswith("_usfx.xml") or base.endswith(".usfx") else 1
        metadata_penalty = 1 if any(token in base for token in ("booknames", "metadata", "vernacular")) else 0
        return explicit_usfx, scripture_name, metadata_penalty, name

    return sorted(candidates, key=score)[0]


class _UsfxState:
    def __init__(self) -> None:
        self.current_book: str | None = None
        self.current_chapter: int | None = None
        self.current_verse: int | None = None
        self.current_text: list[str] = []
        self.current_paragraph_break = True
        self.pending_paragraph_break = True
        self.skip_current_book = False
        self.verses: list[dict[str, Any]] = []

    def set_book(self, code: str) -> None:
        self.flush_verse()
        normalized = code.strip().upper()
        if normalized in IGNORED_USFX_BOOK_CODES:
            self.current_book = None
            self.current_chapter = None
            self.skip_current_book = True
            self.pending_paragraph_break = True
            return
        if normalized not in BOOK_BY_USFM:
            raise ImportErrorDetail(f"Unsupported USFX book code: {code!r}.")
        _book_id, name, _testament, _order = BOOK_BY_USFM[normalized]
        self.current_book = name
        self.current_chapter = None
        self.skip_current_book = False
        self.pending_paragraph_break = True

    def set_chapter(self, value: str) -> None:
        self.flush_verse()
        if self.skip_current_book:
            return
        self.current_chapter = _positive_int(value, "chapter")
        self.pending_paragraph_break = True

    def start_verse(self, value: str) -> None:
        self.flush_verse()
        if self.skip_current_book:
            return
        if self.current_book is None or self.current_chapter is None:
            raise ImportErrorDetail("USFX verse appeared before book and chapter markers.")
        self.current_verse = _positive_int(value, "verse")
        self.current_text = []
        self.current_paragraph_break = self.pending_paragraph_break
        self.pending_paragraph_break = False

    def mark_paragraph(self) -> None:
        if self.current_verse is None or not _joined_text(self.current_text):
            self.pending_paragraph_break = True
        else:
            self.current_text.append("\n")

    def add_text(self, text: str | None) -> None:
        if self.current_verse is None or text is None:
            return
        cleaned = " ".join(text.split())
        if not cleaned:
            return
        if self.current_text and not self.current_text[-1].endswith((" ", "\n")):
            self.current_text.append(" ")
        self.current_text.append(cleaned)

    def add_poetry_break(self) -> None:
        if self.current_verse is not None and _joined_text(self.current_text):
            self.current_text.append("\n")

    def flush_verse(self) -> None:
        if self.current_verse is None:
            return
        text = _joined_text(self.current_text)
        text = _apply_poetry_line_breaks(self.current_book, text)
        if not text:
            # Some source files contain verse markers for omitted textual-tradition
            # verses. Do not import a blank verse record; keep validation strict
            # for normalized bundles.
            self.current_verse = None
            self.current_text = []
            self.current_paragraph_break = False
            return
        self.verses.append(
            {
                "book": self.current_book,
                "chapter": self.current_chapter,
                "verse": self.current_verse,
                "text": text,
                "paragraph_break_before": self.current_paragraph_break,
            }
        )
        self.current_verse = None
        self.current_text = []
        self.current_paragraph_break = False


def _walk_usfx(element: ET.Element, state: _UsfxState) -> None:
    tag = _strip_namespace(element.tag)

    if tag == "book":
        code = element.attrib.get("id") or element.attrib.get("code") or ""
        state.set_book(code)
    elif tag == "c":
        chapter = element.attrib.get("id") or element.attrib.get("number") or ""
        state.set_chapter(chapter)
    elif tag == "v":
        verse = element.attrib.get("id") or element.attrib.get("number") or ""
        state.start_verse(verse)
        state.add_text(element.text)
    elif tag in {"p", "pi", "m", "mi"}:
        state.mark_paragraph()
    elif tag in {"q", "q1", "q2", "q3", "q4", "b"}:
        state.add_poetry_break()
        state.add_text(element.text)
    elif tag in {"f", "x", "note"}:
        return
    else:
        state.add_text(element.text)

    for child in element:
        _walk_usfx(child, state)
        if _strip_namespace(child.tag) not in {"f", "x", "note"}:
            state.add_text(child.tail)


def _joined_text(parts: list[str]) -> str:
    lines = [_normalize_verse_line(line) for line in "".join(parts).splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _apply_poetry_line_breaks(book: str | None, text: str) -> str:
    """Add conservative line breaks for imported Hebrew poetry.

    Some eBible ASV USFX poetry lines arrive as one XML paragraph with a
    semicolon separating the poetic cola instead of explicit ``q`` line tags.
    The renderer already honors embedded newlines, so add a cautious break for
    poetry books only and only when the source did not already provide line
    breaks.
    """
    if book not in POETRY_BOOKS or "\n" in text:
        return text
    return re.sub(r";\s+", ";\n", text)


def _normalize_verse_line(line: str) -> str:
    """Normalize whitespace introduced by XML element boundaries.

    ElementTree exposes nested markup as separate text/tail fragments. The
    importer inserts safe spaces between fragments, then this cleanup removes
    typography artifacts such as ``word ,`` and ``earth .`` without changing
    verse wording.
    """
    cleaned = " ".join(line.split())
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([([{])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+([)\]}])", r"\1", cleaned)
    cleaned = re.sub(r"\s+(['’])", r"\1", cleaned)
    cleaned = re.sub(r"([‘])\s+", r"\1", cleaned)
    return cleaned.strip()


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _positive_int(value: str, field_name: str) -> int:
    try:
        number = int(str(value).strip())
    except ValueError as exc:
        raise ImportErrorDetail(f"{field_name} must be a positive integer.") from exc
    if number <= 0:
        raise ImportErrorDetail(f"{field_name} must be a positive integer.")
    return number
