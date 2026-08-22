"""Human-in-the-Loop Approval Workflow.

When AuthorizationEnforcer returns REQUIRE_APPROVAL, the action is parked
here as a PENDING request until a human approver acts on it.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class ApprovalNotFound(Exception):
    pass


class ApprovalAlreadyResolved(Exception):
    pass


@dataclass
class ApprovalRequest:
    approval_id: str
    agent_id: str
    session_id: str
    action_type: str
    reason: str
    payload: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        return self.expires_at is not None and datetime.now(timezone.utc) > self.expires_at


class ApprovalQueue:
    """In-memory approval queue. Swap for a durable queue (Postgres/Redis) in prod."""

    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}
        self._lock = Lock()

    def submit(
        self,
        agent_id: str,
        session_id: str,
        action_type: str,
        reason: str,
        payload: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[float] = 3600.0,
    ) -> ApprovalRequest:
        approval_id = f"approval_{uuid.uuid4().hex[:16]}"
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            if ttl_seconds
            else None
        )
        request = ApprovalRequest(
            approval_id=approval_id,
            agent_id=agent_id,
            session_id=session_id,
            action_type=action_type,
            reason=reason,
            payload=payload or {},
            expires_at=expires_at,
        )
        with self._lock:
            self._requests[approval_id] = request
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        with self._lock:
            request = self._requests.get(approval_id)
        if request is None:
            raise ApprovalNotFound(approval_id)
        if request.status == ApprovalStatus.PENDING and request.is_expired():
            request.status = ApprovalStatus.EXPIRED
        return request

    def approve(self, approval_id: str, approved_by: str, note: str = "") -> ApprovalRequest:
        request = self.get(approval_id)
        if request.status != ApprovalStatus.PENDING:
            raise ApprovalAlreadyResolved(
                f"Approval {approval_id} already resolved as {request.status.value}"
            )
        request.status = ApprovalStatus.APPROVED
        request.resolved_at = datetime.now(timezone.utc)
        request.resolved_by = approved_by
        request.resolution_note = note
        return request

    def deny(self, approval_id: str, denied_by: str, note: str = "") -> ApprovalRequest:
        request = self.get(approval_id)
        if request.status != ApprovalStatus.PENDING:
            raise ApprovalAlreadyResolved(
                f"Approval {approval_id} already resolved as {request.status.value}"
            )
        request.status = ApprovalStatus.DENIED
        request.resolved_at = datetime.now(timezone.utc)
        request.resolved_by = denied_by
        request.resolution_note = note
        return request

    def pending(self, agent_id: Optional[str] = None) -> List[ApprovalRequest]:
        with self._lock:
            items = [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]
        if agent_id:
            items = [r for r in items if r.agent_id == agent_id]
        return items
