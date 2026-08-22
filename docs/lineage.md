# Artifact Lineage

Every production claim must be reconstructible through a lineage graph:

```text
CapabilityVersion -> ModelVersion -> ToolVersion -> DatasetVersion
       -> EvaluatorVersion -> EvaluationRun -> PromotionDecision
       -> Experiment -> Rollout -> Release
```

Each edge records a relationship, digest, timestamp, actor, and source reference. Promotion decisions retain the policy version and policy snapshot hash, evaluation run, artifact digest, reasons, and actor. Audit records are append-only; corrected decisions create a new record rather than mutating history.
