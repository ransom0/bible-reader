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
    assert "bible search shepherd" in output
    assert "bible doctor" in output
    assert "bible chapters John" in output
    assert "bible bookmark add John 3:16" in output
    assert "bible note add John 3:16" in output


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



def test_doctor_command_reports_runtime_status(capsys):
    assert main(["doctor"]) == 0

    output = capsys.readouterr().out
    assert "bible-reader doctor" in output
    assert f"version: {__version__}" in output
    assert "database: sample fixture" in output
    assert "status: ok" in output


def test_doctor_command_respects_runtime_options(tmp_path, capsys):
    db_path = tmp_path / "bible.sqlite3"
    study_path = tmp_path / "study.json"

    assert main(["--no-color", "--theme", "plain", "--db", str(db_path), "--study", str(study_path), "doctor"]) == 0

    output = capsys.readouterr().out
    assert f"database: {db_path}" in output
    assert f"study file: {study_path}" in output
    assert "theme: plain" in output
    assert "color: off" in output

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


def test_import_bundle_command_writes_sqlite_db_and_lookup_uses_db(tmp_path, capsys):
    db_path = tmp_path / "bible.sqlite3"
    bundle_path = "tests/fixtures/asv_sample_bundle.json"

    assert main(["import-bundle", bundle_path, "--db", str(db_path)]) == 0
    import_output = capsys.readouterr().out
    assert "Imported translation bundle" in import_output

    assert main(["--db", str(db_path), "--no-color", "John", "3:16"]) == 0
    lookup_output = capsys.readouterr().out
    assert "John 3:16 (ASV)" in lookup_output
    assert "For God so loved the world" in lookup_output


def test_import_bundle_requires_db(capsys):
    assert main(["import-bundle", "tests/fixtures/asv_sample_bundle.json"]) == 2

    error = capsys.readouterr().err
    assert "requires --db" in error


def test_import_usfx_command_writes_sqlite_db_and_read_uses_db(tmp_path, capsys):
    db_path = tmp_path / "bible.sqlite3"
    source_path = "tests/fixtures/asv_tiny.usfx"

    assert main(["import-usfx", source_path, "--db", str(db_path)]) == 0
    import_output = capsys.readouterr().out
    assert "Imported ASV USFX source" in import_output

    assert main(["--db", str(db_path), "--no-color", "read", "Ps", "23"]) == 0
    lookup_output = capsys.readouterr().out
    assert "Psalms 23 (ASV)" in lookup_output
    assert "Jehovah is my shepherd;" in lookup_output
    assert "I shall not want." in lookup_output


def test_search_command_finds_sample_fixture_matches(capsys):
    assert main(["--no-color", "search", "shepherd"]) == 0

    output = capsys.readouterr().out
    assert "Search: shepherd (ASV)" in output
    assert "Psalms 23:1" in output
    assert "Jehovah is my shepherd" in output
    assert "\033" not in output


def test_search_command_can_limit_by_book(capsys):
    assert main(["--no-color", "search", "world", "--book", "John"]) == 0

    output = capsys.readouterr().out
    assert "John 3:16" in output
    assert "John 3:17" in output
    assert "Romans" not in output


def test_search_command_returns_one_when_no_matches(capsys):
    assert main(["--no-color", "search", "zzzzzz"]) == 1

    output = capsys.readouterr().out
    assert "No matches found." in output


def test_search_command_rejects_bad_limit(capsys):
    assert main(["search", "world", "--limit", "0"]) == 2

    error = capsys.readouterr().err
    assert "--limit must be 1 or greater" in error


def test_chapters_command_lists_available_chapters(capsys):
    assert main(["chapters", "John"]) == 0

    output = capsys.readouterr().out
    assert output.strip() == "John chapters: 3"


def test_chapters_command_accepts_book_alias(capsys):
    assert main(["chapters", "Ps"]) == 0

    output = capsys.readouterr().out
    assert output.strip() == "Psalms chapters: 23"


def test_chapters_command_returns_one_for_missing_book(capsys):
    assert main(["chapters", "Genesis"]) == 1

    error = capsys.readouterr().err
    assert "Book not found" in error
    assert "Genesis" in error


def test_bookmark_commands_use_explicit_study_file(tmp_path, capsys):
    study_path = tmp_path / "study.json"

    assert main(["--study", str(study_path), "bookmark", "add", "John", "3:16", "--label", "Gospel"]) == 0
    add_output = capsys.readouterr().out
    assert "Bookmarked John 3:16" in add_output
    assert "Gospel" in add_output

    assert main(["--study", str(study_path), "bookmarks"]) == 0
    list_output = capsys.readouterr().out
    assert "Bookmarks:" in list_output
    assert "John 3:16" in list_output
    assert "Gospel" in list_output

    assert main(["--study", str(study_path), "bookmark", "remove", "John", "3:16"]) == 0
    remove_output = capsys.readouterr().out
    assert "Removed bookmark: John 3:16" in remove_output


def test_bookmark_remove_returns_one_for_missing_bookmark(tmp_path, capsys):
    study_path = tmp_path / "study.json"

    assert main(["--study", str(study_path), "bookmark", "remove", "John", "3:16"]) == 1

    error = capsys.readouterr().err
    assert "Bookmark not found: John 3:16" in error


def test_note_commands_use_explicit_study_file(tmp_path, capsys):
    study_path = tmp_path / "study.json"

    assert main(["--study", str(study_path), "note", "add", "John 3:16", "Do", "not", "proof-text"]) == 0
    add_output = capsys.readouterr().out
    assert "Added note for John 3:16" in add_output

    assert main(["--study", str(study_path), "notes"]) == 0
    list_output = capsys.readouterr().out
    assert "Notes:" in list_output
    assert "John 3:16" in list_output
    assert "Do not proof-text" in list_output


def test_study_option_requires_value(capsys):
    assert main(["--study"]) == 2

    error = capsys.readouterr().err
    assert "--study requires a value" in error


def test_tui_command_shows_planning_placeholder(capsys):
    assert main(["tui"]) == 0

    output = capsys.readouterr().out
    assert "bible tui (planned)" in output
    assert "Reading pane" in output
    assert "Comparison pane" in output
    assert "interactive TUI is not implemented yet" in output

