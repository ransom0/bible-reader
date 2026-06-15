"""SQLite storage helpers for bible-reader."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS translations (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    copyright TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    testament TEXT NOT NULL CHECK (testament IN ('OT', 'NT')),
    book_order INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS verses (
    translation_code TEXT NOT NULL,
    book_id INTEGER NOT NULL,
    chapter INTEGER NOT NULL CHECK (chapter > 0),
    verse INTEGER NOT NULL CHECK (verse > 0),
    text TEXT NOT NULL,
    PRIMARY KEY (translation_code, book_id, chapter, verse),
    FOREIGN KEY (translation_code) REFERENCES translations(code) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_verses_reference
ON verses (book_id, chapter, verse);
"""

SAMPLE_TRANSLATION = (
    "ASV",
    "American Standard Version",
    "en",
    "Public domain: ASV 1901",
)

SAMPLE_BOOKS = (
    (43, "John", "NT", 43),
    (45, "Romans", "NT", 45),
)

SAMPLE_VERSES = (
    ("ASV", 43, 3, 16, "For God so loved the world, that he gave his only begotten Son, that whosoever believeth on him should not perish, but have eternal life."),
    ("ASV", 43, 3, 17, "For God sent not the Son into the world to judge the world; but that the world should be saved through him."),
    ("ASV", 45, 8, 28, "And we know that to them that love God all things work together for good, even to them that are called according to his purpose."),
    ("ASV", 45, 8, 29, "For whom he foreknew, he also foreordained to be conformed to the image of his Son, that he might be the firstborn among many brethren:"),
    ("ASV", 45, 8, 30, "and whom he foreordained, them he also called: and whom he called, them he also justified: and whom he justified, them he also glorified."),
)


def connect_database(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open a SQLite connection configured for this app."""
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    """Create database tables and indexes if they do not already exist."""
    connection.executescript(SCHEMA_SQL)
    connection.commit()


def seed_sample_asv(connection: sqlite3.Connection) -> None:
    """Load a tiny ASV fixture used before the full Bible import stage."""
    connection.execute(
        """
        INSERT OR IGNORE INTO translations (code, name, language, copyright)
        VALUES (?, ?, ?, ?)
        """,
        SAMPLE_TRANSLATION,
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO books (id, name, testament, book_order)
        VALUES (?, ?, ?, ?)
        """,
        SAMPLE_BOOKS,
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO verses (translation_code, book_id, chapter, verse, text)
        VALUES (?, ?, ?, ?, ?)
        """,
        SAMPLE_VERSES,
    )
    connection.commit()


def create_sample_connection() -> sqlite3.Connection:
    """Create an in-memory database loaded with the tiny ASV fixture."""
    connection = connect_database()
    initialize_database(connection)
    seed_sample_asv(connection)
    return connection
