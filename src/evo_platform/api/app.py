"""FastAPI application with multi-agent orchestration support."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from ..harness.contracts import AgentRequest, AgentContext, Guardrails, AuthorizationTier
from ..harness.runner import AgentRunner, AgentRunnerConfig
from ..orchestration.hierarchical import create_orchestrator
from ..llm.providers import get_llm_provider

app = FastAPI(title="Evo Platform", version="0.2.0")

runner = AgentRunner(config=AgentRunnerConfig())
llm_provider = get_llm_provider()
orchestrator = create_orchestrator(llm_provider)


class ExecuteRequest(BaseModel):
    agent_id: str
    user_id: str
    session_id: str
    input: str
    action_type: Optional[str] = "generate_response"
    authorization_tier: Optional[str] = "ACT_AND_REPORT"
    spending_cap_usd: Optional[float] = 1.0


class ApproveRequest(BaseModel):
    approver: str
    note: Optional[str] = ""


@app.post("/v1/agents/execute")
def execute_agent(req: ExecuteRequest) -> Dict[str, Any]:
    agent_req = AgentRequest(
        agent_id=req.agent_id,
        user_id=req.user_id,
        session_id=req.session_id,
        input=req.input,
        context=AgentContext(
            guardrails=Guardrails(spending_cap_usd=req.spending_cap_usd),
            authorization_tier=AuthorizationTier(req.authorization_tier),
        ),
    )
    response = runner.execute(agent_req, action_type=req.action_type)
    return {
        "request_id": response.request_id,
        "output": response.output,
        "success": response.success,
        "error": response.error,
        "cost_usd": response.cost_usd,
        "latency_ms": response.latency_ms,
        "total_tokens": response.tokens_used.total_tokens,
    }


@app.post("/v1/orchestrator/execute")
def execute_orchestrated(req: ExecuteRequest) -> Dict[str, Any]:
    agent_req = AgentRequest(
        agent_id="orchestrator",
        user_id=req.user_id,
        session_id=req.session_id,
        input=req.input,
        context=AgentContext(
            guardrails=Guardrails(spending_cap_usd=req.spending_cap_usd),
            authorization_tier=AuthorizationTier(req.authorization_tier),
        ),
    )
    response = orchestrator.execute(agent_req)
    return {
        "request_id": response.request_id,
        "output": response.output,
        "success": response.success,
        "error": response.error,
        "cost_usd": response.cost_usd,
        "latency_ms": response.latency_ms,
        "total_tokens": response.tokens_used.total_tokens,
    }


@app.get("/v1/approvals/pending")
def list_pending() -> List[Dict[str, Any]]:
    pending = runner.approval_queue.pending()
    return [
        {
            "approval_id": p.approval_id,
            "agent_id": p.agent_id,
            "session_id": p.session_id,
            "action_type": p.action_type,
            "reason": p.reason,
            "status": p.status.value,
        }
        for p in pending
    ]


@app.post("/v1/approvals/{approval_id}/approve")
def approve(approval_id: str, req: ApproveRequest) -> Dict[str, Any]:
    try:
        result = runner.approval_queue.approve(approval_id, req.approver, req.note)
        return {
            "approval_id": result.approval_id,
            "agent_id": result.agent_id,
            "session_id": result.session_id,
            "action_type": result.action_type,
            "reason": result.reason,
            "status": result.status.value,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/v1/approvals/{approval_id}/deny")
def deny(approval_id: str, req: ApproveRequest) -> Dict[str, Any]:
    try:
        result = runner.approval_queue.deny(approval_id, req.approver, req.note)
        return {
            "approval_id": result.approval_id,
            "agent_id": result.agent_id,
            "session_id": result.session_id,
            "action_type": result.action_type,
            "reason": result.reason,
            "status": result.status.value,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/v1/audit/session/{session_id}")
def get_session_audit(session_id: str) -> List[Dict[str, Any]]:
    entries = runner.audit_log.for_session(session_id)
    return [
        {
            "sequence": e.sequence,
            "entry_id": e.entry_id,
            "timestamp": e.timestamp,
            "agent_id": e.agent_id,
            "session_id": e.session_id,
            "action": e.action,
            "authorization_tier": e.authorization_tier,
            "outcome": e.outcome,
            "entry_hash": e.entry_hash,
        }
        for e in entries
    ]


@app.get("/v1/audit/verify")
def verify_audit() -> Dict[str, Any]:
    valid = runner.audit_log.verify_chain()
    return {"chain_valid": valid, "total_entries": len(runner.audit_log)}
