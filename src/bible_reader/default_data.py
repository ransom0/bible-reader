"""Default local data helpers for bible-reader."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from .importers import ImportErrorDetail, import_translation_bundle, import_translation_bundle_file, load_translation_bundle
from .storage import connect_database, default_database_path, initialize_database

SAMPLE_BUNDLE_RESOURCE = "asv_sample_bundle.json"


def load_packaged_sample_bundle() -> dict[str, Any]:
    """Load the packaged ASV sample bundle used for default DB bootstrapping."""
    resource = resources.files("bible_reader.data").joinpath(SAMPLE_BUNDLE_RESOURCE)
    try:
        return json.loads(resource.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ImportErrorDetail("Packaged ASV sample bundle contains invalid JSON.") from exc
    except OSError as exc:
        raise ImportErrorDetail("Could not read packaged ASV sample bundle.") from exc


def initialize_default_database(
    *,
    db_path: str | Path | None = None,
    source_path: str | Path | None = None,
    force: bool = False,
) -> Path:
    """Create or replace a local Bible database and import ASV data.

    If ``source_path`` is omitted, the packaged ASV sample bundle is imported.
    Later full-ASV stages can reuse this function with a real local source file.
    """
    target = Path(db_path) if db_path is not None else default_database_path()
    target = target.expanduser()
    if target.exists() and not force:
        raise ImportErrorDetail(
            f"Database already exists: {target}. Use --force to replace it."
        )
    target.parent.mkdir(parents=True, exist_ok=True)

    if force and target.exists():
        target.unlink()

    connection = connect_database(target)
    try:
        initialize_database(connection)
        if source_path is None:
            import_translation_bundle(connection, load_packaged_sample_bundle())
        else:
            # Validate before writing; this path loads JSON only and never executes input.
            bundle = load_translation_bundle(source_path)
            import_translation_bundle(connection, bundle)
    finally:
        connection.close()
    return target
