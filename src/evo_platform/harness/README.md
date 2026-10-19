# Agent Harness (Production Runtime)

The Agent Harness is the production runtime environment that wraps AI agents with enterprise-grade security, observability, and governance.

## Architecture

```
┌─────────────────────────────────────────────┐
│ Agent Harness (Production Runtime)         │
├─────────────────────────────────────────────┤
│ 1. API Gateway (auth, rate limiting, DDoS) │
│ 2. Context Manager (RAG, memory, session)  │
│ 3. Tool Proxy (circuit breakers, caching)  │
│ 4. Validation Layer (schema, guardrails)   │
│ 5. Observability (tracing, metrics, logs)  │
│ 6. Audit Trail (immutable, compliance)     │
└─────────────────────────────────────────────┘
```

## Key Principles

### 1. Sandboxed Execution

All agent code runs in isolated containers (E2B-powered) with:
- Filesystem isolation
- Network isolation (allowlist-only)
- Resource limits (CPU, memory, time)
- No access to host credentials

### 2. Credential Security

- Credentials never touch the sandbox
- Proxy layer intercepts all credential usage
- Virtual credentials per agent/session
- Automatic rotation and revocation

### 3. SSE Streaming

- Real-time token streaming to clients
- Progressive rendering
- Early cancellation support
- Cost tracking per token

### 4. Structured Tool Contracts

All tools must implement:
- Input/output JSON schemas
- Timeout limits
- Retry policies
- Circuit breaker integration
- Idempotency keys

## Components

### `contracts.py`

Defines the interface between agents and the harness:

```python
@dataclass
class AgentRequest:
    agent_id: str
    user_id: str
    session_id: str
    input: str
    context: AgentContext
    metadata: Dict[str, Any]

@dataclass
class AgentResponse:
    output: str
    tokens_used: int
    latency_ms: float
    cost_usd: float
    success: bool
    error: Optional[str]
    audit_log_id: str
```

### `runner.py` (Coming Soon)

Main execution engine:
- Sandbox provisioning
- Credential injection
- Tool proxying
- Streaming response
- Observability capture

### `eval_runner.py` (Coming Soon)

Evaluation harness:
- Load graded eval sets
- Execute agent on examples
- Compute scores (semantic, LLM-as-judge, custom)
- Generate reports
- Block deployments below thresholds

## Usage

```python
from evo_platform.harness.contracts import AgentRequest, AgentContext

# Create request
request = AgentRequest(
    agent_id="customer-support-agent",
    user_id="user-123",
    session_id="session-456",
    input="How do I reset my password?",
    context=AgentContext(
        memory=memory_context,
        tools=["knowledge_base", "account_lookup"],
        authorization_tier=AuthorizationTier.ACT_AND_REPORT
    ),
    metadata={"channel": "web-chat"}
)

# Execute (runner coming soon)
# response = await harness.execute(request)
```

## Security

### Authorization Tiers

| Tier | Autonomy | Example |
|---|---|---|
| **0: Observe** | Read-only, no execution | Dashboard monitoring |
| **1: Recommend** | Suggests actions, human executes | Investment recommendations |
| **2: Act with Approval** | Executes pre-approved types, human approves new | Sending templated emails |
| **3: Act and Report** | Executes autonomously, logs everything | Scheduling meetings |

### Guardrails

- Spending caps per agent/session
- Tool allowlists/denylists
- Output validation (schema, content)
- Rate limiting per user/agent
- PII detection and redaction

## Observability

All agent executions are traced with:
- Request/response payloads
- Token usage (input/output)
- Tool calls (success/failure)
- Latency breakdown
- Cost attribution
- User feedback (if provided)

Traces are exported to:
- OpenTelemetry collectors
- Prometheus (metrics)
- Structured logs (JSON)
- Immutable audit store (compliance)

## Next Steps

1. Implement `runner.py` with E2B sandbox integration
2. Add credential proxy layer
3. Implement SSE streaming
4. Add circuit breakers for tools
5. Implement eval runner with graded sets
6. Add cost tracking per execution
