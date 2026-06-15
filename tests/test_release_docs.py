from __future__ import annotations

from pathlib import Path

from bible_reader import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_release_docs_exist_and_mention_pipx_and_smoke_tests():
    assert (ROOT / "CHANGELOG.md").is_file()
    assert (ROOT / "docs" / "INSTALL.md").is_file()
    assert (ROOT / "docs" / "SMOKE_TEST.md").is_file()
    assert (ROOT / "docs" / "VERSIONING.md").is_file()

    install = (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")
    smoke = (ROOT / "docs" / "SMOKE_TEST.md").read_text(encoding="utf-8")
    assert "pipx install" in install
    assert "bible doctor" in install
    assert "bible --no-color Ps 23" in smoke


def test_changelog_mentions_current_version():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert __version__ in changelog
    assert "Unreleased" in changelog
