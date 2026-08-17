import json
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

SCHEMA_DIR = Path(__file__).parents[1] / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def validator() -> Draft202012Validator:
    schema = load_schema("evaluation-run.schema.json")
    resolver = RefResolver(
        "evaluation-run.schema.json",
        schema,
        store={"common.schema.json": load_schema("common.schema.json")},
    )
    return Draft202012Validator(schema, resolver=resolver)


def valid_fixture() -> dict:
    return {
        "schemaVersion": "1.0.0",
        "id": "eval-run:001",
        "capability": {"id": "summarize", "version": "1.0.0"},
        "dataset": {
            "id": "golden",
            "version": "1.0.0",
            "split": "validation",
            "hash": "sha256:" + "a" * 64,
        },
        "model": {"provider": "example", "name": "model", "version": "1"},
        "evaluator": {"type": "deterministic", "version": "1.0.0"},
        "execution": {
            "startedAt": "2026-01-01T00:00:00Z",
            "finishedAt": "2026-01-01T00:01:00Z",
            "status": "completed",
        },
        "outcome": {"metrics": {"accuracy": 0.9}, "promotion": "candidate"},
        "reproducibility": {
            "configHash": "sha256:" + "b" * 64,
            "recordedAt": "2026-01-01T00:01:00Z",
        },
    }


def test_evaluation_run_validates() -> None:
    assert list(validator().iter_errors(valid_fixture())) == []


def test_evaluation_run_requires_dataset_hash() -> None:
    fixture = valid_fixture()
    del fixture["dataset"]["hash"]
    assert list(validator().iter_errors(fixture))
