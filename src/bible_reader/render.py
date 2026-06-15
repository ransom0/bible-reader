"""Terminal rendering helpers for Bible passages."""

from __future__ import annotations

from collections.abc import Iterable

from .models import Verse
from .search import SearchResult
from .references import BibleReference


class PassageRenderer:
    """Render Bible passages with readable CLI formatting.

    The renderer is intentionally small and dependency-free for now. It gives the
    project a stable formatting layer before adding richer terminal/TUI output.
    """

    def __init__(self, *, color: bool = True, theme: str = "classic") -> None:
        self.color = color and theme != "plain"
        self.theme = theme

    def render(self, reference: BibleReference, verses: Iterable[Verse], *, translation: str) -> str:
        """Return a formatted passage string."""
        verse_list = list(verses)
        lines: list[str] = [self._header(f"{reference.label()} ({translation})"), ""]
        previous_was_break = False

        for verse in verse_list:
            if verse.paragraph_break_before and lines[-1] != "":
                lines.append("")
                previous_was_break = True
            lines.extend(self._verse_lines(verse))
            previous_was_break = False

        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines)

    def _header(self, text: str) -> str:
        if not self.color:
            return text
        return f"\033[1m{text}\033[0m"

    def _verse_number(self, verse: int) -> str:
        number = f"{verse:>3}"
        if not self.color:
            return number
        return f"\033[2m{number}\033[0m"

    def _verse_lines(self, verse: Verse) -> list[str]:
        text_lines = verse.text.splitlines() or [""]
        rendered = [f"{self._verse_number(verse.verse)}  {text_lines[0]}"]
        for continuation in text_lines[1:]:
            rendered.append(f"     {continuation}")
        return rendered


class SearchRenderer:
    """Render search results with compact reference-first formatting."""

    def __init__(self, *, color: bool = True, theme: str = "classic") -> None:
        self.color = color and theme != "plain"
        self.theme = theme

    def render(self, query: str, results: Iterable[SearchResult], *, translation: str) -> str:
        """Return formatted search results."""
        result_list = list(results)
        header = f"Search: {query} ({translation})"
        lines: list[str] = [self._header(header), ""]
        if not result_list:
            lines.append("No matches found.")
            return "\n".join(lines)

        for result in result_list:
            lines.append(f"{self._reference(result.reference_label)}  {self._single_line(result.verse.text)}")
        return "\n".join(lines)

    def _header(self, text: str) -> str:
        if not self.color:
            return text
        return f"\033[1m{text}\033[0m"

    def _reference(self, text: str) -> str:
        if not self.color:
            return text
        return f"\033[36m{text}\033[0m"

    @staticmethod
    def _single_line(text: str) -> str:
        return " / ".join(line.strip() for line in text.splitlines() if line.strip())
