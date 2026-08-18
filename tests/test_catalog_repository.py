from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from evo_platform.catalog.models import CatalogEntry, PromotionDecision, PromotionState
from evo_platform.catalog.repository import SqlAlchemyCatalogRepository


def make_entry() -> CatalogEntry:
    return CatalogEntry(
        id="catalog:summarize",
        capability_id="summarize",
        capability_version="1.0.0",
        risk_level="low",
        quality={
            "evaluation_status": "passed",
            "score": 0.95,
            "reproducibility": 0.95,
            "trust": 0.9,
            "regression_status": "passed",
        },
        license_identifier="Apache-2.0",
        provenance_source_type="original",
    )


def make_decision(*, evaluation_run_id: str = "eval-run:1") -> PromotionDecision:
    return PromotionDecision(
        decision_id=uuid4(),
        idempotency_key=f"publish:{evaluation_run_id}",
        state=PromotionState.promoted,
        reasons=[],
        policy_version="1.0.0",
        evaluation_run_id=evaluation_run_id,
    )


@pytest.mark.asyncio
async def test_publish_requires_matching_evaluation() -> None:
    session = AsyncMock()
    session.get.return_value = None
    repository = SqlAlchemyCatalogRepository(session)

    with pytest.raises(ValueError, match="evaluation_run_not_found"):
        await repository.publish_if_promoted(make_entry(), make_decision())


@pytest.mark.asyncio
async def test_rejected_decision_does_not_publish() -> None:
    session = AsyncMock()
    repository = SqlAlchemyCatalogRepository(session)
    decision = make_decision()
    decision.state = PromotionState.rejected

    with pytest.raises(ValueError, match="promoted decision"):
        await repository.publish_if_promoted(make_entry(), decision)
    session.add.assert_not_called()
