# Evaluation

## Purpose

Evaluation turns capability behavior into evidence. A capability must be evaluated against a declared task, dataset, runtime, model configuration, and version.

A score without its scope, dataset, evaluator, and execution context is not a portable quality claim.

## Evaluation layers

### Contract checks

Validate identifiers, versions, required fields, input schemas, output schemas, and manifest consistency.

### Deterministic checks

Use exact checks for structure, required fields, allowed values, regular expressions, citations, permissions, and forbidden actions.

### Semantic checks

Assess correctness, relevance, completeness, groundedness, reasoning quality, and usefulness through references, rubrics, or calibrated model judges.

### Safety checks

Test prompt injection, data exfiltration, unsafe tool use, privacy leakage, policy violations, and dangerous outputs.

### Operational checks

Measure latency, token usage, cost, retries, tool calls, failure recovery, and resource consumption.

### Human review

Use qualified reviewers for high-risk domains, ambiguous cases, evaluator calibration, and final production approval.

## Dataset types

- Development: used during iteration.
- Validation: held out from optimization decisions when possible.
- Regression: protects previously working behavior.
- Adversarial: targets safety and robustness weaknesses.
- Production-derived: anonymized cases reviewed for privacy and reuse.

Datasets must be versioned, documented, privacy-reviewed, and traceable to their source.

## Metrics

Metrics depend on the capability, but may include:

- Task success.
- Correctness.
- Completeness.
- Groundedness.
- Output contract compliance.
- Robustness.
- Safety.
- Privacy.
- Latency.
- Token usage.
- Cost.
- Tool-call accuracy.
- Human agreement.

Do not reduce a multi-objective capability to one score without preserving the underlying measurements.

## Promotion gates

A candidate may be promoted only when it satisfies the declared thresholds for quality, safety, compatibility, cost, and regression behavior.

```text
Draft
  -> Contract-valid
  -> Evaluated
  -> Safety-tested
  -> Human-reviewed when required
  -> Regression-passed
  -> Candidate
  -> Canary
  -> Promoted
```

Any critical safety regression blocks promotion regardless of quality improvement.

## Reproducibility

Every evaluation record should include:

- Capability and version.
- Dataset and split.
- Evaluator versions.
- Model and provider.
- Relevant configuration.
- Random seed when applicable.
- Tool and runtime versions.
- Timestamp.
- Cost and latency.
- Raw results or a privacy-safe reference.

## Evaluator limitations

Evaluators can be wrong, biased, or gamed. Use multiple signals, calibrate model-based judges against human review, and test evaluators with known positive and negative examples.
