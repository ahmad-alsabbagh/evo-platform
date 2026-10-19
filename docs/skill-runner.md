# Skill-aware AgentRunner

`SkillAgentRunner` subclasses `AgentRunner` and inherits `execute()` unchanged.
It overrides only model context construction. The original runner remains intact.
Nothing is enabled in the API, deployed, or approved for production by this change.

## Configuration

Validate SKILL.md with `tools/validate_skills.py` first. Review the content and
provenance and approve its SHA-256 through server configuration/code review.
A digest detects changes; computing it does not establish trust.

```python
from pathlib import Path
from evo_platform.harness.skill_loader import SkillBinding, SkillLoader
from evo_platform.harness.skill_runner import SkillAgentRunner

loader = SkillLoader(Path("capabilities/skills").resolve(), {
    "inventory-auditor": SkillBinding("kubernetes-readonly-audit", approved_digest),
})
runner = SkillAgentRunner(
    skill_loader=loader,
    system_prompt="Analyze supplied evidence. Do not invent completed actions.",
    llm_provider=provider,
)
```

`approved_digest` and `provider` are server-owned objects, not request fields.
The example skill is draft and must be evaluated before production approval.
Unbound agents fail without an LLM call. Map that configuration error to a safe
API response when integrating the bootstrap; this patch does not change HTTP routes.

## Boundaries

- Uses one combined system message and preserves the user message.
- Existing deny/pending branches return before skill context lookup or model use.
- No tools, authorization tiers, scripts or references are enabled by skill metadata.
- Snapshot is loaded at construction from a read-only immutable directory. Digest
  applies to SKILL.md only; other resource files are not loaded or pinned.
- Runtime limits instruction bodies to 16000 characters and file reads to 256 KiB.
  This is a character limit, not a model-token/context-window guarantee.
- Runtime names use a restricted ASCII subset. Format validation remains a separate
  prerequisite; this loader is not an official Agent Skills conformance validator.
- Full instruction text is not put in the skill-context audit metadata.
- `output_max_tokens` is passed to the provider; Ollama currently ignores that kwarg.
- Authenticate callers and authorize access to agent IDs before exposing bindings.
  The existing client-provided authorization tier is not fixed by this bridge.
- Filesystem checks assume a trusted immutable deployment; they are not a sandbox
  against an attacker concurrently rewriting directories.

## Tests

`python -m unittest discover -s tests -p test_skill_runner_integration.py -v`

Tests import real classes and invoke inherited execute(), with fake model, audit,
approval and sandbox boundaries. No AST extraction or live services are used.
Run them in the project's locked environment. They do not prove provider-network,
API authentication, database persistence, skill quality or production readiness.
