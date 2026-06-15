"""Search helpers for Bible text."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Verse


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A Bible search match."""

    verse: Verse
    query: str

    @property
    def reference_label(self) -> str:
        """Return a normalized verse reference label."""
        return f"{self.verse.book} {self.verse.chapter}:{self.verse.verse}"
