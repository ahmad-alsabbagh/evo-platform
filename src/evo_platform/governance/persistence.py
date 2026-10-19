"""PostgreSQL-backed implementations of the audit log and approval queue.

These classes expose the exact same public method signatures as the
in-memory `ImmutableAuditLog` / `ApprovalQueue` in `audit.py` / `approval.py`,
so `AgentRunner` can swap between them with zero call-site changes -- the
only difference is durability.

Activated automatically when `DATABASE_URL` is set in the environment.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .approval import (
    ApprovalAlreadyResolved,
    ApprovalNotFound,
    ApprovalRequest,
    ApprovalStatus,
)
from .audit import GENESIS_HASH, AuditEntry
from .models import ApprovalRequestRow, AuditLogRow, Base


def _row_to_audit_entry(row: AuditLogRow) -> AuditEntry:
    return AuditEntry(
        sequence=row.sequence,
        entry_id=row.entry_id,
        timestamp=row.timestamp.isoformat(),
        agent_id=row.agent_id,
        user_id=row.user_id,
        session_id=row.session_id,
        action=row.action,
        authorization_tier=row.authorization_tier,
        outcome=row.outcome,
        metadata=row.metadata_json or {},
        prev_hash=row.prev_hash,
        entry_hash=row.entry_hash,
    )


def _row_to_approval_request(row: ApprovalRequestRow) -> ApprovalRequest:
    req = ApprovalRequest(
        approval_id=row.approval_id,
        agent_id=row.agent_id,
        session_id=row.session_id,
        action_type=row.action_type,
        reason=row.reason,
        payload=row.payload_json or {},
        status=ApprovalStatus(row.status),
        created_at=row.created_at,
        resolved_at=row.resolved_at,
        resolved_by=row.resolved_by,
        resolution_note=row.resolution_note,
        expires_at=row.expires_at,
    )
    return req


class PostgresImmutableAuditLog:
    """Durable, hash-chained audit log backed by Postgres."""

    def __init__(self, database_url: str, create_tables: bool = True):
        self.engine = create_engine(database_url, future=True)
        if create_tables:
            Base.metadata.create_all(self.engine, tables=[AuditLogRow.__table__])
        self._Session = sessionmaker(bind=self.engine, future=True)

    def _compute_hash(self, sequence: int, entry_id: str, timestamp: str, agent_id: str,
                       user_id: str, session_id: str, action: str, authorization_tier: str,
                       outcome: str, metadata: Dict[str, Any], prev_hash: str) -> str:
        payload = {
            "sequence": sequence,
            "entry_id": entry_id,
            "timestamp": timestamp,
            "agent_id": agent_id,
            "user_id": user_id,
            "session_id": session_id,
            "action": action,
            "authorization_tier": authorization_tier,
            "outcome": outcome,
            "metadata": metadata,
            "prev_hash": prev_hash,
        }
        blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def append(
        self,
        agent_id: str,
        user_id: str,
        session_id: str,
        action: str,
        authorization_tier: str,
        outcome: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        metadata = metadata or {}
        with self._Session() as session:
            last = session.query(AuditLogRow).order_by(AuditLogRow.sequence.desc()).first()
            sequence = (last.sequence + 1) if last else 0
            prev_hash = last.entry_hash if last else GENESIS_HASH
            entry_id = f"audit_{sequence:012d}"
            timestamp = datetime.now(timezone.utc)
            entry_hash = self._compute_hash(
                sequence, entry_id, timestamp.isoformat(), agent_id, user_id,
                session_id, action, authorization_tier, outcome, metadata, prev_hash,
            )
            row = AuditLogRow(
                sequence=sequence,
                entry_id=entry_id,
                timestamp=timestamp,
                agent_id=agent_id,
                user_id=user_id,
                session_id=session_id,
                action=action,
                authorization_tier=authorization_tier,
                outcome=outcome,
                metadata_json=metadata,
                prev_hash=prev_hash,
                entry_hash=entry_hash,
            )
            session.add(row)
            session.commit()
            return _row_to_audit_entry(row)

    def verify_chain(self) -> bool:
        with self._Session() as session:
            rows = session.query(AuditLogRow).order_by(AuditLogRow.sequence.asc()).all()
            prev_hash = GENESIS_HASH
            for row in rows:
                if row.prev_hash != prev_hash:
                    return False
                recomputed = self._compute_hash(
                    row.sequence, row.entry_id, row.timestamp.isoformat(), row.agent_id,
                    row.user_id, row.session_id, row.action, row.authorization_tier,
                    row.outcome, row.metadata_json or {}, row.prev_hash,
                )
                if recomputed != row.entry_hash:
                    return False
                prev_hash = row.entry_hash
            return True

    def for_session(self, session_id: str) -> List[AuditEntry]:
        with self._Session() as session:
            rows = (
                session.query(AuditLogRow)
                .filter(AuditLogRow.session_id == session_id)
                .order_by(AuditLogRow.sequence.asc())
                .all()
            )
            return [_row_to_audit_entry(r) for r in rows]

    def for_agent(self, agent_id: str) -> List[AuditEntry]:
        with self._Session() as session:
            rows = (
                session.query(AuditLogRow)
                .filter(AuditLogRow.agent_id == agent_id)
                .order_by(AuditLogRow.sequence.asc())
                .all()
            )
            return [_row_to_audit_entry(r) for r in rows]

    def export(self) -> List[Dict[str, Any]]:
        with self._Session() as session:
            rows = session.query(AuditLogRow).order_by(AuditLogRow.sequence.asc()).all()
            return [
                {
                    "sequence": r.sequence,
                    "entry_id": r.entry_id,
                    "timestamp": r.timestamp.isoformat(),
                    "agent_id": r.agent_id,
                    "user_id": r.user_id,
                    "session_id": r.session_id,
                    "action": r.action,
                    "authorization_tier": r.authorization_tier,
                    "outcome": r.outcome,
                    "metadata": r.metadata_json,
                    "prev_hash": r.prev_hash,
                    "entry_hash": r.entry_hash,
                }
                for r in rows
            ]

    def __len__(self) -> int:
        with self._Session() as session:
            return session.query(AuditLogRow).count()


class PostgresApprovalQueue:
    """Durable human-in-the-loop approval queue backed by Postgres."""

    def __init__(self, database_url: str, create_tables: bool = True):
        self.engine = create_engine(database_url, future=True)
        if create_tables:
            Base.metadata.create_all(self.engine, tables=[ApprovalRequestRow.__table__])
        self._Session = sessionmaker(bind=self.engine, future=True)

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
            datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        )
        with self._Session() as session:
            row = ApprovalRequestRow(
                approval_id=approval_id,
                agent_id=agent_id,
                session_id=session_id,
                action_type=action_type,
                reason=reason,
                payload_json=payload or {},
                status=ApprovalStatus.PENDING.value,
                expires_at=expires_at,
            )
            session.add(row)
            session.commit()
            return _row_to_approval_request(row)

    def _get_row(self, session: Session, approval_id: str) -> ApprovalRequestRow:
        row = (
            session.query(ApprovalRequestRow)
            .filter(ApprovalRequestRow.approval_id == approval_id)
            .first()
        )
        if row is None:
            raise ApprovalNotFound(approval_id)
        if row.status == ApprovalStatus.PENDING.value and row.expires_at is not None:
            if datetime.now(timezone.utc) > row.expires_at:
                row.status = ApprovalStatus.EXPIRED.value
                session.commit()
        return row

    def get(self, approval_id: str) -> ApprovalRequest:
        with self._Session() as session:
            row = self._get_row(session, approval_id)
            return _row_to_approval_request(row)

    def approve(self, approval_id: str, approved_by: str, note: str = "") -> ApprovalRequest:
        with self._Session() as session:
            row = self._get_row(session, approval_id)
            if row.status != ApprovalStatus.PENDING.value:
                raise ApprovalAlreadyResolved(
                    f"Approval {approval_id} already resolved as {row.status}"
                )
            row.status = ApprovalStatus.APPROVED.value
            row.resolved_at = datetime.now(timezone.utc)
            row.resolved_by = approved_by
            row.resolution_note = note
            session.commit()
            return _row_to_approval_request(row)

    def deny(self, approval_id: str, denied_by: str, note: str = "") -> ApprovalRequest:
        with self._Session() as session:
            row = self._get_row(session, approval_id)
            if row.status != ApprovalStatus.PENDING.value:
                raise ApprovalAlreadyResolved(
                    f"Approval {approval_id} already resolved as {row.status}"
                )
            row.status = ApprovalStatus.DENIED.value
            row.resolved_at = datetime.now(timezone.utc)
            row.resolved_by = denied_by
            row.resolution_note = note
            session.commit()
            return _row_to_approval_request(row)

    def pending(self, agent_id: Optional[str] = None) -> List[ApprovalRequest]:
        with self._Session() as session:
            query = session.query(ApprovalRequestRow).filter(
                ApprovalRequestRow.status == ApprovalStatus.PENDING.value
            )
            if agent_id:
                query = query.filter(ApprovalRequestRow.agent_id == agent_id)
            rows = query.order_by(ApprovalRequestRow.created_at.asc()).all()
            return [_row_to_approval_request(r) for r in rows]


def get_governance_backend(database_url: Optional[str] = None):
    """Factory: returns (audit_log, approval_queue) backed by Postgres if
    DATABASE_URL is configured, else falls back to in-memory implementations.
    """
    import os

    from .approval import ApprovalQueue
    from .audit import ImmutableAuditLog

    url = database_url or os.environ.get("DATABASE_URL")
    if url:
        try:
            return PostgresImmutableAuditLog(url), PostgresApprovalQueue(url)
        except Exception:
            # Fall back to in-memory if Postgres is unreachable
            pass
    return ImmutableAuditLog(), ApprovalQueue()
