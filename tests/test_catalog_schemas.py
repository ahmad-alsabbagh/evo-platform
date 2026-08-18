import json
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

SCHEMA_DIR = Path(__file__).parents[1] / "schemas"


def load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def validator(name: str) -> Draft202012Validator:
    schema = load(name)
    store = {path.name: load(path.name) for path in SCHEMA_DIR.glob("*.json")}
    return Draft202012Validator(schema, resolver=RefResolver(name, schema, store=store))


def test_taxonomy_valid() -> None:
    fixture = {
        "taxonomyVersion": "1.0.0",
        "category": "AI Agents",
        "slug": "ai-agents",
        "riskLevel": "medium",
    }
    assert list(validator("taxonomy.schema.json").iter_errors(fixture)) == []


def test_catalog_entry_valid() -> None:
    fixture = {
        "id": "catalog:summarize",
        "schemaVersion": "1.0.0",
        "title": "Summarizer",
        "capability": {"id": "summarize", "version": "1.0.0"},
        "taxonomy": {
            "taxonomyVersion": "1.0.0",
            "category": "AI",
            "slug": "ai",
            "riskLevel": "low",
        },
        "lifecycle": "evaluated",
        "quality": {"evaluationStatus": "passed", "score": 0.91},
        "license": {"identifier": "Apache-2.0"},
        "provenance": {
            "sourceType": "original",
            "createdAt": "2026-01-01T00:00:00Z",
        },
    }
    assert list(validator("catalog-entry.schema.json").iter_errors(fixture)) == []


def test_collection_rejects_empty_items() -> None:
    fixture = {
        "id": "collection:empty",
        "schemaVersion": "1.0.0",
        "name": "Empty",
        "kind": "catalog",
        "owner": "team",
        "items": [],
        "license": {"identifier": "Apache-2.0"},
        "provenance": {
            "sourceType": "original",
            "createdAt": "2026-01-01T00:00:00Z",
        },
    }
    assert list(validator("collection.schema.json").iter_errors(fixture))
