"""Agent execution routes, including SSE streaming, human-in-the-loop approvals,
and immutable audit trail access.

POST /v1/agents/execute          -> synchronous execution, full AgentResponse
POST /v1/agents/execute/stream   -> SSE stream of incremental output tokens
GET  /v1/approvals/pending       -> list pending human approval requests
POST /v1/approvals/{id}/approve  -> approve a pending action
POST /v1/approvals/{id}/deny     -> deny a pending action
GET  /v1/audit/session/{id}      -> audit entries for a session
GET  /v1/audit/verify            -> verify the audit chain has not been tampered with
"""

import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..governance.approval import ApprovalAlreadyResolved, ApprovalNotFound
from ..harness.contracts import AgentContext, AgentRequest, AuthorizationTier, Guardrails
from ..harness.runner import AgentRunner, GuardrailViolation

router = APIRouter()

_runner = AgentRunner()


class ExecuteRequest(BaseModel):
    agent_id: str
    user_id: str
    session_id: str
    input: str
    action_type: str = "generate_response"
    authorization_tier: int = Field(default=3, ge=0, le=3)
    spending_cap_usd: float = Field(default=1.0, gt=0)
    tool_allowlist: Optional[list[str]] = None


class ExecuteResponse(BaseModel):
    request_id: str
    output: str
    success: bool
    error: Optional[str] = None
    cost_usd: float
    latency_ms: float
    total_tokens: int


def _build_agent_request(payload: ExecuteRequest) -> AgentRequest:
    guardrails = Guardrails(
        spending_cap_usd=payload.spending_cap_usd,
        tool_allowlist=payload.tool_allowlist,
    )
    context = AgentContext(
        guardrails=guardrails,
        authorization_tier=AuthorizationTier(payload.authorization_tier),
    )
    return AgentRequest(
        agent_id=payload.agent_id,
        user_id=payload.user_id,
        session_id=payload.session_id,
        input=payload.input,
        context=context,
    )


@router.post("/agents/execute", response_model=ExecuteResponse)
async def execute_agent(payload: ExecuteRequest) -> ExecuteResponse:
    """Execute an agent synchronously and return the full response."""
    request = _build_agent_request(payload)
    try:
        response = await asyncio.to_thread(_runner.execute, request, payload.action_type)
    except GuardrailViolation as e:
        raise HTTPException(status_code=403, detail=str(e))

    return ExecuteResponse(
        request_id=response.request_id,
        output=response.output,
        success=response.success,
        error=response.error,
        cost_usd=response.cost_usd,
        latency_ms=response.latency_ms,
        total_tokens=response.tokens_used.total_tokens,
    )


async def _stream_tokens(text: str, request_id: str) -> AsyncGenerator[str, None]:
    words = text.split(" ")
    for i, word in enumerate(words):
        event = {
            "request_id": request_id,
            "index": i,
            "delta": word + (" " if i < len(words) - 1 else ""),
            "done": False,
        }
        yield f"data: {json.dumps(event)}\n\n"
        await asyncio.sleep(0.01)
    yield f"data: {json.dumps({'request_id': request_id, 'done': True})}\n\n"


@router.post("/agents/execute/stream")
async def execute_agent_stream(payload: ExecuteRequest) -> StreamingResponse:
    """Execute an agent and stream the output as Server-Sent Events."""
    request = _build_agent_request(payload)
    try:
        response = await asyncio.to_thread(_runner.execute, request, payload.action_type)
    except GuardrailViolation as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not response.success:
        async def _error_stream() -> AsyncGenerator[str, None]:
            yield f"data: {json.dumps({'request_id': response.request_id, 'error': response.error, 'done': True})}\n\n"

        return StreamingResponse(_error_stream(), media_type="text/event-stream")

    return StreamingResponse(
        _stream_tokens(response.output, response.request_id),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Human-in-the-loop approvals
# ---------------------------------------------------------------------------


class ApprovalResponse(BaseModel):
    approval_id: str
    agent_id: str
    session_id: str
    action_type: str
    reason: str
    status: str


class ApprovalDecisionRequest(BaseModel):
    approver: str
    note: str = ""


@router.get("/approvals/pending", response_model=list[ApprovalResponse])
async def list_pending_approvals(agent_id: Optional[str] = None) -> list[ApprovalResponse]:
    items = _runner.approval_queue.pending(agent_id=agent_id)
    return [
        ApprovalResponse(
            approval_id=r.approval_id,
            agent_id=r.agent_id,
            session_id=r.session_id,
            action_type=r.action_type,
            reason=r.reason,
            status=r.status.value,
        )
        for r in items
    ]


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_action(approval_id: str, payload: ApprovalDecisionRequest) -> ApprovalResponse:
    try:
        r = _runner.approval_queue.approve(approval_id, payload.approver, payload.note)
    except ApprovalNotFound:
        raise HTTPException(status_code=404, detail="Approval not found")
    except ApprovalAlreadyResolved as e:
        raise HTTPException(status_code=409, detail=str(e))

    return ApprovalResponse(
        approval_id=r.approval_id,
        agent_id=r.agent_id,
        session_id=r.session_id,
        action_type=r.action_type,
        reason=r.reason,
        status=r.status.value,
    )


@router.post("/approvals/{approval_id}/deny", response_model=ApprovalResponse)
async def deny_action(approval_id: str, payload: ApprovalDecisionRequest) -> ApprovalResponse:
    try:
        r = _runner.approval_queue.deny(approval_id, payload.approver, payload.note)
    except ApprovalNotFound:
        raise HTTPException(status_code=404, detail="Approval not found")
    except ApprovalAlreadyResolved as e:
        raise HTTPException(status_code=409, detail=str(e))

    return ApprovalResponse(
        approval_id=r.approval_id,
        agent_id=r.agent_id,
        session_id=r.session_id,
        action_type=r.action_type,
        reason=r.reason,
        status=r.status.value,
    )


# ---------------------------------------------------------------------------
# Immutable audit trail
# ---------------------------------------------------------------------------


class AuditEntryResponse(BaseModel):
    sequence: int
    entry_id: str
    timestamp: str
    agent_id: str
    session_id: str
    action: str
    authorization_tier: str
    outcome: str
    entry_hash: str


@router.get("/audit/session/{session_id}", response_model=list[AuditEntryResponse])
async def get_session_audit_trail(session_id: str) -> list[AuditEntryResponse]:
    entries = _runner.audit_log.for_session(session_id)
    return [
        AuditEntryResponse(
            sequence=e.sequence,
            entry_id=e.entry_id,
            timestamp=e.timestamp,
            agent_id=e.agent_id,
            session_id=e.session_id,
            action=e.action,
            authorization_tier=e.authorization_tier,
            outcome=e.outcome,
            entry_hash=e.entry_hash,
        )
        for e in entries
    ]


@router.get("/audit/verify")
async def verify_audit_chain() -> dict:
    """Verify the audit log's hash chain has not been tampered with."""
    is_valid = _runner.audit_log.verify_chain()
    return {"chain_valid": is_valid, "total_entries": len(_runner.audit_log)}
