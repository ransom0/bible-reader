"""Terminal UI planning primitives.

This module is intentionally dependency-free. It records the first TUI design
contract without pulling in Textual, prompt-toolkit, curses, or any interactive
runtime before the CLI behavior and data model are stable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TuiPane:
    """A planned pane in the future terminal UI."""

    name: str
    purpose: str


@dataclass(frozen=True, slots=True)
class TuiPlan:
    """Static TUI design plan for docs, tests, and the placeholder command."""

    command: str
    status: str
    panes: tuple[TuiPane, ...]
    principles: tuple[str, ...]


def get_tui_plan() -> TuiPlan:
    """Return the current TUI design contract."""
    return TuiPlan(
        command="bible tui",
        status="planned",
        panes=(
            TuiPane("Reading pane", "Display the current passage with the same renderer rules as the CLI."),
            TuiPane("Navigation pane", "Move by book, chapter, passage, search result, bookmark, or note."),
            TuiPane("Study pane", "Show bookmarks, notes, and later public-domain commentary without replacing context."),
            TuiPane("Comparison pane", "Compare translations in stacked or split views depending on terminal width."),
        ),
        principles=(
            "Keep Scripture text, study data, and commentary corpora separate.",
            "Prefer passage/chapter context over isolated topical proof-texting.",
            "Reuse repository, reference parser, search, and render layers instead of forking TUI logic.",
            "Start with a read-only interface before adding interactive writes.",
        ),
    )


def render_tui_plan(plan: TuiPlan | None = None) -> str:
    """Render the TUI plan as plain terminal text."""
    selected = plan or get_tui_plan()
    lines = [
        f"{selected.command} ({selected.status})",
        "",
        "Planned panes:",
    ]
    for pane in selected.panes:
        lines.append(f"  - {pane.name}: {pane.purpose}")

    lines.extend(["", "Design principles:"])
    for principle in selected.principles:
        lines.append(f"  - {principle}")

    lines.extend([
        "",
        "The interactive TUI is not implemented yet; this command records the stable foundation.",
    ])
    return "\n".join(lines)
