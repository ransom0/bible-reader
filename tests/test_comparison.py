from __future__ import annotations

from bible_reader.cli import main
from bible_reader.importers import import_translation_bundle, load_translation_bundle
from bible_reader.render import ComparisonRenderer
from bible_reader.references import BibleReference
from bible_reader.storage import connect_database
from bible_reader.models import Verse


def test_comparison_renderer_stacks_translations_without_color():
    renderer = ComparisonRenderer(color=False, theme="plain")
    passage = renderer.render(
        BibleReference(book="John", chapter=3, start_verse=16, end_verse=16),
        {
            "ASV": [Verse("ASV", "John", 3, 16, "For God so loved the world", True)],
            "ALT": [Verse("ALT", "John", 3, 16, "God loved the world in this way", True)],
        },
    )

    assert passage.splitlines() == [
        "Compare: John 3:16",
        "",
        "ASV",
        "   16  For God so loved the world",
        "",
        "ALT",
        "   16  God loved the world in this way",
    ]


def test_comparison_renderer_reports_missing_translation_passage():
    renderer = ComparisonRenderer(color=False, theme="plain")
    passage = renderer.render(
        BibleReference(book="John", chapter=3, start_verse=16, end_verse=16),
        {"ASV": [Verse("ASV", "John", 3, 16, "For God so loved the world", True)], "ALT": []},
    )

    assert "ALT\n  Not available for this reference." in passage


def test_compare_command_uses_sample_fixture(capsys):
    assert main(["--no-color", "compare", "John", "3:16"]) == 0

    output = capsys.readouterr().out
    assert "Compare: John 3:16" in output
    assert "ASV" in output
    assert "For God so loved the world" in output
    assert "\033" not in output


def test_compare_command_accepts_specific_versions(capsys):
    assert main(["--no-color", "compare", "John", "3:16", "--versions", "ASV"]) == 0

    output = capsys.readouterr().out
    assert "Compare: John 3:16" in output
    assert "ASV" in output


def test_compare_command_rejects_unknown_version(capsys):
    assert main(["--no-color", "compare", "John", "3:16", "--versions", "NOPE"]) == 2

    error = capsys.readouterr().err
    assert "unknown translation code" in error
    assert "NOPE" in error


def test_compare_command_handles_range(capsys):
    assert main(["--no-color", "compare", "Romans", "8:28-30"]) == 0

    output = capsys.readouterr().out
    assert "Compare: Romans 8:28-30" in output
    assert "work together for good" in output
    assert "also glorified" in output


def test_compare_command_can_use_multi_translation_database(tmp_path, capsys):
    db_path = tmp_path / "compare.sqlite3"
    bundle = load_translation_bundle("tests/fixtures/asv_sample_bundle.json")
    alt_bundle = load_translation_bundle("tests/fixtures/asv_sample_bundle.json")
    alt_bundle["translation"] = {
        "code": "ALT",
        "name": "Alternate Test Translation",
        "language": "en",
        "copyright": "Test fixture only",
    }
    alt_bundle["verses"][1]["text"] = "For the alternate fixture loved the comparison test."

    connection = connect_database(db_path)
    try:
        import_translation_bundle(connection, bundle)
        import_translation_bundle(connection, alt_bundle)
    finally:
        connection.close()

    assert main(["--db", str(db_path), "--no-color", "compare", "John", "3:16", "--versions", "ASV,ALT"]) == 0

    output = capsys.readouterr().out
    assert "ASV" in output
    assert "For God so loved the world" in output
    assert "ALT" in output
    assert "alternate fixture" in output
