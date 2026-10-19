# Skill Runner

`SkillAgentRunner` is an optional extension of `AgentRunner`. It adds reviewed
skill instructions to the model context without changing the existing
authorization or execution path.

This feature is not enabled in the API, deployed, or approved for production.

## How it works

`SkillAgentRunner` inherits `AgentRunner.execute()` unchanged. It overrides only
the model context construction.

For an allowed request, it:

1. Looks up the skill bound to the agent.
2. Adds the skill instructions to the server-owned base system prompt.
3. Records the skill name and SHA-256 digest in the audit log.
4. Calls the model provider.

The skill instructions do not grant tools, change authorization tiers, or
override server policy.

## Configuration

Validate the skill first with `tools/validate_skills.py`. Review its content
and provenance, then approve its SHA-256 digest through server configuration or
code review.

A digest detects changes. It does not establish trust by itself.

```python
from pathlib import Path
from evo_platform.harness.skill_loader import SkillBinding, SkillLoader
from evo_platform.harness.skill_runner import SkillAgentRunner

loader = SkillLoader(
    Path("capabilities/skills").resolve(),
    {
        "inventory-auditor": SkillBinding(
            "kubernetes-readonly-audit",
            approved_digest,
        )
    },
)

runner = SkillAgentRunner(
    skill_loader=loader,
    system_prompt="Analyze supplied evidence. Do not invent completed actions.",
    llm_provider=provider,
)
```

`approved_digest` and `provider` are server-owned values. They are not request
fields.

An agent without a skill binding fails before any model call. When adding the
API bootstrap later, map this configuration error to a safe API response.

## Boundaries

- The runner uses one combined system message and preserves the user message.
- Denied and pending requests return before skill lookup or model use.
- Skill metadata does not enable tools, scripts, or authorization changes.
- Skills are loaded from a read-only directory at startup.
- The digest covers `SKILL.md` only. Other resource files are not loaded or
  pinned.
- Instruction bodies are limited to 16,000 characters; file reads are limited
  to 256 KiB. These are file limits, not model context guarantees.
- Skill names use lowercase ASCII identifiers.
- The full instruction text is not stored in audit metadata.
- Filesystem checks assume a trusted deployment. They are not a defense against
  an attacker modifying files while the process is running.

## Tests

Run the execute-path tests with:

```bash
python -m unittest discover -s tests -p test_skill_runner_integration.py -v
```

The tests use the real runner and contracts, with mocked model, audit,
approval, and sandbox boundaries. They do not test provider networking, API
authentication, database persistence, skill quality, or production readiness.
