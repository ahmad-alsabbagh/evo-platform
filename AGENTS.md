# EvoPlatform Agent Instructions

## Verification

Before considering a change complete, run the smallest relevant checks and then the full CI-equivalent suite when possible:

- `python -c "from evo_platform.api.app import app"`
- `ruff check .`
- `mypy src`
- `pytest -m "not integration"`
- `pytest -m integration`
- `python -m jsonschema` or the repository schema tests.

## Contract rules

- Every capability, evaluation, trace, experiment, and promotion decision is versioned.
- A catalog entry must reference an evaluation run before publication.
- Promotion is deny-by-default and cannot be inferred from catalog storage.
- Changes to schemas require valid and invalid fixtures.
- Changes to migrations require upgrade, downgrade, and round-trip tests.
- Side-effecting tools require explicit policy authorization.

## Review rules

- Do not merge with unresolved import, migration, security, or reproducibility failures.
- Keep audit records append-only.
- Preserve artifact digests, policy versions, dataset hashes, and evaluator versions.
- Update documentation when contracts or lifecycle behavior changes.
