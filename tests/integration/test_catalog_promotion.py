import pytest

from evo_platform.catalog.models import CatalogEntry, PromotionDecision, PromotionState
from evo_platform.catalog.repository import SqlAlchemyCatalogRepository


@pytest.mark.integration
async def test_missing_evaluation_blocks_publication(session) -> None:
    entry = CatalogEntry(id="catalog:integration", capability_id="integration", capability_version="1.0.0", risk_level="low", quality={"evaluation_status":"passed","score":0.95,"reproducibility":0.95,"trust":0.9,"regression_status":"passed"}, license_identifier="Apache-2.0", provenance_source_type="original")
    decision = PromotionDecision(decision_id="00000000-0000-0000-0000-000000000001", idempotency_key="integration:missing-eval", state=PromotionState.promoted, reasons=[], policy_version="1.0.0", evaluation_run_id="missing")
    with pytest.raises(ValueError, match="evaluation_run_not_found"):
        await SqlAlchemyCatalogRepository(session).publish_if_promoted(entry, decision)
