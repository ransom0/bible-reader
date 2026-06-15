"""Default local data helpers for bible-reader."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from .asv_sources import convert_asv_source_to_bundle
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
    usfx_source_path: str | Path | None = None,
    force: bool = False,
) -> Path:
    """Create or replace a local Bible database and import ASV data.

    If both source paths are omitted, the packaged ASV sample bundle is
    imported. Use ``source_path`` for normalized JSON bundles and
    ``usfx_source_path`` for local ASV USFX XML/zip sources.
    """
    if source_path is not None and usfx_source_path is not None:
        raise ImportErrorDetail("Choose either source_path or usfx_source_path, not both.")

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
        if usfx_source_path is not None:
            bundle = convert_asv_source_to_bundle(usfx_source_path)
            import_translation_bundle(connection, bundle)
        elif source_path is not None:
            # Validate before writing; this path loads JSON only and never executes input.
            bundle = load_translation_bundle(source_path)
            import_translation_bundle(connection, bundle)
        else:
            import_translation_bundle(connection, load_packaged_sample_bundle())
    finally:
        connection.close()
    return target
