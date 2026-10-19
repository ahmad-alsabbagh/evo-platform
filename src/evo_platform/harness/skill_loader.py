"""Load explicitly reviewed Agent Skills without executing their resources."""
import hashlib
from pathlib import Path
import re
from typing import NamedTuple


class SkillBinding(NamedTuple):
    name: str
    sha256: str


class LoadedSkill(NamedTuple):
    name: str
    sha256: str
    instructions: str


class SkillLoader:
    """Build a read-only instruction snapshot from trusted server configuration."""

    def __init__(self, root: Path, bindings: dict[str, SkillBinding]) -> None:
        base = Path(root).absolute()
        if not base.is_dir() or any(p.is_symlink() for p in (base, *base.parents)):
            raise ValueError("Use a skill root without symlink ancestors")
        self._skills: dict[str, LoadedSkill] = {}
        for agent_id, binding in bindings.items():
            if not agent_id or len(binding.name) > 64:
                raise ValueError("Invalid agent ID or skill name")
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", binding.name):
                raise ValueError("Runtime skill names must use lowercase ASCII identifiers")
            if not re.fullmatch(r"[0-9a-f]{64}", binding.sha256):
                raise ValueError("A reviewed SHA-256 pin is required")
            directory = base / binding.name
            source = directory / "SKILL.md"
            if directory.is_symlink() or source.is_symlink():
                raise ValueError("Symlinked skill paths are not allowed")
            if not source.resolve().is_relative_to(base.resolve()):
                raise ValueError("Skill path escapes configured root")
            with source.open("rb") as handle:
                raw = handle.read(262145)
            if len(raw) > 262144 or hashlib.sha256(raw).hexdigest() != binding.sha256:
                raise ValueError("Skill exceeds size limit or differs from reviewed digest")
            lines = raw.decode("utf-8").splitlines()
            if not lines or lines[0] != "---":
                raise ValueError("Missing skill frontmatter")
            try:
                end = lines.index("---", 1)
            except ValueError as exc:
                raise ValueError("Unclosed skill frontmatter") from exc
            body = "\n".join(lines[end + 1:]).strip()
            if not body or len(body) > 16000:
                raise ValueError("Runtime instructions must contain 1-16000 characters")
            self._skills[agent_id] = LoadedSkill(binding.name, binding.sha256, body)

    def for_agent(self, agent_id: str) -> LoadedSkill | None:
        return self._skills.get(agent_id)
