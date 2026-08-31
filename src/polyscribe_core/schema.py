"""JSON Schema 加载与校验。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from polyscribe_core.io import read_json
from polyscribe_core.paths import Layout, resolve_layout


@lru_cache(maxsize=16)
def load_schema(name: str, schemas_dir: str) -> dict[str, Any]:
    path = Path(schemas_dir) / f"{name}.schema.json"
    return read_json(path)


def validate_document(name: str, document: dict[str, Any], layout: Layout | None = None) -> None:
    resolved = layout or resolve_layout()
    schema = load_schema(name, str(resolved.schemas))
    Draft202012Validator(schema).validate(document)
