# Versioning Guidance

The package version currently lives in two places:

- `pyproject.toml` under `[project].version`
- `src/bible_reader/__init__.py` as `__version__`

Before tagging a release, update both values together and run:

```bash
python -m pytest
python -m bible_reader --version
bible --version
```

Use semantic versioning once the project has releases:

- Patch version: bug fixes and documentation-only release polish.
- Minor version: backward-compatible commands or data-model additions.
- Major version: breaking CLI, storage, or import-format changes.

Pre-1.0 versions may still change quickly, but breaking changes should be documented in `CHANGELOG.md`.
