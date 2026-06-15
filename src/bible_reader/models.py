"""Domain models for Bible text metadata and verses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Translation:
    """A Bible translation available to the application."""

    code: str
    name: str
    language: str
    copyright: str


@dataclass(frozen=True, slots=True)
class Book:
    """A canonical Bible book."""

    id: int
    name: str
    testament: str
    order: int


@dataclass(frozen=True, slots=True)
class Verse:
    """A single Bible verse in one translation."""

    translation: str
    book: str
    chapter: int
    verse: int
    text: str
