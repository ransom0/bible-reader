# Development Environment

This project can be used with a manual virtual environment or with `direnv`.

## One-time setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest
```

## Enable direnv

After `.venv` exists, allow the checked-in `.envrc`:

```bash
direnv allow
```

Then leaving and re-entering the repository should automatically activate `.venv` and expose the source tree:

```bash
cd ~
cd ~/Code/bible-reader
which python
which bible
bible --version
```

## What `.envrc` does

The `.envrc` file:

- sources `.venv/bin/activate` when `.venv` exists;
- exports `PYTHONPATH="$PWD/src"` so local source imports work consistently;
- does not create, download, or execute project dependencies by itself.

That keeps setup explicit and avoids surprising shell behavior.

## Normal development test gate

```bash
python -m pip install -e . pytest
python -m pytest
python -m bible_reader --help
python -m bible_reader --version
bible --help
bible --version
bible doctor
```
