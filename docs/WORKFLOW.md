# Workflow

This project uses the same general workflow as the `helpme` app, but remains a separate repository and codebase.

## Standard pass pattern

1. Start from `main`.
2. Create a small feature/stage branch.
3. Create a tarball and upload it for review.
4. Apply the returned patch with `patch -p1`.
5. Run the full test gate.
6. Commit and push the branch.
7. Merge to `main` with `--ff-only`.
8. Delete the local and remote stage branch.

## Branch start

```bash
git switch main
git pull --ff-only
git switch -c stage-name-here
```

## Create upload tarball

From `~/Code`:

```bash
tar -czf ~/Downloads/bible-reader-stage-name-start.tar.gz bible-reader
```

## Apply returned patch

From `~/Code/bible-reader`:

```bash
patch -p1 < ~/Downloads/bible-reader-stage-name.patch
```

## Test gate

The gate will grow as the app grows.

Initial editable-install gate:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest
python -m pytest
python -m bible_reader --help
python -m bible_reader --version
bible --help
bible --version
```

After the CLI exists:

```bash
python -m pytest
python -m bible_reader --help
python -m bible_reader --version
```

After the console script exists and the package is installed editable:

```bash
python -m pytest
bible --help
bible --version
```

Feature-specific smoke commands should be added in each stage.

## Commit and push branch

```bash
git status
git add .
git commit -m "Describe the stage change"
git push -u origin stage-name-here
```

## Merge and cleanup

```bash
git switch main
git pull --ff-only origin main
git merge --ff-only stage-name-here
git push origin main
git branch -d stage-name-here
git push origin --delete stage-name-here
git fetch --all --prune
git status
```

## Tarball naming convention

Use names like:

```text
bible-reader-stage0-project-spec-start.tar.gz
bible-reader-stage1-repo-scaffold-start.tar.gz
bible-reader-stage2-sqlite-fixture-start.tar.gz
```

Returned files should use matching names:

```text
bible-reader-stage0-project-spec.patch
bible-reader-stage0-project-spec-patched.tar.gz
```

## Local environment convention

Use a project-local virtual environment at `.venv/`. The repository includes `.envrc` for `direnv`; run `direnv allow` only after creating `.venv`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest
direnv allow
```

Patch tarballs should continue to exclude `.venv`, `.pytest_cache`, and `__pycache__`.
