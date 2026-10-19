"""Immutable Audit Trail - Hash-chained, append-only log of agent actions."""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

GENESIS_HASH = "0" * 64


@dataclass
class AuditEntry:
    sequence: int
    entry_id: str
    timestamp: str
    agent_id: str
    user_id: str
    session_id: str
    action: str
    authorization_tier: str
    outcome: str
    metadata: Dict[str, Any]
    prev_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "sequence": self.sequence,
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "action": self.action,
            "authorization_tier": self.authorization_tier,
            "outcome": self.outcome,
            "metadata": self.metadata,
            "prev_hash": self.prev_hash,
        }
        blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()


class AuditChainCorrupted(Exception):
    """Raised when hash-chain verification fails."""


class ImmutableAuditLog:
    """Append-only, hash-chained audit log."""

    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._lock = Lock()

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
        with self._lock:
            sequence = len(self._entries)
            prev_hash = self._entries[-1].entry_hash if self._entries else GENESIS_HASH
            entry = AuditEntry(
                sequence=sequence,
                entry_id=f"audit_{sequence:012d}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id,
                user_id=user_id,
                session_id=session_id,
                action=action,
                authorization_tier=authorization_tier,
                outcome=outcome,
                metadata=metadata or {},
                prev_hash=prev_hash,
            )
            entry.entry_hash = entry.compute_hash()
            self._entries.append(entry)
            return entry

    def verify_chain(self) -> bool:
        """Recompute every hash and confirm the chain is unbroken."""
        with self._lock:
            prev_hash = GENESIS_HASH
            for entry in self._entries:
                if entry.prev_hash != prev_hash:
                    return False
                if entry.compute_hash() != entry.entry_hash:
                    return False
                prev_hash = entry.entry_hash
            return True

    def for_session(self, session_id: str) -> List[AuditEntry]:
        with self._lock:
            return [e for e in self._entries if e.session_id == session_id]

    def for_agent(self, agent_id: str) -> List[AuditEntry]:
        with self._lock:
            return [e for e in self._entries if e.agent_id == agent_id]

    def export(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(e) for e in self._entries]

    def __len__(self) -> int:
        return len(self._entries)
