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

After editable install, the console command is available:

```bash
bible --help
bible --version
bible books
bible John 3:16
bible read John 3
bible --no-color Ps 23
```

## Current development fixture

The app currently uses a tiny in-memory ASV fixture to prove the SQLite schema, reference parsing, and rendering layers before importing a full Bible text. The fixture currently includes Psalm 23:1-4, John 3:16-17, and Romans 8:28-30.

## Planning documents

- `PROJECT_SPEC.md`
- `docs/STAGES.md`
- `docs/WORKFLOW.md`

## Data sources

See `docs/DATA_SOURCES.md` for translation import policy and the current ASV import bundle shape.

