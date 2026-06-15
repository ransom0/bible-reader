"""Terminal rendering helpers for Bible passages."""

from __future__ import annotations

from collections.abc import Iterable
import textwrap

from .models import Verse
from .search import SearchResult
from .references import BibleReference


def _resolve_width(width: int | None) -> int:
    """Return a safe wrapping width for terminal output."""
    if width is not None:
        return max(20, width)
    # Keep default output stable and readable across test runners, cron, and
    # terminals that do not report a useful width. Users can opt into narrower
    # wrapping with --width.
    return 120


def _wrap_prefixed_line(text: str, *, prefix: str, continuation_prefix: str, width: int) -> list[str]:
    """Wrap one logical line while preserving verse/reference prefixes."""
    content = text.strip()
    available_first = max(10, width - _visible_prefix_len(prefix))
    available_next = max(10, width - _visible_prefix_len(continuation_prefix))
    wrapped = textwrap.wrap(
        content,
        width=available_first,
        subsequent_indent="",
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]

    lines = [prefix + wrapped[0]]
    for part in wrapped[1:]:
        # Re-wrap continuation chunks against the continuation prefix width so
        # narrow outputs stay inside the requested width.
        for continuation in textwrap.wrap(
            part,
            width=available_next,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [""]:
            lines.append(continuation_prefix + continuation)
    return lines


def _visible_prefix_len(text: str) -> int:
    """Return printable prefix width; ANSI escapes are not generated here."""
    # The current colorized prefixes only wrap the verse number, so measuring the
    # raw prefix would over-count ANSI escape codes. Use the plain-space shape
    # instead.
    if "\033" not in text:
        return len(text)
    stripped = text.replace("\033[2m", "").replace("\033[0m", "")
    return len(stripped)


class PassageRenderer:
    """Render Bible passages with readable CLI formatting.

    The renderer is intentionally small and dependency-free for now. It gives the
    project a stable formatting layer before adding richer terminal/TUI output.
    """

    def __init__(self, *, color: bool = True, theme: str = "classic", width: int | None = None) -> None:
        self.color = color and theme != "plain"
        self.theme = theme
        self.width = _resolve_width(width)

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
        first_prefix = f"{self._verse_number(verse.verse)}  "
        continuation_prefix = "     "
        rendered: list[str] = []
        for index, logical_line in enumerate(text_lines):
            prefix = first_prefix if index == 0 else continuation_prefix
            rendered.extend(_wrap_prefixed_line(logical_line, prefix=prefix, continuation_prefix=continuation_prefix, width=self.width))
        return rendered


class SearchRenderer:
    """Render search results with compact reference-first formatting."""

    def __init__(self, *, color: bool = True, theme: str = "classic", width: int | None = None) -> None:
        self.color = color and theme != "plain"
        self.theme = theme
        self.width = _resolve_width(width)

    def render(self, query: str, results: Iterable[SearchResult], *, translation: str) -> str:
        """Return formatted search results."""
        result_list = list(results)
        header = f"Search: {query} ({translation})"
        lines: list[str] = [self._header(header)]
        if not result_list:
            lines.extend(["", "No matches found.", "Try a shorter phrase or remove book filters."])
            return "\n".join(lines)

        count_label = "result" if len(result_list) == 1 else "results"
        lines.extend([f"Showing {len(result_list)} {count_label}.", ""])
        for index, result in enumerate(result_list):
            if index > 0:
                lines.append("")
            lines.append(self._reference(result.reference_label))
            lines.extend(
                _wrap_prefixed_line(
                    self._single_line(result.verse.text),
                    prefix="  ",
                    continuation_prefix="  ",
                    width=self.width,
                )
            )
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


class ComparisonRenderer:
    """Render one passage across multiple translations.

    The first comparison view is intentionally stacked instead of side-by-side.
    Stacked output is readable in narrow terminals and gives the future TUI a
    stable, testable comparison data path before split-pane rendering arrives.
    """

    def __init__(self, *, color: bool = True, theme: str = "classic", width: int | None = None) -> None:
        self.color = color and theme != "plain"
        self.theme = theme
        self.width = _resolve_width(width)

    def render(self, reference: BibleReference, passages: dict[str, Iterable[Verse]]) -> str:
        """Return a formatted comparison for one reference."""
        lines: list[str] = [self._header(f"Compare: {reference.label()}"), ""]
        for translation, verses in passages.items():
            verse_list = list(verses)
            lines.append(self._translation_header(translation))
            if not verse_list:
                lines.append("  Not available for this reference.")
            else:
                for verse in verse_list:
                    lines.extend(self._verse_lines(verse))
            lines.append("")

        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines)

    def _header(self, text: str) -> str:
        if not self.color:
            return text
        return f"\033[1m{text}\033[0m"

    def _translation_header(self, text: str) -> str:
        if not self.color:
            return text
        return f"\033[36m{text}\033[0m"

    def _verse_lines(self, verse: Verse) -> list[str]:
        text_lines = verse.text.splitlines() or [""]
        first_prefix = f"  {verse.verse:>3}  "
        continuation_prefix = "       "
        rendered: list[str] = []
        for index, logical_line in enumerate(text_lines):
            prefix = first_prefix if index == 0 else continuation_prefix
            rendered.extend(_wrap_prefixed_line(logical_line, prefix=prefix, continuation_prefix=continuation_prefix, width=self.width))
        return rendered
