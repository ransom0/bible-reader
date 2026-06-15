# Install and Update Notes

## Development install

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest
python -m pytest
```

Optional direnv setup, after `.venv` exists:

```bash
direnv allow
```

Smoke check:

```bash
bible --help
bible --version
bible doctor
bible books
bible --no-color John 3:16
```

See `docs/DEV_ENVIRONMENT.md` for the full local development workflow.

## pipx install from GitHub

After the project is pushed to GitHub, a local machine with `pipx` can install from the repository:

```bash
pipx install git+ssh://git@github.com/ransom0/bible-reader.git
bible --version
bible doctor
```

For HTTPS instead of SSH:

```bash
pipx install git+https://github.com/ransom0/bible-reader.git
```

## Update a pipx install

```bash
pipx upgrade bible-reader
bible doctor
```

## Local data policy

Current early-stage commands do not silently create a default Bible database. Explicit imports require `--db PATH`.

Study data is separate from Bible text. By default, user notes/bookmarks are stored under the platform user-data directory. Use `--study PATH` for an explicit study file during testing.


## Local database initialization

Create the default local SQLite database after installing:

```bash
bible init-db
bible doctor
bible John 3:16
```

By default, this initializes the packaged ASV sample bundle at `~/.local/share/bible-reader/bible-reader.sqlite3` unless `XDG_DATA_HOME` is set. Use `--db PATH` to target another SQLite file. Use `--force` only when you intentionally want to replace the target database.


## Full ASV source import

Download the public-domain ASV USFX zip from eBible, then initialize the default
local SQLite database from that local file:

```bash
mkdir -p ~/Downloads/bible-sources
curl -L -o ~/Downloads/bible-sources/eng-asv_usfx.zip \
  https://ebible.org/scriptures/eng-asv_usfx.zip
bible init-db --force --usfx-source ~/Downloads/bible-sources/eng-asv_usfx.zip
bible doctor
bible Genesis 1:1
```

The app does not commit or ship generated SQLite databases. Rebuild the local DB
from the public-domain source file whenever needed.
