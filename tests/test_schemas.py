import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).parents[1] / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def test_all_schemas_are_draft_2020_12() -> None:
    for path in SCHEMA_DIR.glob("*.json"):
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)


def test_capability_minimal_fixture() -> None:
    schema = load_schema("capability.schema.json")
    fixture = {"id": "summarize", "version": "1.0.0"}
    errors = list(Draft202012Validator(schema).iter_errors(fixture))
    assert errors == []


def test_capability_rejects_missing_required_field() -> None:
    schema = load_schema("capability.schema.json")
    fixture = {"id": "summarize"}
    assert list(Draft202012Validator(schema).iter_errors(fixture))


def test_evaluation_minimal_fixture() -> None:
    schema = load_schema("evaluation.schema.json")
    fixture = {
        "id": "eval-001",
        "capability": {"id": "summarize", "version": "1.0.0"},
        "dataset": {"id": "golden", "version": "1.0.0", "split": "validation"},
        "evaluator": {"type": "deterministic", "version": "1.0.0"},
        "execution": {"timestamp": "2026-01-01T00:00:00Z", "status": "completed"},
        "result": {"metrics": {"accuracy": 1.0}, "promotion": "candidate"},
        "reproducibility": {"configHash": "sha256:test"},
    }
    assert list(Draft202012Validator(schema).iter_errors(fixture)) == []


def test_provenance_minimal_fixture() -> None:
    schema = load_schema("provenance.schema.json")
    fixture = {
        "sourceType": "original",
        "license": {"identifier": "Apache-2.0"},
        "createdAt": "2026-01-01T00:00:00Z",
    }
    assert list(Draft202012Validator(schema).iter_errors(fixture)) == []
