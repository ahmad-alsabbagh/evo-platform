import json
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

SCHEMA_DIR = Path(__file__).parents[1] / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def validator(name: str) -> Draft202012Validator:
    schema = load_schema(name)
    store = {path.name: load_schema(path.name) for path in SCHEMA_DIR.glob("*.json")}
    return Draft202012Validator(schema, resolver=RefResolver(name, schema, store=store))


def test_capability_requires_contract_fields() -> None:
    schema = load_schema("capability.schema.json")
    fixture = {"id": "summarize", "version": "1.0.0"}
    assert list(Draft202012Validator(schema).iter_errors(fixture))


def test_experiment_schema_resolves_defs() -> None:
    fixture = {
        "id": "experiment:summarize",
        "schemaVersion": "1.0.0",
        "hypothesis": "better groundedness",
        "baseline": {"capabilityId": "summarize", "version": "1.0.0"},
        "variants": [{"capabilityId": "summarize", "version": "1.1.0"}],
        "primaryMetric": "groundedness",
        "guardrails": {
            "maxSafetyViolations": 0,
            "maxCostIncrease": 0.1,
            "maxP95LatencyIncrease": 0.2,
        },
        "trafficPlan": {"mode": "shadow", "steps": [1, 5], "rollbackOn": ["safety_regression"]},
    }
    assert list(validator("experiment.schema.json").iter_errors(fixture)) == []
