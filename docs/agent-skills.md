# Agent Skills support

## Scope

Agent Skills packages live in `capabilities/skills/<name>/SKILL.md`.
This change introduces package examples, metadata validation and offline CI.
It does not wire skills into AgentRunner, publish a registry, execute scripts,
implement runtime progressive loading or certify skills as safe.

Specification reviewed: https://agentskills.io/specification (2026-10-19).
The upstream document is not pinned to a version; review changes before updating
validation rules. This is an Evo validator, not official skills-ref certification.

## Package contract

Required fields: `name` and `description`. Optional standard fields include
`license`, `compatibility`, string-to-string `metadata`, and experimental
`allowed-tools`. The name must match its directory and obey the specification's
length and naming constraints. Put Evo-specific fields under `metadata` and
quote numeric-looking versions. No repository-wide license is inferred.

Optional directories include `references/`, `scripts/` and `assets/`; other files
are permitted by the specification. References in SKILL.md should be relative
to the skill root. Keep main instructions under 500 lines as a recommendation,
not a required validity rule. Empty Markdown bodies are accepted by the validator.

## Validation

Use an isolated Python environment, then run:

```bash
python -m pip install -r tools/requirements-skills.txt
python tools/validate_skills.py capabilities/skills
python -m unittest discover -s tests -p test_agent_skills_format.py -v
```

The CLI emits only name and description for discovery; it reads SKILL.md to
validate it but does not emit its body or load resource contents. A future host
adapter must load full instructions only on activation and resources on demand.

Evo import hardening adds rejection of duplicate YAML keys, non-string YAML
mapping keys, symlinked skill roots/SKILL.md, and SKILL.md files over 256 KiB.
These are local restrictions, not additional upstream format requirements.
Additional filesystem paths are not recursively security-scanned by this tool.
Run validation on an immutable checkout without credentials or network privileges.

## Security boundary

A valid file is not an approved capability. `allowed-tools` and `evo.risk` are
claims from the package author, never an authorization decision. Imported content
remains untrusted until separate provenance, licensing, evaluation and human
review gates pass. The example is draft and is not approved for production.

Do not execute bundled scripts during discovery or validation. Runtime adapters
must enforce independent server-side policy, safe resource path resolution,
execution isolation and approval rules. None of those controls is supplied by
this format validator. No cluster addresses, credentials or private inventory
are needed for the example or tests.
