"""Sandboxed Execution - Isolated runtime for untrusted agent/tool code."""

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class SandboxLimits:
    timeout_s: float = 10.0
    max_output_bytes: int = 1_000_000
    allowed_domains: List[str] = field(default_factory=list)
    env_allowlist: List[str] = field(default_factory=list)


@dataclass
class SandboxResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    latency_ms: float = 0.0
    timed_out: bool = False
    truncated: bool = False


class SandboxProvider(Protocol):
    """Interface every sandbox backend must implement."""

    def run_python(
        self, code: str, limits: SandboxLimits, proxy_env: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        ...


class LocalProcessSandbox:
    """Development-grade sandbox using an isolated subprocess."""

    def run_python(
        self, code: str, limits: SandboxLimits, proxy_env: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        start = time.time()
        with TemporaryDirectory(prefix="evo-sandbox-") as workdir:
            script_path = Path(workdir) / "agent_code.py"
            script_path.write_text(code)

            env = {"PATH": "/usr/bin:/bin"}
            for key in limits.env_allowlist:
                import os

                if key in os.environ:
                    env[key] = os.environ[key]
            if proxy_env:
                env.update(proxy_env)

            try:
                proc = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=workdir,
                    env=env,
                    capture_output=True,
                    timeout=limits.timeout_s,
                    text=True,
                )
                latency_ms = (time.time() - start) * 1000
                stdout = proc.stdout[: limits.max_output_bytes]
                stderr = proc.stderr[: limits.max_output_bytes]
                truncated = len(proc.stdout) > limits.max_output_bytes
                return SandboxResult(
                    success=proc.returncode == 0,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=proc.returncode,
                    latency_ms=latency_ms,
                    truncated=truncated,
                )
            except subprocess.TimeoutExpired:
                latency_ms = (time.time() - start) * 1000
                return SandboxResult(
                    success=False,
                    stderr=f"Execution exceeded timeout of {limits.timeout_s}s",
                    exit_code=-1,
                    latency_ms=latency_ms,
                    timed_out=True,
                )


class RemoteSandboxProvider:
    """Placeholder for a real isolated backend (E2B, Firecracker, etc)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if not api_key:
            raise RuntimeError(
                "RemoteSandboxProvider requires an API key. "
                "Set E2B_API_KEY or pass api_key explicitly. "
                "Falling back to LocalProcessSandbox is recommended for dev."
            )

    def run_python(
        self, code: str, limits: SandboxLimits, proxy_env: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        raise NotImplementedError(
            "Wire this up to your sandbox vendor SDK (e.g. e2b-code-interpreter). "
            "Interface (run_python -> SandboxResult) is stable; only the body changes."
        )


def get_default_sandbox() -> SandboxProvider:
    """Factory: returns remote sandbox if configured, else local dev sandbox."""
    import os

    api_key = os.environ.get("E2B_API_KEY")
    if api_key:
        try:
            return RemoteSandboxProvider(api_key=api_key)
        except NotImplementedError:
            pass
    return LocalProcessSandbox()
