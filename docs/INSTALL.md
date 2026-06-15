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

Smoke check:

```bash
bible --help
bible --version
bible doctor
bible books
bible --no-color John 3:16
```

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
