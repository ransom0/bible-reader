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
bible init-db
bible tui
bible chapters John
bible chapters Ps
bible --no-color Ps 23
bible --study /tmp/bible-study.json bookmark add John 3:16 --label Gospel
bible --study /tmp/bible-study.json bookmarks
bible --study /tmp/bible-study.json note add "John 3:16" "Do not detach from context"
bible --study /tmp/bible-study.json notes
bible init-db
bible John 3:16
bible import-bundle tests/fixtures/asv_sample_bundle.json --db /tmp/bible.sqlite3
bible import-usfx ~/Downloads/bible-sources/eng-asv_usfx.zip --db /tmp/asv.sqlite3
bible init-db --force --usfx-source ~/Downloads/bible-sources/eng-asv_usfx.zip
bible --db /tmp/bible.sqlite3 John 3:16
```

## Current development fixture

The app uses a tiny in-memory ASV fixture when no default database exists. The fixture includes Psalm 23:1-4, John 3:16-17, and Romans 8:28-30. `bible init-db` creates a default local SQLite database at the XDG data path. By default that database is bootstrapped from the packaged ASV sample bundle; use `bible init-db --force --usfx-source ~/Downloads/bible-sources/eng-asv_usfx.zip` to build the default database from a full local ASV USFX source archive.

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
