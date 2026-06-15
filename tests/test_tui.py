from __future__ import annotations

from bible_reader.tui import get_tui_plan, render_tui_plan


def test_tui_plan_records_expected_command_and_panes():
    plan = get_tui_plan()

    assert plan.command == "bible tui"
    assert plan.status == "planned"
    assert [pane.name for pane in plan.panes] == [
        "Reading pane",
        "Navigation pane",
        "Study pane",
        "Comparison pane",
    ]


def test_tui_plan_keeps_context_first_design_rule():
    plan = get_tui_plan()

    assert any("passage/chapter context" in principle for principle in plan.principles)
    assert any("Scripture text, study data, and commentary" in principle for principle in plan.principles)


def test_render_tui_plan_outputs_plain_text():
    output = render_tui_plan()

    assert "bible tui (planned)" in output
    assert "Planned panes:" in output
    assert "Reading pane" in output
    assert "Design principles:" in output
    assert "interactive TUI is not implemented yet" in output
