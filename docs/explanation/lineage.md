# Artifact lineage

Every production claim should be reconstructible through a lineage graph:

```text
CapabilityVersion -> ModelVersion -> ToolVersion -> DatasetVersion
       -> EvaluatorVersion -> EvaluationRun -> PromotionDecision
       -> Experiment -> Rollout -> Release
```

Each edge records a relationship, digest, timestamp, actor, and source
reference.

Promotion decisions keep the policy version and policy snapshot hash, evaluation
run, artifact digest, reasons, and actor. Audit records are append-only. A
corrected decision creates a new record instead of changing history.
