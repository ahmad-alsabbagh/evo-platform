"""Credential Proxy - Ensures raw credentials never enter the sandbox.

Agents and sandboxed tool code only ever see short-lived, scoped proxy
tokens. The proxy resolves those tokens to real credentials at call time,
inside the trusted control plane, and injects them into outbound requests.
"""

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CredentialAccessDenied(Exception):
    """Raised when a proxy token is invalid, expired, or scope-mismatched."""


@dataclass
class ProxyToken:
    token: str
    credential_id: str
    allowed_domains: List[str]
    expires_at: float
    max_uses: int
    uses: int = 0
    session_id: str = ""

    def is_valid(self) -> bool:
        return time.time() < self.expires_at and self.uses < self.max_uses


@dataclass
class StoredCredential:
    credential_id: str
    secret_value: str
    provider: str
    allowed_domains: List[str] = field(default_factory=list)


class CredentialVault:
    """In-memory credential store. Swap for KMS/Vault/Secrets Manager in prod."""

    def __init__(self):
        self._credentials: Dict[str, StoredCredential] = {}

    def register(self, credential: StoredCredential) -> None:
        self._credentials[credential.credential_id] = credential

    def get(self, credential_id: str) -> Optional[StoredCredential]:
        return self._credentials.get(credential_id)


class CredentialProxy:
    """Issues and resolves short-lived proxy tokens for sandboxed execution."""

    def __init__(self, vault: Optional[CredentialVault] = None):
        self.vault = vault or CredentialVault()
        self._tokens: Dict[str, ProxyToken] = {}

    def issue_token(
        self,
        credential_id: str,
        session_id: str,
        ttl_s: float = 300.0,
        max_uses: int = 50,
        allowed_domains: Optional[List[str]] = None,
    ) -> ProxyToken:
        credential = self.vault.get(credential_id)
        if credential is None:
            raise CredentialAccessDenied(f"Unknown credential_id: {credential_id}")

        raw = secrets.token_urlsafe(32)
        token_value = f"evo_proxy_{hashlib.sha256(raw.encode()).hexdigest()[:24]}"

        proxy_token = ProxyToken(
            token=token_value,
            credential_id=credential_id,
            allowed_domains=allowed_domains or credential.allowed_domains,
            expires_at=time.time() + ttl_s,
            max_uses=max_uses,
            session_id=session_id,
        )
        self._tokens[token_value] = proxy_token
        return proxy_token

    def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)

    def revoke_session(self, session_id: str) -> int:
        to_remove = [t for t, pt in self._tokens.items() if pt.session_id == session_id]
        for t in to_remove:
            self._tokens.pop(t, None)
        return len(to_remove)

    def resolve(self, token: str, target_domain: str) -> str:
        proxy_token = self._tokens.get(token)
        if proxy_token is None:
            raise CredentialAccessDenied("Unknown or revoked proxy token")
        if not proxy_token.is_valid():
            raise CredentialAccessDenied("Proxy token expired or exhausted")
        if proxy_token.allowed_domains and target_domain not in proxy_token.allowed_domains:
            raise CredentialAccessDenied(
                f"Domain '{target_domain}' not in allowed_domains for this token"
            )

        credential = self.vault.get(proxy_token.credential_id)
        if credential is None:
            raise CredentialAccessDenied("Backing credential no longer exists")

        proxy_token.uses += 1
        return credential.secret_value

    def active_token_count(self, session_id: Optional[str] = None) -> int:
        if session_id is None:
            return len(self._tokens)
        return sum(1 for pt in self._tokens.values() if pt.session_id == session_id)
