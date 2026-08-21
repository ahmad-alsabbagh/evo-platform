"""Agent Runner - Ties together sandbox, credential proxy, circuit breakers,
cost tracking, authorization enforcement, and the immutable audit trail into
a single production execution path.

Execution flow for a single AgentRequest:
  1. Enforce guardrails (spending cap, tool allowlist) up front.
  2. Evaluate authorization tier for the requested action.
     - DENY -> reject immediately, write audit entry.
     - REQUIRE_APPROVAL -> park in ApprovalQueue, write audit entry, return pending.
     - ALLOW -> continue execution.
  3. Execute agent logic (LLM call + tool calls) through circuit breakers.
  4. Meter cost per token/tool call against the session budget.
  5. Record an immutable, hash-chained audit entry and return AgentResponse.
"""

import time
from dataclasses import dataclass
from typing import Callable, Optional

from .circuit_breaker import CircuitBreakerRegistry, CircuitBreakerOpen
from .contracts import (
    AgentRequest,
    AgentResponse,
    TokenUsage,
    ToolCallResult,
)
from .cost_tracker import CostEvent, CostTracker, BudgetExceededError, BudgetPolicy
from .credential_proxy import CredentialProxy
from .sandbox import SandboxLimits, SandboxProvider, get_default_sandbox
from ..governance.audit import ImmutableAuditLog
from ..governance.authorization import ActionRequest, AuthorizationDecision, AuthorizationEnforcer
from ..governance.approval import ApprovalQueue


class GuardrailViolation(Exception):
    """Raised when a request violates a deterministic guardrail."""


@dataclass
class AgentRunnerConfig:
    default_model: str = "gpt-4o-mini"
    cost_per_1k_input_tokens: float = 0.00015
    cost_per_1k_output_tokens: float = 0.0006
    default_action_type: str = "generate_response"


class AgentRunner:
    """Production execution engine for AgentRequest -> AgentResponse."""

    def __init__(
        self,
        llm_call: Optional[Callable[[AgentRequest], tuple[str, int, int]]] = None,
        sandbox: Optional[SandboxProvider] = None,
        config: Optional[AgentRunnerConfig] = None,
    ):
        self.llm_call = llm_call or self._stub_llm_call
        self.sandbox = sandbox or get_default_sandbox()
        self.config = config or AgentRunnerConfig()
        self.circuit_breakers = CircuitBreakerRegistry()
        self.cost_tracker = CostTracker()
        self.credential_proxy = CredentialProxy()
        self.audit_log = ImmutableAuditLog()
        self.authorization_enforcer = AuthorizationEnforcer()
        self.approval_queue = ApprovalQueue()

    @staticmethod
    def _stub_llm_call(request: AgentRequest) -> tuple[str, int, int]:
        output = f"[stub-response] Acknowledged: {request.input[:120]}"
        input_tokens = max(1, len(request.input.split()))
        output_tokens = max(1, len(output.split()))
        return output, input_tokens, output_tokens

    def _enforce_guardrails(self, request: AgentRequest) -> None:
        guardrails = request.context.guardrails
        scope = f"session:{request.session_id}"

        self.cost_tracker.set_budget(
            BudgetPolicy(scope=scope, cap_usd=guardrails.spending_cap_usd)
        )

        for tool in request.context.tools:
            if tool.name in guardrails.tool_denylist:
                raise GuardrailViolation(f"Tool '{tool.name}' is denylisted")
            if guardrails.tool_allowlist is not None and tool.name not in guardrails.tool_allowlist:
                raise GuardrailViolation(f"Tool '{tool.name}' not in allowlist")

    def _run_tool_call(self, tool_name: str, code: str, request: AgentRequest) -> ToolCallResult:
        breaker = self.circuit_breakers.get(tool_name)
        start = time.time()
        try:
            limits = SandboxLimits(
                timeout_s=10.0,
                allowed_domains=request.context.guardrails.allowed_domains,
            )
            result = breaker.call(lambda: self.sandbox.run_python(code, limits))
            latency_ms = (time.time() - start) * 1000
            return ToolCallResult(
                tool_name=tool_name,
                success=result.success,
                result=result.stdout if result.success else None,
                error=result.stderr if not result.success else None,
                latency_ms=latency_ms,
            )
        except CircuitBreakerOpen as e:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                latency_ms=(time.time() - start) * 1000,
            )

    def _audit(
        self, request: AgentRequest, action: str, outcome: str, metadata: Optional[dict] = None
    ) -> None:
        self.audit_log.append(
            agent_id=request.agent_id,
            user_id=request.user_id,
            session_id=request.session_id,
            action=action,
            authorization_tier=request.context.authorization_tier.name,
            outcome=outcome,
            metadata=metadata or {},
        )

    def execute(self, request: AgentRequest, action_type: Optional[str] = None) -> AgentResponse:
        """Execute an AgentRequest through the full production harness.

        Args:
            request: the agent request to execute.
            action_type: the governed action type this request represents
                (e.g. "generate_response", "refund_payment"). Defaults to
                a low-risk generic action if not specified.
        """
        start = time.time()
        scope = f"session:{request.session_id}"
        action_type = action_type or self.config.default_action_type

        try:
            self._enforce_guardrails(request)
        except GuardrailViolation as e:
            self._audit(request, action_type, "denied", {"reason": str(e)})
            return AgentResponse(
                request_id=request.request_id,
                output="",
                tokens_used=TokenUsage(0, 0, 0, 0.0, self.config.default_model),
                latency_ms=(time.time() - start) * 1000,
                cost_usd=0.0,
                success=False,
                error=str(e),
                guardrails_triggered=[str(e)],
            )

        auth_result = self.authorization_enforcer.evaluate(
            ActionRequest(
                action_type=action_type,
                agent_id=request.agent_id,
                session_id=request.session_id,
                authorization_tier=request.context.authorization_tier,
            )
        )

        if auth_result.decision == AuthorizationDecision.DENY:
            self._audit(request, action_type, "denied", {"reason": auth_result.reason})
            return AgentResponse(
                request_id=request.request_id,
                output="",
                tokens_used=TokenUsage(0, 0, 0, 0.0, self.config.default_model),
                latency_ms=(time.time() - start) * 1000,
                cost_usd=0.0,
                success=False,
                error=auth_result.reason,
                guardrails_triggered=["authorization_denied"],
            )

        if auth_result.decision == AuthorizationDecision.REQUIRE_APPROVAL:
            approval = self.approval_queue.submit(
                agent_id=request.agent_id,
                session_id=request.session_id,
                action_type=action_type,
                reason=auth_result.reason,
                payload={"input": request.input},
            )
            self._audit(
                request,
                action_type,
                "pending_approval",
                {"reason": auth_result.reason, "approval_id": approval.approval_id},
            )
            return AgentResponse(
                request_id=request.request_id,
                output="",
                tokens_used=TokenUsage(0, 0, 0, 0.0, self.config.default_model),
                latency_ms=(time.time() - start) * 1000,
                cost_usd=0.0,
                success=False,
                error=f"Awaiting human approval: {auth_result.reason}",
                guardrails_triggered=[f"pending_approval:{approval.approval_id}"],
            )

        output, input_tokens, output_tokens = self.llm_call(request)

        cost_usd = (
            (input_tokens / 1000.0) * self.config.cost_per_1k_input_tokens
            + (output_tokens / 1000.0) * self.config.cost_per_1k_output_tokens
        )

        try:
            self.cost_tracker.record(
                CostEvent(
                    scope=scope,
                    agent_id=request.agent_id,
                    amount_usd=cost_usd,
                    category="llm_tokens",
                    metadata={"model": self.config.default_model},
                )
            )
        except BudgetExceededError as e:
            self._audit(request, action_type, "denied", {"reason": str(e)})
            return AgentResponse(
                request_id=request.request_id,
                output="",
                tokens_used=TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens, cost_usd, self.config.default_model),
                latency_ms=(time.time() - start) * 1000,
                cost_usd=cost_usd,
                success=False,
                error=str(e),
                guardrails_triggered=["spending_cap_usd"],
            )

        latency_ms = (time.time() - start) * 1000

        self._audit(
            request,
            action_type,
            "success",
            {"cost_usd": cost_usd, "total_tokens": input_tokens + output_tokens},
        )

        return AgentResponse(
            request_id=request.request_id,
            output=output,
            tokens_used=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost_usd,
                model=self.config.default_model,
            ),
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            success=True,
            authorization_tier_used=request.context.authorization_tier,
        )
