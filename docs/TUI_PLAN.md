# TUI Plan

The first interactive TUI should be built after the CLI data model, reference
parser, rendering layer, search, comparison, and study-data store are stable.
The project should not fork a separate TUI data path. The TUI should call the
same repository, parser, search, rendering, comparison, and study modules that
the CLI already tests.

## Initial command

```bash
bible tui
```

Stage 11 intentionally adds a placeholder/planning command rather than pulling
in a TUI framework immediately. That keeps packaging, tests, and CLI behavior
stable before choosing an interactive stack.

## Candidate stack

Textual is the likely future choice because it is Python-native, testable, and
well suited for split-pane terminal applications. The project should still keep
TUI dependencies optional until the real interface is implemented.

## Planned panes

- Reading pane: current passage, chapter, or search result using the existing
  passage renderer's formatting decisions.
- Navigation pane: books, chapters, search results, bookmarks, and notes.
- Study pane: user notes/bookmarks first; public-domain commentary/Fathers later.
- Comparison pane: stacked by default; split-screen when terminal width allows.

## Design rules

- Scripture text, user study data, and commentary corpora remain separate.
- The TUI should encourage passage/chapter context instead of topical
  proof-texting.
- Read-only navigation should come before interactive editing.
- Notes/bookmarks must continue to use safe local writes and explicit test paths.
- Full-screen behavior must have an escape hatch back to plain CLI output.
