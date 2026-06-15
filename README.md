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
```

## Planning documents

- `PROJECT_SPEC.md`
- `docs/STAGES.md`
- `docs/WORKFLOW.md`
