"""Agent Harness Contracts - Production-grade interfaces for agent execution.

This module defines the core contracts between agents and the harness,
including request/response schemas, authorization tiers, and execution context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class AuthorizationTier(Enum):
    """Graduated autonomy levels for AI agents (Singapore framework).
    
    Reference: https://www.pdpc.gov.sg/ai-governance
    """
    OBSERVE = 0  # Read-only, no execution
    RECOMMEND = 1  # Suggests actions, human executes
    ACT_WITH_APPROVAL = 2  # Executes pre-approved types, human approves new
    ACT_AND_REPORT = 3  # Executes autonomously, logs everything


@dataclass
class MemoryContext:
    """Tiered memory system for agent context.
    
    Attributes:
        hot: Last 3-5 conversation turns (in-memory deque)
        warm: Compressed summary of earlier conversation
        cold: Semantic retrieval from long-term vector store
        session_metadata: Session-level metadata (user_id, created_at, etc.)
    """
    hot: List[Dict[str, Any]] = field(default_factory=list)
    warm: Optional[str] = None
    cold: List[Dict[str, Any]] = field(default_factory=list)
    session_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Structured tool contract with schema validation.
    
    Attributes:
        name: Unique tool identifier
        description: Human-readable description
        input_schema: JSON Schema for input validation
        output_schema: JSON Schema for output validation
        timeout_ms: Maximum execution time in milliseconds
        retry_policy: Retry configuration (max_retries, backoff)
        idempotency_key: Optional idempotency key for deduplication
        allowlist: Optional URL/resource allowlist for network calls
        cost_estimate_usd: Estimated cost per execution
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout_ms: int = 30000
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "backoff": "exponential"
    })
    idempotency_key: Optional[str] = None
    allowlist: Optional[List[str]] = None
    cost_estimate_usd: float = 0.001


@dataclass
class Guardrails:
    """Deterministic guardrails for agent execution.
    
    Attributes:
        spending_cap_usd: Maximum cost per execution
        tool_allowlist: Allowed tool names (None = all allowed)
        tool_denylist: Denied tool names (takes precedence over allowlist)
        output_max_tokens: Maximum tokens in output
        pii_redaction: Whether to redact PII from outputs
        rate_limit_per_minute: Maximum executions per minute
        allowed_domains: URL domains allowed for network calls
        prohibited_actions: List of prohibited action types
    """
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
    """Execution context for agent requests.
    
    Attributes:
        memory: Tiered memory system
        tools: List of available tools
        authorization_tier: Agent autonomy level
        guardrails: Deterministic guardrails
        user_preferences: User-specific preferences
        compliance_flags: Compliance-related flags (GDPR, HIPAA, etc.)
    """
    memory: MemoryContext = field(default_factory=MemoryContext)
    tools: List[ToolDefinition] = field(default_factory=list)
    authorization_tier: AuthorizationTier = AuthorizationTier.ACT_AND_REPORT
    guardrails: Guardrails = field(default_factory=Guardrails)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    compliance_flags: Dict[str, bool] = field(default_factory=dict)


@dataclass
class AgentRequest:
    """Request to execute an agent.
    
    Attributes:
        request_id: Unique request identifier (auto-generated)
        agent_id: Agent identifier
        user_id: User identifier
        session_id: Session identifier for conversation continuity
        input: User input/prompt
        context: Execution context (memory, tools, guardrails)
        metadata: Additional metadata (channel, locale, etc.)
        created_at: Request timestamp (auto-generated)
    """
    agent_id: str
    user_id: str
    session_id: str
    input: str
    context: AgentContext = field(default_factory=AgentContext)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate request after initialization."""
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
    """Token usage breakdown.
    
    Attributes:
        input_tokens: Tokens in input/prompt
        output_tokens: Tokens in output/completion
        total_tokens: Total tokens used
        cost_usd: Total cost in USD
        model: Model identifier
        cost_breakdown: Detailed cost breakdown by component
    """
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    model: str
    cost_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    """Result of a tool execution.
    
    Attributes:
        tool_name: Tool identifier
        success: Whether execution succeeded
        result: Tool output (if successful)
        error: Error message (if failed)
        latency_ms: Execution time in milliseconds
        cost_usd: Cost of execution
        retries: Number of retry attempts
    """
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    retries: int = 0


@dataclass
class AgentResponse:
    """Response from agent execution.
    
    Attributes:
        request_id: Reference to original request
        output: Agent output/response
        tokens_used: Token usage breakdown
        latency_ms: Total execution time in milliseconds
        cost_usd: Total cost in USD
        success: Whether execution succeeded
        error: Error message (if failed)
        audit_log_id: Immutable audit log identifier
        tool_calls: List of tool calls made during execution
        authorization_tier_used: Authorization tier used for execution
        guardrails_triggered: List of triggered guardrails
        created_at: Response timestamp (auto-generated)
    """
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
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvaluationExample:
    """Single example in a graded evaluation set.
    
    Attributes:
        id: Unique example identifier
        input: Input prompt
        expected_output: Expected output (golden)
        metadata: Example metadata (difficulty, category, tags)
        scorers: Expected scores for each metric
    """
    id: str
    input: str
    expected_output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    scorers: Dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationSet:
    """Graded evaluation set for a capability.
    
    Attributes:
        capability_id: Capability identifier
        capability_version: Capability version
        examples: List of evaluation examples
        created_at: Creation timestamp
        updated_at: Last update timestamp
        owner: Owner identifier
        metadata: Additional metadata (target examples, distribution, etc.)
    """
    capability_id: str
    capability_version: str
    examples: List[EvaluationExample]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    owner: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of running evaluation on a capability.
    
    Attributes:
        capability_id: Capability identifier
        eval_set_id: Evaluation set identifier
        examples_run: Number of examples executed
        examples_passed: Number of examples passing thresholds
        pass_rate: Overall pass rate (0.0-1.0)
        scores: Score breakdown by metric
        failures: List of failed examples with details
        latency_p50_ms: Median latency
        latency_p95_ms: 95th percentile latency
        cost_total_usd: Total cost of evaluation
        created_at: Evaluation timestamp
    """
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
    created_at: datetime = field(default_factory=datetime.utcnow)


# Production thresholds (from best practices)
PRODUCTION_THRESHOLDS = {
    "semantic_similarity": 0.85,
    "llm_judge_score": 4.0,
    "response_time_ms": 2000,
    "helpfulness": 0.8,
    "accuracy": 0.9,
    "pass_rate": 0.95,
}

# Authorization tier descriptions
AUTHORIZATION_TIER_DESCRIPTIONS = {
    AuthorizationTier.OBSERVE: "Read-only, no execution - Dashboard monitoring",
    AuthorizationTier.RECOMMEND: "Suggests actions, human executes - Investment recommendations",
    AuthorizationTier.ACT_WITH_APPROVAL: "Executes pre-approved types, human approves new - Sending templated emails",
    AuthorizationTier.ACT_AND_REPORT: "Executes autonomously, logs everything - Scheduling meetings",
}
