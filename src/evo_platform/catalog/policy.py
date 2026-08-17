from evo_platform.catalog.models import CatalogEntry, PromotionDecision


class PromotionPolicy:
    def __init__(
        self,
        *,
        policy_version: str,
        minimum_score: float,
        minimum_reproducibility: float,
        minimum_trust: float,
        allowed_risk_levels: set[str],
        require_human_review_for: set[str] | None = None,
        require_regression_pass: bool = True,
        require_license: bool = True,
        require_provenance: bool = True,
    ) -> None:
        self.policy_version = policy_version
        self.minimum_score = minimum_score
        self.minimum_reproducibility = minimum_reproducibility
        self.minimum_trust = minimum_trust
        self.allowed_risk_levels = allowed_risk_levels
        self.require_human_review_for = require_human_review_for or set()
        self.require_regression_pass = require_regression_pass
        self.require_license = require_license
        self.require_provenance = require_provenance

    def evaluate(self, entry: CatalogEntry) -> PromotionDecision:
        reasons: list[str] = []
        quality = entry.quality
        if quality.evaluation_status != "passed":
            reasons.append("evaluation_not_passed")
        if quality.score is None or quality.score < self.minimum_score:
            reasons.append("score_below_threshold")
        if quality.reproducibility is None or quality.reproducibility < self.minimum_reproducibility:
            reasons.append("reproducibility_below_threshold")
        if quality.trust is None or quality.trust < self.minimum_trust:
            reasons.append("trust_below_threshold")
        if entry.risk_level not in self.allowed_risk_levels:
            reasons.append("risk_level_not_allowed")
        if self.require_regression_pass and quality.regression_status != "passed":
            reasons.append("regression_not_passed")
        if self.require_license and not entry.license_identifier:
            reasons.append("license_missing")
        if self.require_provenance and not entry.provenance_source_type:
            reasons.append("provenance_missing")
        if entry.risk_level in self.require_human_review_for and not entry.human_reviewed:
            reasons.append("human_review_required")
        allowed = not reasons
        return PromotionDecision(
            allowed=allowed,
            target_lifecycle="promoted" if allowed else "rejected",
            reasons=reasons,
            policy_version=self.policy_version,
        )
