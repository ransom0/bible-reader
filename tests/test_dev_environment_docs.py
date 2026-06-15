from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_envrc_exists_and_uses_project_venv():
    envrc = ROOT / ".envrc"
    assert envrc.is_file()
    text = envrc.read_text(encoding="utf-8")
    assert ".venv/bin/activate" in text
    assert "PYTHONPATH" in text
    assert "$PWD/src" in text


def test_dev_environment_docs_mention_direnv_and_test_gate():
    doc = (ROOT / "docs" / "DEV_ENVIRONMENT.md").read_text(encoding="utf-8")
    assert "direnv allow" in doc
    assert "python -m pytest" in doc
    assert "bible doctor" in doc


def test_readme_links_dev_environment_doc():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/DEV_ENVIRONMENT.md" in readme
    assert "direnv allow" in readme
