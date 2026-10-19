# Agent Skills

Agent Skills are packages of instructions stored in
`capabilities/skills/<name>/SKILL.md`.

This repository includes package examples, metadata validation, and offline CI.
It does not yet publish a skill registry, run skill scripts, load resources at
runtime, or certify a skill as safe.

The validation rules are based on the Agent Skills specification:
https://agentskills.io/specification. Review upstream changes before updating
the validator. This is an Evo validator, not an official certification tool.

## Package layout

A skill package needs:

- A directory under `capabilities/skills/`.
- A `SKILL.md` file with `name` and `description` frontmatter.
- A directory name that matches the skill name.

Optional files and directories include `references/`, `scripts/`, and
`assets/`. References inside `SKILL.md` should be relative to the skill root.

Put Evo-specific settings under `metadata`. Quote values that look like
versions, such as `"1.0"`.

## Validation

Run the validator in an isolated Python environment:

```bash
python -m pip install -r tools/requirements-skills.txt
python tools/validate_skills.py capabilities/skills
python -m unittest discover -s tests -p test_agent_skills_format.py -v
```

The validator reads `SKILL.md` to check its structure. It reports only the
skill name and description for discovery. It does not print the instruction
body or load other resource files.

The validator also rejects duplicate YAML keys, non-string YAML mapping keys,
symlinked skill roots or `SKILL.md` files, and `SKILL.md` files larger than
256 KiB. These are local safety rules, not upstream specification requirements.

Run validation on an immutable checkout without credentials or network access.

## Security boundary

A valid skill file is not an approved capability.

Fields such as `allowed-tools` and `evo.risk` are claims made by the package
author. They are not authorization decisions. Imported content remains
untrusted until it has passed provenance, licensing, evaluation, and human
review.

Do not execute bundled scripts during discovery or validation. A runtime
adapter must enforce its own server-side policy, safe resource paths,
isolation, and approval rules.
