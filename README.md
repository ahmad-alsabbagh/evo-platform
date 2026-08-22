# Evo Platform 🚀

Enterprise-grade AI agent platform with governance, multi-agent orchestration, and **100% free LLM support**.

## 🎯 What You Get

| Feature | Description |
|---------|-------------|
| **🆓 Free LLM** | Ollama (local) or Groq (cloud) - no API key needed |
| **🤖 Multi-Agent** | Hierarchical orchestration with specialized sub-agents |
| **🔒 Governance** | Authorization tiers, human approval queue, audit trail |
| **💰 Cost Control** | Per-session budgets, circuit breakers |
| **🗄️ Persistent** | PostgreSQL-backed audit log (hash-chained) |
| **⚡ Production** | FastAPI, async, Docker-ready |

## 🚀 Quick Start (5 minutes)

### 1. Start Services

```bash
docker-compose up -d postgres ollama

# Pull Llama 3 model (one-time, ~4GB)
docker exec -it evo-platform-ollama ollama pull llama3
```

### 2. Apply Migrations

```bash
export DATABASE_URL=postgresql://evo:evo_dev_password@localhost:5432/evo_platform
alembic upgrade head
```

### 3. Install Dependencies

```bash
pip install -r requirements-lock.txt
```

### 4. Start Server

```bash
export DATABASE_URL=postgresql://evo:evo_dev_password@localhost:5432/evo_platform
export LLM_PROVIDER=ollama  # FREE, no API key!
export LLM_MODEL=llama3

uvicorn src.evo_platform.api.app:app --reload
```

### 5. Test

```bash
# Single agent
curl -X POST http://localhost:8000/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-support",
    "user_id": "user-123",
    "session_id": "test-1",
    "input": "How do I reset my password?",
    "authorization_tier": "ACT_AND_REPORT",
    "spending_cap_usd": 1.0
  }'

# Multi-agent orchestrator (auto-routes to specialist)
curl -X POST http://localhost:8000/v1/orchestrator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "session_id": "test-2",
    "input": "I need a refund for my last payment",
    "spending_cap_usd": 1.0
  }'
```

## 🤖 Multi-Agent Orchestration

The orchestrator automatically routes requests to specialized agents:

| Input Example | Routed To | Authorization |
|--------------|-----------|---------------|
| "I need a **refund**" | `billing-agent` | REQUIRE_APPROVAL |
| "There's a **bug**" | `technical-agent` | ACT_AND_REPORT |
| "Reset my **password**" | `account-agent` | ACT_AND_REPORT |
| "General question" | `general-agent` | ACT_AND_REPORT |

### Example: Refund Request Flow

```bash
# 1. User requests refund
curl -X POST http://localhost:8000/v1/orchestrator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-456",
    "session_id": "refund-123",
    "input": "Please refund my last payment",
    "spending_cap_usd": 1.0
  }'

# Response: {"success": false, "error": "Awaiting human approval: ..."}

# 2. List pending approvals
curl http://localhost:8000/v1/approvals/pending

# 3. Approve
curl -X POST http://localhost:8000/v1/approvals/{approval_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver": "admin@company.com", "note": "Verified"}'

# 4. Check audit trail
curl http://localhost:8000/v1/audit/session/refund-123
```

## 🆓 Free LLM Options

| Provider | Speed | Quality | API Key | Setup |
|----------|-------|---------|---------|-------|
| **Ollama** (default) | ⚡ Fast | Good | ❌ No | `docker-compose up -d ollama` |
| **Groq** | ⚡⚡ Fastest | Excellent | ✅ Free | Sign up at groq.com |

### Switch to Groq (Free Tier)

```bash
# Get free key from https://console.groq.com
export GROQ_API_KEY=gsk_your_key_here
export LLM_PROVIDER=groq
export LLM_MODEL=llama-3.1-70b-versatile
```

## 🔒 Governance Features

### Authorization Tiers

```python
ACT_AND_REPORT    # Execute immediately, log to audit
REQUIRE_APPROVAL  # Park in approval queue, wait for human
DENY              # Reject immediately
```

### Audit Trail

Every action is logged with:
- Hash chain (immutable, tamper-evident)
- Agent ID, user ID, session ID
- Authorization tier used
- Cost and token count
- Timestamp

```bash
# Verify chain integrity
curl http://localhost:8000/v1/audit/verify
# Response: {"chain_valid": true, "total_entries": 42}
```

## 📁 Project Structure

```
src/evo_platform/
├── api/                 # FastAPI endpoints
│   ├── app.py           # Main application
│   └── routes.py        # API routes
├── governance/          # Authorization, Audit, Approval
│   ├── authorization.py # Policy evaluation
│   ├── audit.py         # Hash-chained audit log
│   ├── approval.py      # Human approval queue
│   ├── models.py        # SQLAlchemy models
│   └── persistence.py   # PostgreSQL backend
├── harness/             # Agent execution engine
│   ├── runner.py        # Main execution loop
│   ├── contracts.py     # Data types
│   ├── cost_tracker.py  # Budget enforcement
│   ├── circuit_breaker.py # Failure isolation
│   ├── sandbox.py       # Code execution
│   └── credential_proxy.py # Secure auth
├── llm/                 # LLM providers
│   └── providers.py     # Ollama, Groq, OpenAI, Anthropic
├── orchestration/       # Multi-agent routing
│   └── hierarchical.py  # Orchestrator + sub-agents
├── storage/             # Database repositories
└── workers/             # Background jobs
```

## 🛠️ Development

```bash
# Run tests
pytest tests/

# Format code
black src/ tests/
ruff check src/ tests/

# View logs
docker-compose logs -f ollama
docker-compose logs -f postgres
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/agents/execute` | Execute single agent |
| POST | `/v1/orchestrator/execute` | Execute via orchestrator |
| GET | `/v1/approvals/pending` | List pending approvals |
| POST | `/v1/approvals/{id}/approve` | Approve action |
| POST | `/v1/approvals/{id}/deny` | Deny action |
| GET | `/v1/audit/session/{id}` | Get session audit trail |
| GET | `/v1/audit/verify` | Verify hash chain |

## 🎯 What's Next?

- [ ] Observability (Prometheus + Grafana)
- [ ] Rate limiting + quotas
- [ ] Python SDK + CLI
- [ ] Retrieval-as-subagent (RAG)
- [ ] Multi-turn conversations

## 📝 License

MIT
