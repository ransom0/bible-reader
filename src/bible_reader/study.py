"""Local user study-data storage for bookmarks and notes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


class StudyStoreError(ValueError):
    """Raised when local study data cannot be read or written safely."""


@dataclass(frozen=True, slots=True)
class Bookmark:
    """A locally stored bookmarked Bible reference."""

    reference: str
    label: str = ""
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class Note:
    """A locally stored note attached to a Bible reference."""

    reference: str
    text: str
    created_at: str = ""


EMPTY_STUDY_DATA: dict[str, list[dict[str, str]]] = {
    "bookmarks": [],
    "notes": [],
}


def default_study_path() -> Path:
    """Return the default XDG-ish local study-data path."""
    data_home = os.environ.get("XDG_DATA_HOME")
    if data_home:
        return Path(data_home).expanduser() / "bible-reader" / "study.json"
    return Path.home() / ".local" / "share" / "bible-reader" / "study.json"


class StudyStore:
    """JSON-backed local user study-data store.

    The store intentionally keeps user data separate from Scripture text. It
    only reads/writes JSON, uses no dynamic imports/eval, and writes via an
    atomic replace to avoid half-written files.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else default_study_path()

    def list_bookmarks(self) -> list[Bookmark]:
        """Return bookmarks in stored order."""
        data = self._read()
        return [
            Bookmark(
                reference=str(item.get("reference", "")),
                label=str(item.get("label", "")),
                created_at=str(item.get("created_at", "")),
            )
            for item in data["bookmarks"]
        ]

    def add_bookmark(self, reference: str, *, label: str = "") -> Bookmark:
        """Add or update a bookmark by normalized reference."""
        data = self._read()
        created_at = _timestamp()
        bookmark = Bookmark(reference=reference, label=label, created_at=created_at)
        remaining = [item for item in data["bookmarks"] if item.get("reference") != reference]
        remaining.append(_bookmark_to_dict(bookmark))
        data["bookmarks"] = remaining
        self._write(data)
        return bookmark

    def remove_bookmark(self, reference: str) -> bool:
        """Remove a bookmark by reference. Return True when one was removed."""
        data = self._read()
        before = len(data["bookmarks"])
        data["bookmarks"] = [item for item in data["bookmarks"] if item.get("reference") != reference]
        removed = len(data["bookmarks"]) != before
        if removed:
            self._write(data)
        return removed

    def list_notes(self) -> list[Note]:
        """Return notes in stored order."""
        data = self._read()
        return [
            Note(
                reference=str(item.get("reference", "")),
                text=str(item.get("text", "")),
                created_at=str(item.get("created_at", "")),
            )
            for item in data["notes"]
        ]

    def add_note(self, reference: str, text: str) -> Note:
        """Append a note for a normalized reference."""
        data = self._read()
        note = Note(reference=reference, text=text, created_at=_timestamp())
        data["notes"].append(_note_to_dict(note))
        self._write(data)
        return note

    def _read(self) -> dict[str, list[dict[str, str]]]:
        if not self.path.exists():
            return {"bookmarks": [], "notes": []}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StudyStoreError(f"Study data file is not valid JSON: {self.path}") from exc
        if not isinstance(raw, dict):
            raise StudyStoreError(f"Study data file must contain a JSON object: {self.path}")
        bookmarks = _validate_record_list(raw.get("bookmarks", []), "bookmarks")
        notes = _validate_record_list(raw.get("notes", []), "notes")
        return {"bookmarks": bookmarks, "notes": notes}

    def _write(self, data: dict[str, list[dict[str, str]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
        ) as handle:
            handle.write(payload)
            temp_name = handle.name
        Path(temp_name).replace(self.path)


def _validate_record_list(value: Any, key: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise StudyStoreError(f"Study data field must be a list: {key}")
    records: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise StudyStoreError(f"Study data field contains a non-object record: {key}")
        records.append({str(record_key): str(record_value) for record_key, record_value in item.items()})
    return records


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bookmark_to_dict(bookmark: Bookmark) -> dict[str, str]:
    return {
        "reference": bookmark.reference,
        "label": bookmark.label,
        "created_at": bookmark.created_at,
    }


def _note_to_dict(note: Note) -> dict[str, str]:
    return {
        "reference": note.reference,
        "text": note.text,
        "created_at": note.created_at,
    }
