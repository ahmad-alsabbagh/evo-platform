# Evo Platform - Production AI Agent Harness

Enterprise-grade AI agent platform with governance, cost control, and free LLM support.

## 🚀 Quick Start (FREE)

### 1. Start PostgreSQL + Ollama (FREE LLM)

```bash
docker-compose up -d postgres ollama

# Pull Llama 3 model (first time only)
docker exec -it evo-platform-ollama ollama pull llama3
```

### 2. Apply Migrations

```bash
export DATABASE_URL=postgresql://evo:evo_dev_password@localhost:5432/evo_platform
alembic upgrade head
```

### 3. Start Server

```bash
export DATABASE_URL=postgresql://evo:evo_dev_password@localhost:5432/evo_platform
export LLM_PROVIDER=ollama  # FREE, no API key!
export LLM_MODEL=llama3

uvicorn src.evo_platform.api.app:app --reload
```

### 4. Test

```bash
curl -X POST http://localhost:8000/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-support-agent",
    "user_id": "user-123",
    "session_id": "session-1",
    "input": "How do I reset my password?",
    "action_type": "generate_response",
    "authorization_tier": "ACT_AND_REPORT",
    "spending_cap_usd": 1.0
  }'
```

## 🆓 Free LLM Options

| Provider | Speed | Quality | API Key | Setup |
|----------|-------|---------|---------|-------|
| **Ollama** (default) | Fast | Good | ❌ No | `docker-compose up -d ollama` |
| **Groq** | ⚡ Fastest | Excellent | ✅ Free | Sign up at groq.com |
| OpenAI | Fast | Excellent | ✅ Paid | - |
| Anthropic | Fast | Excellent | ✅ Paid | - |

### Using Groq (FREE tier)

```bash
# Get free API key from https://console.groq.com
export GROQ_API_KEY=gsk_your_key_here
export LLM_PROVIDER=groq
export LLM_MODEL=llama-3.1-70b-versatile
```

## 🔒 Governance Features

- **Authorization Tiers**: ACT_AND_REPORT, REQUIRE_APPROVAL, DENY
- **Human Approval Queue**: High-risk actions need approval
- **Immutable Audit Log**: Hash-chained, PostgreSQL-backed
- **Cost Tracking**: Per-session budgets with hard cutoffs
- **Circuit Breakers**: Prevent cascading failures
- **Sandbox Execution**: Restricted code execution

## 📁 Project Structure

```
src/evo_platform/
├── api/              # FastAPI endpoints
├── governance/       # Authorization, Audit, Approval
├── harness/          # Runner, Sandbox, Cost Tracker
├── llm/              # LLM providers (Ollama, Groq, OpenAI, Anthropic)
├── storage/          # Database repositories
└── workers/          # Background jobs
```

## 🧪 Testing Approval Flow

```bash
# 1. Request requiring approval
curl -X POST http://localhost:8000/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-support-agent",
    "user_id": "user-456",
    "session_id": "session-refund",
    "input": "Refund my last payment",
    "action_type": "refund_payment",
    "authorization_tier": "REQUIRE_APPROVAL",
    "spending_cap_usd": 1.0
  }'

# 2. List pending approvals
curl http://localhost:8000/v1/approvals/pending

# 3. Approve
curl -X POST http://localhost:8000/v1/approvals/{approval_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver": "admin@example.com", "note": "Verified"}'
```

## 📊 Monitoring

```bash
# Audit trail for session
curl http://localhost:8000/v1/audit/session/session-1

# Verify hash chain integrity
curl http://localhost:8000/v1/audit/verify
```

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements-lock.txt

# Run tests
pytest tests/

# Format code
black src/ tests/
```

## 📝 License

MIT
