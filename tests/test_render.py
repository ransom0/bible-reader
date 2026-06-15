from __future__ import annotations

from bible_reader.models import Verse
from bible_reader.references import BibleReference
from bible_reader.render import PassageRenderer


def test_renderer_outputs_plain_passage_with_spacing():
    renderer = PassageRenderer(color=False, theme="plain")
    passage = renderer.render(
        BibleReference(book="John", chapter=3, start_verse=16, end_verse=17),
        [
            Verse("ASV", "John", 3, 16, "For God so loved the world", True),
            Verse("ASV", "John", 3, 17, "For God sent not the Son", False),
        ],
        translation="ASV",
    )

    assert passage.splitlines() == [
        "John 3:16-17 (ASV)",
        "",
        " 16  For God so loved the world",
        " 17  For God sent not the Son",
    ]


def test_renderer_indents_poetry_continuation_lines():
    renderer = PassageRenderer(color=False, theme="plain")
    passage = renderer.render(
        BibleReference(book="Psalms", chapter=23),
        [Verse("ASV", "Psalms", 23, 1, "Jehovah is my shepherd;\nI shall not want.", True)],
        translation="ASV",
    )

    assert "  1  Jehovah is my shepherd;" in passage
    assert "     I shall not want." in passage


def test_renderer_can_emit_ansi_emphasis_for_classic_theme():
    renderer = PassageRenderer(color=True, theme="classic")
    passage = renderer.render(
        BibleReference(book="John", chapter=3, start_verse=16, end_verse=16),
        [Verse("ASV", "John", 3, 16, "For God so loved the world", True)],
        translation="ASV",
    )

    assert "\033[1mJohn 3:16 (ASV)\033[0m" in passage
    assert "\033[2m 16\033[0m" in passage
