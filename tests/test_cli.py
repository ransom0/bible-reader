from __future__ import annotations

from bible_reader import __version__
from bible_reader.cli import main


def test_main_without_args_prints_placeholder(capsys):
    assert main([]) == 0

    output = capsys.readouterr().out
    assert "bible-reader is installed" in output
    assert "bible --help" in output
    assert "bible books" in output


def test_help_output(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out
    assert "Offline-first Bible reader" in output
    assert "--version" in output


def test_version_output(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out.strip()
    assert output == f"bible {__version__}"


def test_books_command_lists_sample_fixture_books(capsys):
    assert main(["books"]) == 0

    output = capsys.readouterr().out
    assert "Books available in the ASV sample fixture" in output
    assert "John" in output
    assert "Romans" in output
