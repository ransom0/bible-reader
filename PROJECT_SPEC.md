# bible-reader Project Specification

## Project identity

- Repository: `bible-reader`
- Executable command: `bible`
- Python package: `bible_reader`
- GitHub owner: `ransom0`
- Primary goal: offline-first Bible reading, search, notes, and study from a clean Python CLI application.

This project is separate from the `helpme` CLI app. It should use the same small-pass, patch/tarball/test/merge workflow, but it should not share code or naming with `helpme`.

## Project goals

Build a maintainable Python CLI Bible reader/study tool with:

- offline Bible reading and lookup
- readable terminal formatting from the beginning
- verse, passage, and chapter display
- search
- local notes and bookmarks
- later multi-translation comparison
- later TUI/split-screen reading and comparison
- later public-domain commentary, early church fathers, and theologian corpora

The application should be useful for serious Bible reading and study, not just quick proof-text lookup. Features should prefer passage and context-aware use. The app should avoid encouraging poor hermeneutical practice, such as detached topical verse grabbing without literary or canonical context.

## Translation and licensing policy

The first bundled translation target is the American Standard Version (ASV 1901), because it is public domain.

Project rule:

- Bundle only public-domain, permissively licensed, or explicitly authorized Bible texts.
- Do not scrape or redistribute copyrighted Bible texts.
- Later support for copyrighted translations may be added only through lawful mechanisms such as official APIs, explicit licensing, or user-supplied private local imports that are not distributed by this project.

Likely translation stages:

1. ASV 1901 as the first offline bundled/imported text.
2. Other legally usable public-domain/permissive translations as optional additions.
3. Optional online/API adapters later for translations that cannot be bundled.

## Storage strategy

Use SQLite as the primary local storage engine.

Reasons:

- Python standard library support via `sqlite3`
- portable single-file local database
- efficient lookup and search
- clean support for multiple translations
- clean future support for notes, bookmarks, comparison, commentary, reading state, and search indexes

Planned local storage locations:

- Application data: `~/.local/share/bible-reader/`
- Database: `~/.local/share/bible-reader/bible-reader.sqlite3`
- Configuration: `~/.config/bible-reader/config.toml`

Tests should use small fixture databases and temporary directories, not the user's real local data.

## Security principles

The app should be local-first and conservative:

- Use parameterized SQLite queries only.
- Do not build SQL by concatenating user input.
- Do not use `eval`, `exec`, unsafe deserialization, or dynamic code loading.
- Do not pass user input through shell commands.
- Keep imports/parsers deterministic and validate input data.
- Keep network support out of early stages.
- Do not run downloaded data as code.
- Keep user notes/bookmarks local unless a later sync feature is explicitly designed.

## Architecture

Use a layered structure similar in spirit to `helpme`, but shaped for this domain:

```text
src/bible_reader/
  __init__.py
  cli.py
  config.py
  models.py
  references.py
  rendering.py
  repository.py
  schema.py
  search.py
  service.py
  storage.py
```

Layering:

```text
CLI arguments
  -> service/use-case layer
    -> reference parser
    -> repository/storage layer
    -> renderer
```

The CLI should stay thin. Business rules belong in services, data access belongs in repositories/storage, formatting belongs in rendering, and reference parsing belongs in `references.py`.

## Formatting and terminal output

Formatting should be a first-class concern, not an afterthought.

Initial output should support:

- readable chapter and passage headers
- verse numbers with stable alignment
- sane wrapping and indentation
- paragraph/pericope spacing when source data supports it
- Psalm/superscription-friendly formatting when source data supports it
- plain mode suitable for pipes and copying
- `--no-color` support once color is introduced

The default CLI should be attractive but not noisy. Future TUI work should build on the same rendering concepts rather than replacing them entirely.

## Initial command direction

Candidate early commands:

```bash
bible --help
bible --version
bible books
bible John 3:16
bible read John 3
bible Romans 8:28-30
bible search "kingdom of God"
```

The exact MVP command set will be finalized before implementation.

## Future feature direction

Planned later features include:

- notes
- bookmarks
- search notes/bookmarks
- passage comparison across translations
- TUI/split-screen comparison
- reading plans
- public-domain commentary and patristic/theological sources
- import/export for user data
- pipx-friendly packaging

## Non-goals for early stages

Early stages should not include:

- copyrighted bundled Bible texts
- web scraping
- sync/cloud features
- AI commentary generation
- complex reading plans
- topical proof-text workflows
- full TUI before the CLI foundation is stable
