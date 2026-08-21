"""Agent execution routes, including SSE streaming."""

import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..harness.contracts import AgentContext, AgentRequest, Guardrails
from ..harness.runner import AgentRunner, GuardrailViolation

router = APIRouter()

_runner = AgentRunner()


class ExecuteRequest(BaseModel):
    agent_id: str
    user_id: str
    session_id: str
    input: str
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
    context = AgentContext(guardrails=guardrails)
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
        response = await asyncio.to_thread(_runner.execute, request)
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
    """Chunk output into SSE-formatted token events."""
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
        response = await asyncio.to_thread(_runner.execute, request)
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
