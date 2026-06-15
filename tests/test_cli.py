from __future__ import annotations

from bible_reader import __version__
from bible_reader.cli import main


def test_main_without_args_prints_placeholder(capsys):
    assert main([]) == 0

    output = capsys.readouterr().out
    assert "bible-reader is installed" in output
    assert "bible books" in output
    assert "bible John 3:16" in output
    assert "bible read John 3" in output


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
    assert "Psalms" in output
    assert "John" in output
    assert "Romans" in output


def test_lookup_single_verse_by_positional_reference(capsys):
    assert main(["John", "3:16"]) == 0

    output = capsys.readouterr().out
    assert "John 3:16 (ASV)" in output
    assert "For God so loved the world" in output


def test_lookup_range_by_positional_reference(capsys):
    assert main(["Romans", "8:28-30"]) == 0

    output = capsys.readouterr().out
    assert "Romans 8:28-30 (ASV)" in output
    assert "work together for good" in output
    assert "also glorified" in output


def test_read_chapter_command(capsys):
    assert main(["read", "John", "3"]) == 0

    output = capsys.readouterr().out
    assert "John 3 (ASV)" in output
    assert "For God so loved the world" in output
    assert "world should be saved" in output


def test_lookup_missing_reference_reports_error(capsys):
    assert main(["John", "3:99"]) == 1

    error = capsys.readouterr().err
    assert "Reference not found" in error
    assert "John 3:99" in error


def test_bad_reference_reports_parse_error(capsys):
    assert main(["not", "a", "reference"]) == 2

    error = capsys.readouterr().err
    assert "Could not parse reference" in error


def test_lookup_plain_theme_disables_ansi_color(capsys):
    assert main(["--no-color", "John", "3:16"]) == 0

    output = capsys.readouterr().out
    assert "\033" not in output
    assert "John 3:16 (ASV)" in output


def test_lookup_psalm_keeps_poetry_line_spacing(capsys):
    assert main(["--no-color", "Ps", "23"]) == 0

    output = capsys.readouterr().out
    assert "Psalms 23 (ASV)" in output
    assert "  1  Jehovah is my shepherd;" in output
    assert "     I shall not want." in output


def test_unknown_theme_reports_error(capsys):
    assert main(["--theme", "loud", "John", "3:16"]) == 2

    error = capsys.readouterr().err
    assert "Unknown theme: loud" in error
