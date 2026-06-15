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

## Stage 6 — Search

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

## Stage 7 — Navigation helpers

Add reader-friendly navigation.

Deliverables:

- `bible books`
- `bible chapters <book>`
- optional `random` or next/previous helpers

## Stage 8 — Notes and bookmarks

Add local user study data.

Deliverables:

- bookmark passages
- list bookmarks
- add/list notes
- keep user data separate from Bible text
- tests using temporary data dirs

## Stage 9 — Comparison

Prepare for multi-translation study.

Deliverables:

- compare a passage across available translations
- data model support for multiple versions
- formatted side-by-side or stacked output

## Stage 10 — TUI foundation

Add a real terminal UI after the CLI is stable.

Deliverables:

- basic TUI entry command
- reading pane
- search/navigation pane if feasible
- groundwork for split-screen comparison

## Stage 11 — Commentary and public-domain sources

Add non-Scripture corpora carefully.

Deliverables:

- source/corpus metadata
- public-domain commentary/fathers import path
- verse/passage linking without flattening everything into topical proof-texts

## Stage 12 — Release/install/docs polish

Prepare for GitHub sharing and pipx installation.

Deliverables:

- README polish
- CHANGELOG
- install/update docs
- smoke-test checklist
- versioning guidance


## Stage 2 implementation note

Stage 2 proves the SQLite schema and repository layer with a tiny in-memory ASV fixture. The full ASV import is intentionally deferred until lookup, formatting, and validation behavior are stable.

## Stage 4 implementation note

Stage 4 introduces a dedicated rendering layer before the full ASV import. The fixture includes Psalm text with embedded line breaks so poetry indentation can be tested early. Paragraph/pericope spacing is modeled as verse metadata, not as hard-coded CLI behavior.

## Stage 5 — ASV import planning

- Add a validated internal translation bundle format.
- Add importer tests using a tiny ASV JSON fixture.
- Document source licensing and import safety rules.
- Keep full ASV text import for a later, separately testable pass.

