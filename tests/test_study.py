import json

import pytest

from bible_reader.study import StudyStore, StudyStoreError, default_study_path


def test_study_store_adds_lists_and_removes_bookmark(tmp_path):
    store = StudyStore(tmp_path / "study.json")

    bookmark = store.add_bookmark("John 3:16", label="Gospel")

    assert bookmark.reference == "John 3:16"
    assert bookmark.label == "Gospel"
    assert bookmark.created_at.endswith("Z")
    assert store.list_bookmarks() == [bookmark]

    assert store.remove_bookmark("John 3:16") is True
    assert store.list_bookmarks() == []
    assert store.remove_bookmark("John 3:16") is False


def test_study_store_replaces_existing_bookmark_by_reference(tmp_path):
    store = StudyStore(tmp_path / "study.json")

    store.add_bookmark("John 3:16", label="first")
    store.add_bookmark("John 3:16", label="second")

    bookmarks = store.list_bookmarks()
    assert len(bookmarks) == 1
    assert bookmarks[0].label == "second"


def test_study_store_adds_notes_without_replacing_existing_notes(tmp_path):
    store = StudyStore(tmp_path / "study.json")

    store.add_note("John 3:16", "First note")
    store.add_note("John 3:16", "Second note")

    notes = store.list_notes()
    assert [note.text for note in notes] == ["First note", "Second note"]


def test_study_store_writes_expected_json_shape(tmp_path):
    path = tmp_path / "nested" / "study.json"
    store = StudyStore(path)

    store.add_bookmark("Psalms 23", label="Psalm")
    store.add_note("Psalms 23", "Poetry note")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert sorted(data) == ["bookmarks", "notes"]
    assert data["bookmarks"][0]["reference"] == "Psalms 23"
    assert data["notes"][0]["text"] == "Poetry note"


def test_study_store_rejects_malformed_json(tmp_path):
    path = tmp_path / "study.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(StudyStoreError):
        StudyStore(path).list_bookmarks()


def test_default_study_path_respects_xdg_data_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert default_study_path() == tmp_path / "bible-reader" / "study.json"
