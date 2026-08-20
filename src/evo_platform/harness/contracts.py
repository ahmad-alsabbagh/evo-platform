"""Agent Harness Contracts - Production-grade interfaces for agent execution."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class AuthorizationTier(Enum):
    """Graduated autonomy levels for AI agents (Singapore framework)."""
    OBSERVE = 0
    RECOMMEND = 1
    ACT_WITH_APPROVAL = 2
    ACT_AND_REPORT = 3


@dataclass
class MemoryContext:
    """Tiered memory system for agent context."""
    hot: List[Dict[str, Any]] = field(default_factory=list)
    warm: Optional[str] = None
    cold: List[Dict[str, Any]] = field(default_factory=list)
    session_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Structured tool contract with schema validation."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout_ms: int = 30000
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {"max_retries": 3, "backoff": "exponential"})
    idempotency_key: Optional[str] = None
    allowlist: Optional[List[str]] = None
    cost_estimate_usd: float = 0.001


@dataclass
class Guardrails:
    """Deterministic guardrails for agent execution."""
    spending_cap_usd: float = 1.0
    tool_allowlist: Optional[List[str]] = None
    tool_denylist: List[str] = field(default_factory=list)
    output_max_tokens: int = 2000
    pii_redaction: bool = True
    rate_limit_per_minute: int = 60
    allowed_domains: List[str] = field(default_factory=list)
    prohibited_actions: List[str] = field(default_factory=list)


@dataclass
class AgentContext:
    """Execution context for agent requests."""
    memory: MemoryContext = field(default_factory=MemoryContext)
    tools: List[ToolDefinition] = field(default_factory=list)
    authorization_tier: AuthorizationTier = AuthorizationTier.ACT_AND_REPORT
    guardrails: Guardrails = field(default_factory=Guardrails)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    compliance_flags: Dict[str, bool] = field(default_factory=dict)


@dataclass
class AgentRequest:
    """Request to execute an agent."""
    agent_id: str
    user_id: str
    session_id: str
    input: str
    context: AgentContext = field(default_factory=AgentContext)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if not self.agent_id:
            raise ValueError("agent_id is required")
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.input:
            raise ValueError("input is required")


@dataclass
class TokenUsage:
    """Token usage breakdown."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    model: str
    cost_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    """Result of a tool execution."""
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    retries: int = 0


@dataclass
class AgentResponse:
    """Response from agent execution."""
    request_id: str
    output: str
    tokens_used: TokenUsage
    latency_ms: float
    cost_usd: float
    success: bool
    error: Optional[str] = None
    audit_log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_calls: List[ToolCallResult] = field(default_factory=list)
    authorization_tier_used: AuthorizationTier = AuthorizationTier.ACT_AND_REPORT
    guardrails_triggered: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EvaluationExample:
    """Single example in a graded evaluation set."""
    id: str
    input: str
    expected_output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    scorers: Dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationSet:
    """Graded evaluation set for a capability."""
    capability_id: str
    capability_version: str
    examples: List[EvaluationExample]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    owner: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of running evaluation on a capability."""
    capability_id: str
    eval_set_id: str
    examples_run: int
    examples_passed: int
    pass_rate: float
    scores: Dict[str, float]
    failures: List[Dict[str, Any]]
    latency_p50_ms: float
    latency_p95_ms: float
    cost_total_usd: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Production thresholds (simplified for initial deployment)
PRODUCTION_THRESHOLDS = {
    "semantic_similarity": 0.85,
    "llm_judge_score": 2.0,  # Simplified heuristic threshold
    "response_time_ms": 2000,
    "helpfulness": 0.8,
    "accuracy": 0.9,
    "pass_rate": 0.80,
}

AUTHORIZATION_TIER_DESCRIPTIONS = {
    AuthorizationTier.OBSERVE: "Read-only, no execution - Dashboard monitoring",
    AuthorizationTier.RECOMMEND: "Suggests actions, human executes - Investment recommendations",
    AuthorizationTier.ACT_WITH_APPROVAL: "Executes pre-approved types, human approves new - Sending templated emails",
    AuthorizationTier.ACT_AND_REPORT: "Executes autonomously, logs everything - Scheduling meetings",
}
