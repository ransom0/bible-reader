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
    assert "database:" in output
    assert ("sample fixture" in output) or ("default local database" in output)
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




def test_import_usfx_command_accepts_zip_source(tmp_path, capsys):
    from zipfile import ZipFile

    db_path = tmp_path / "bible.sqlite3"
    source_zip = tmp_path / "eng-asv_usfx.zip"
    with ZipFile(source_zip, "w") as archive:
        archive.write("tests/fixtures/asv_tiny.usfx", "eng-asv_usfx.xml")

    assert main(["import-usfx", str(source_zip), "--db", str(db_path)]) == 0
    import_output = capsys.readouterr().out
    assert "Imported ASV USFX source" in import_output
    assert "2 books, 4 verses" in import_output

    assert main(["--db", str(db_path), "--no-color", "Ps", "23"]) == 0
    lookup_output = capsys.readouterr().out
    assert "Psalms 23 (ASV)" in lookup_output
    assert "Jehovah is my shepherd" in lookup_output


def test_init_db_command_accepts_usfx_source(tmp_path, capsys):
    db_path = tmp_path / "default.sqlite3"

    assert main([
        "init-db",
        "--force",
        "--usfx-source",
        "tests/fixtures/asv_tiny.usfx",
        "--db",
        str(db_path),
    ]) == 0
    output = capsys.readouterr().out
    assert "Initialized Bible database from ASV USFX source" in output

    assert main(["--db", str(db_path), "--no-color", "John", "3:16"]) == 0
    lookup_output = capsys.readouterr().out
    assert "For God so loved the world" in lookup_output


def test_init_db_command_rejects_two_source_modes(tmp_path, capsys):
    db_path = tmp_path / "bad.sqlite3"

    assert main([
        "init-db",
        "--source",
        "tests/fixtures/asv_sample_bundle.json",
        "--usfx-source",
        "tests/fixtures/asv_tiny.usfx",
        "--db",
        str(db_path),
    ]) == 2

    error = capsys.readouterr().err
    assert "choose either --source or --usfx-source" in error


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



def test_init_db_command_creates_default_database_with_xdg_home(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert main(["init-db"]) == 0
    init_output = capsys.readouterr().out
    assert "Initialized Bible database" in init_output

    assert main(["--no-color", "Romans", "8:28-30"]) == 0
    lookup_output = capsys.readouterr().out
    assert "Romans 8:28-30 (ASV)" in lookup_output
    assert "work together for good" in lookup_output


def test_init_db_command_rejects_existing_without_force(tmp_path, capsys):
    db_path = tmp_path / "bible.sqlite3"

    assert main(["--db", str(db_path), "init-db"]) == 0
    capsys.readouterr()

    assert main(["--db", str(db_path), "init-db"]) == 2
    error = capsys.readouterr().err
    assert "Use --force" in error


def test_init_db_command_force_replaces_existing_database(tmp_path, capsys):
    db_path = tmp_path / "bible.sqlite3"

    assert main(["--db", str(db_path), "init-db"]) == 0
    capsys.readouterr()

    assert main(["--db", str(db_path), "init-db", "--force"]) == 0
    output = capsys.readouterr().out
    assert "Initialized Bible database" in output


def test_doctor_reports_default_database_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "default database not initialized" in output
    assert "bible-reader.sqlite3" in output

    assert main(["init-db"]) == 0
    capsys.readouterr()

    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "default local database" in output


def test_width_option_wraps_direct_reference_output(capsys):
    assert main(["--no-color", "--width", "44", "John", "3:16"]) == 0

    output = capsys.readouterr().out
    lines = output.splitlines()
    assert "John 3:16 (ASV)" in lines[0]
    assert " 16  For God so loved the world, that he" in lines
    assert "     gave his only begotten Son, that" in lines
    assert all(len(line) <= 44 for line in lines if line)


def test_width_option_rejects_too_narrow_value(capsys):
    assert main(["--width", "12", "John", "3:16"]) == 2

    error = capsys.readouterr().err
    assert "--width must be 20 or greater" in error
