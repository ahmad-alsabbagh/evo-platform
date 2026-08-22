"""Authorization Tier Enforcement - Graduated autonomy for AI agents.

Singapore PDPC-style tiering model:
  0 OBSERVE            - read-only, no side effects allowed
  1 RECOMMEND          - agent suggests, human must execute
  2 ACT_WITH_APPROVAL  - auto-executes pre-approved action types; else needs sign-off
  3 ACT_AND_REPORT     - agent executes autonomously, logs everything for review
"""

from dataclasses import dataclass, field
from typing import Optional, Set

from ..harness.contracts import AuthorizationTier


@dataclass
class ActionRequest:
    action_type: str
    agent_id: str
    session_id: str
    authorization_tier: AuthorizationTier
    pre_approved_action_types: Set[str] = field(default_factory=set)
    amount_usd: Optional[float] = None
    high_risk_threshold_usd: float = 100.0


class AuthorizationDecision:
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class AuthorizationResult:
    decision: str
    reason: str


class AuthorizationEnforcer:
    """Decides ALLOW / DENY / REQUIRE_APPROVAL for a given action request."""

    ALWAYS_REQUIRE_APPROVAL: Set[str] = {
        "delete_account",
        "refund_payment",
        "export_all_data",
        "modify_permissions",
    }

    def evaluate(self, request: ActionRequest) -> AuthorizationResult:
        tier = request.authorization_tier

        if request.action_type in self.ALWAYS_REQUIRE_APPROVAL:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_APPROVAL,
                f"Action '{request.action_type}' always requires human approval",
            )

        if tier == AuthorizationTier.OBSERVE:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                "Tier 0 (OBSERVE) permits no side-effecting actions",
            )

        if tier == AuthorizationTier.RECOMMEND:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_APPROVAL,
                "Tier 1 (RECOMMEND) requires human to execute any action",
            )

        if request.amount_usd is not None and request.amount_usd > request.high_risk_threshold_usd:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_APPROVAL,
                f"Amount ${request.amount_usd:.2f} exceeds high-risk threshold "
                f"${request.high_risk_threshold_usd:.2f}",
            )

        if tier == AuthorizationTier.ACT_WITH_APPROVAL:
            if request.action_type in request.pre_approved_action_types:
                return AuthorizationResult(
                    AuthorizationDecision.ALLOW,
                    f"Action '{request.action_type}' is pre-approved for Tier 2",
                )
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_APPROVAL,
                f"Action '{request.action_type}' not in pre-approved set for Tier 2",
            )

        if tier == AuthorizationTier.ACT_AND_REPORT:
            return AuthorizationResult(
                AuthorizationDecision.ALLOW,
                "Tier 3 (ACT_AND_REPORT) permits autonomous execution with full logging",
            )

        return AuthorizationResult(AuthorizationDecision.DENY, "Unrecognized authorization tier")
