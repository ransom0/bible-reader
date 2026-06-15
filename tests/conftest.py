"""Shared pytest fixtures for bible-reader tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_user_data_home(tmp_path, monkeypatch):
    """Keep tests from reading or writing the developer's real app data.

    CLI tests that do not pass --db should exercise the packaged sample fixture,
    not ~/.local/share/bible-reader/bible-reader.sqlite3 from a previous manual
    smoke test.
    """
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
