# bible-reader

Offline-first Python CLI Bible reader, search, notes, and study tool.

Initial command: `bible`

Initial bundled translation target: American Standard Version (ASV 1901), public domain.

This project is intentionally built in small tested passes using a patch/tarball/test/merge workflow.

## Development quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest
python -m pytest
python -m bible_reader --help
python -m bible_reader --version
```

Optional `direnv` workflow, after `.venv` exists:

```bash
direnv allow
cd ..
cd bible-reader
bible --version
```

After editable install, the console command is available:

```bash
bible --help
bible --version
bible books
bible John 3:16
bible read John 3
bible search shepherd
bible compare John 3:16
bible compare Romans 8:28-30 --versions ASV
bible doctor
bible tui
bible chapters John
bible chapters Ps
bible --no-color Ps 23
bible --study /tmp/bible-study.json bookmark add John 3:16 --label Gospel
bible --study /tmp/bible-study.json bookmarks
bible --study /tmp/bible-study.json note add "John 3:16" "Do not detach from context"
bible --study /tmp/bible-study.json notes
bible import-bundle tests/fixtures/asv_sample_bundle.json --db /tmp/bible.sqlite3
bible --db /tmp/bible.sqlite3 John 3:16
```

## Current development fixture

The app currently uses a tiny in-memory ASV fixture by default to prove the SQLite schema, reference parsing, rendering, import, search, navigation, comparison, and local study-data layers. The fixture currently includes Psalm 23:1-4, John 3:16-17, and Romans 8:28-30. Stage 6 adds explicit `--db` import/read commands for local ASV source or bundle files; a default installed user database will come later.

## Planning documents

- `PROJECT_SPEC.md`
- `docs/STAGES.md`
- `docs/WORKFLOW.md`
- `docs/TUI_PLAN.md`
- `docs/INSTALL.md`
- `docs/SMOKE_TEST.md`
- `docs/VERSIONING.md`
- `docs/DEV_ENVIRONMENT.md`
- `CHANGELOG.md`

## Data sources

See `docs/DATA_SOURCES.md` for translation import policy and the current ASV import bundle shape.

## Install preview

Development install:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest
python -m pytest
bible doctor
```

Future pipx/GitHub install:

```bash
pipx install git+ssh://git@github.com/ransom0/bible-reader.git
bible doctor
```

See `docs/INSTALL.md`, `docs/DEV_ENVIRONMENT.md`, and `docs/SMOKE_TEST.md` for fuller release checks.
