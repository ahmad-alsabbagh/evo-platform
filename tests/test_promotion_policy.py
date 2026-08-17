from evo_platform.catalog.models import CatalogEntry
from evo_platform.catalog.policy import PromotionPolicy


def policy() -> PromotionPolicy:
    return PromotionPolicy(
        policy_version="1.0.0",
        minimum_score=0.9,
        minimum_reproducibility=0.9,
        minimum_trust=0.8,
        allowed_risk_levels={"low", "medium"},
        require_human_review_for={"medium"},
    )


def entry(**overrides) -> CatalogEntry:
    values = {
        "id": "catalog:summarize",
        "capability_id": "summarize",
        "capability_version": "1.0.0",
        "risk_level": "low",
        "quality": {
            "evaluation_status": "passed",
            "score": 0.95,
            "reproducibility": 0.95,
            "trust": 0.9,
            "regression_status": "passed",
        },
        "license_identifier": "Apache-2.0",
        "provenance_source_type": "original",
    }
    values.update(overrides)
    return CatalogEntry(**values)


def test_policy_promotes_qualified_entry() -> None:
    decision = policy().evaluate(entry())
    assert decision.allowed is True
    assert decision.target_lifecycle == "promoted"


def test_policy_rejects_regression_failure() -> None:
    quality = entry().quality.model_copy(update={"regression_status": "failed"})
    decision = policy().evaluate(entry(quality=quality))
    assert decision.allowed is False
    assert "regression_not_passed" in decision.reasons


def test_policy_requires_human_review_for_medium_risk() -> None:
    decision = policy().evaluate(entry(risk_level="medium"))
    assert decision.allowed is False
    assert "human_review_required" in decision.reasons
