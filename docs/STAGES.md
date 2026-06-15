# Development Stages

## Stage 0 — Project planning/spec

Define the project shape before code.

Deliverables:

- `PROJECT_SPEC.md`
- `docs/STAGES.md`
- `docs/WORKFLOW.md`
- initial README alignment

No Python implementation is required in this stage.

## Stage 1 — Repository scaffold

Create a testable Python package skeleton.

Deliverables:

- `pyproject.toml`
- `src/bible_reader/`
- `tests/`
- console script entry point: `bible`
- `bible --help`
- `bible --version`
- pytest baseline

Suggested test gate:

```bash
python -m pytest
python -m bible_reader --help
python -m bible_reader --version
```

## Stage 2 — SQLite schema and tiny fixture data

Prove the storage design before importing a full Bible.

Deliverables:

- SQLite schema for translations, books, chapters/verses
- tiny test fixture database
- repository lookup methods
- schema validation tests

No full ASV data yet.

## Stage 3 — Reference parsing and lookup

Support normal Bible references.

Deliverables:

- parse book/chapter/verse references
- support passages and ranges
- support common book abbreviations
- helpful errors for malformed references

Target examples:

```bash
bible John 3:16
bible John 3
bible Romans 8:28-30
bible "1 Cor 13"
```

## Stage 4 — Reading output polish

Make terminal output genuinely pleasant.

Deliverables:

- chapter/passages headers
- aligned verse numbers
- wrapping/indentation
- spacing hooks for paragraphs/pericopes
- Psalm/superscription formatting hooks
- `--no-color` or equivalent plain-output option

## Stage 5 — ASV import

Add the first real public-domain translation.

Deliverables:

- ASV import path
- source/licensing documentation
- imported SQLite data or reproducible import command
- validation checks for book/chapter/verse counts

## Stage 6 — Full ASV source import

Add a local-file source import path for public-domain ASV source files.

Deliverables:

- ASV USFX source converter
- explicit SQLite import commands
- tests for source conversion and database lookup
- documentation for safe local source import

## Stage 7 — Search

Add simple and useful full-text search.

Deliverables:

- case-insensitive search
- phrase search
- optional book-limited search if straightforward
- readable search results
- tests for matching behavior

Target examples:

```bash
bible search "kingdom of God"
bible search resurrection --book Romans
```

## Stage 8 — Navigation helpers

Add reader-friendly navigation.

Deliverables:

- `bible books`
- `bible chapters <book>`
- optional `random` or next/previous helpers

## Stage 9 — Notes and bookmarks

Add local user study data.

Deliverables:

- bookmark passages
- list/remove bookmarks
- add/list notes
- keep user data separate from Bible text
- write JSON user data atomically
- tests using temporary data dirs

## Stage 10 — Comparison

Prepare for multi-translation study.

Deliverables:

- compare a passage across available translations
- data model support for multiple versions
- formatted side-by-side or stacked output

## Stage 11 — TUI foundation

Add a real terminal UI after the CLI is stable.

Deliverables:

- basic TUI entry command
- reading pane
- search/navigation pane if feasible
- groundwork for split-screen comparison

## Stage 12 — Release/install/docs polish

Prepare the project for GitHub sharing, pipx installation, and repeatable smoke testing.

Deliverables:

- README polish
- CHANGELOG
- install/update docs
- smoke-test checklist
- versioning guidance
- lightweight doctor command

## Stage 13 — Commentary and public-domain sources

Add non-Scripture corpora carefully.

Deliverables:

- source/corpus metadata
- public-domain commentary/fathers import path
- verse/passage linking without flattening everything into topical proof-texts


## Stage 2 implementation note

Stage 2 proves the SQLite schema and repository layer with a tiny in-memory ASV fixture. The full ASV import is intentionally deferred until lookup, formatting, and validation behavior are stable.

## Stage 4 implementation note

Stage 4 introduces a dedicated rendering layer before the full ASV import. The fixture includes Psalm text with embedded line breaks so poetry indentation can be tested early. Paragraph/pericope spacing is modeled as verse metadata, not as hard-coded CLI behavior.

## Stage 5 — ASV import planning

- Add a validated internal translation bundle format.
- Add importer tests using a tiny ASV JSON fixture.
- Document source licensing and import safety rules.
- Keep full ASV text import for a later, separately testable pass.


## Stage 6 implementation note

Stage 6 adds explicit local import commands instead of silently writing to user
data directories. This keeps the early app safe and testable: data imports use
parameterized SQLite writes, downloaded source files are treated as untrusted
text/XML, and normal reading remains offline after import.


## Stage 7 status

Adds simple safe SQLite-backed phrase search with result formatting, book limiting, and result limits. This remains intentionally passage-aware and reference-first rather than topical proof-text generation.


## Stage 8 status

Adds `bible chapters <book>` as the first navigation helper beyond the existing `books` command. This keeps navigation reference-first and context-aware: users can inspect available chapters for a canonical book or common alias before reading/searching.

## Stage 9 implementation note

Stage 9 adds a separate JSON-backed study-data store for bookmarks and notes. User study data is kept outside the Scripture SQLite database and can be redirected with `--study PATH` for tests, backups, or experiments.


## Stage 10 implementation note

Stage 10 adds `bible compare <reference>` with stacked comparison output. The
first CLI comparison view favors narrow-terminal readability and testability over
side-by-side layout. The SQLite model already supports multiple translation codes,
so this stage proves comparison behavior with the sample ASV fixture and an
additional test translation bundle.


## Stage 11 implementation note

Stage 11 records the TUI foundation without adding an interactive dependency yet. The `bible tui` command prints the planned pane layout and design rules so the future Textual-style interface remains tied to the tested CLI/service/repository/render layers.


## Stage 12 status

Adds release documentation and a lightweight `bible doctor` command for smoke tests. The project remains pre-alpha and intentionally uses explicit local data paths for imports and study data.

## Stage 13 — dev environment polish

- Add `.envrc` for the local direnv workflow.
- Document the venv/direnv setup.
- Keep dependency installation explicit and testable.


## Stage 14 — Default ASV database

- Add an XDG-compatible default SQLite database path.
- Add `bible init-db` for bootstrapping a local database.
- Prefer the default local database when it exists; otherwise keep the tiny fixture fallback.
- Keep full-ASV import separate from the bootstrapping mechanics.
