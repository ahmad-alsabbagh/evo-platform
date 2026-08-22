# EvoPlatform Roadmap

## Roadmap principles

The roadmap prioritizes evidence, composability, security, and useful outcomes over feature count. Each phase should produce a usable artifact and a reviewable result.

The project is general-purpose. Domain packs are used to validate the core without making the platform dependent on one industry.

## Phase 0: Foundation

Status: in progress.

Deliverables:

- Vision and scope.
- Architecture principles.
- Capability model.
- Evaluation foundations.
- Security foundations.
- Initial repository conventions.

Exit criteria:

- Core concepts are documented.
- Non-goals and boundaries are explicit.
- No external implementation is copied into the repository.

## Phase 1: Contracts and schemas

Deliverables:

- Capability manifest schema.
- Evaluation record schema.
- Provenance schema.
- Tool permission schema.
- Output contract examples.
- Schema validation tests.

Exit criteria:

- Example artifacts validate successfully.
- Invalid artifacts fail with actionable errors.
- Version and provenance requirements are testable.

## Phase 2: Reference capabilities

Deliverables:

- A small set of original capabilities from different domains.
- Input and output examples.
- Development datasets.
- Basic deterministic evaluators.
- Documented limitations.

Initial domains may include research, coding, and business or data analysis.

Exit criteria:

- Each capability has a complete manifest.
- Each capability has at least one evaluation path.
- Results can be reproduced from documented inputs and configuration.

## Phase 3: Evaluation and safety runtime

Deliverables:

- Dataset runner.
- Contract and output validation.
- Regression testing.
- Safety test harness.
- Cost and latency measurement.
- Privacy-safe trace references.

Exit criteria:

- A candidate can be evaluated consistently.
- Critical safety failures block promotion.
- Evaluation reports preserve scope and configuration.

## Phase 4: Capability runtime

Deliverables:

- Model adapter interface.
- Context assembly.
- Workflow execution.
- Tool interface and permission checks.
- Human approval hooks.
- Error and retry policies.

Exit criteria:

- A capability can run through a documented adapter.
- Tool side effects are visible and bounded.
- Failed runs do not claim successful execution.

## Phase 5: Registry and local distribution

Deliverables:

- Versioned capability registry.
- Search and metadata index.
- CLI for validation and local execution.
- Import and export formats.
- Local or self-hosted operation.

Exit criteria:

- Users can discover, validate, run, and version capabilities locally.
- Registry records preserve provenance and lifecycle state.

## Phase 6: Standards interoperability

Deliverables:

- Agent Skills compatibility.
- MCP integration.
- Agent Plugin compatibility where appropriate.
- OCI packaging exploration.
- Model and runtime adapters.

Exit criteria:

- A capability can be exported to supported formats without losing its contract or security metadata.
- Unsupported features are reported explicitly.

## Phase 7: Controlled evolution

Deliverables:

- Candidate generation interface.
- Baseline and validation comparison.
- Evolution records.
- Optimizer integrations such as reflective or search-based methods.
- Human and policy approval gates.
- Rollback support.

Exit criteria:

- No candidate is promoted solely on development-set improvement.
- Regression and safety thresholds are enforced.
- Every accepted change has a lineage record.

## Phase 8: Hosted and enterprise operation

Deliverables:

- Multi-tenant boundaries.
- Identity and access control.
- Audit and retention policies.
- Private registries.
- Deployment and release controls.
- Operational dashboards.

Exit criteria:

- Tenant data is isolated.
- Administrative actions are auditable.
- High-risk capabilities have enforceable policies.

## Phase 9: Curated ecosystem

Deliverables:

- Contributor publishing workflow.
- License and provenance intake.
- Security review process.
- Verified capability listings.
- Partner and enterprise packs.
- Commercial distribution experiments.

This phase is intentionally later than the registry and runtime phases. A marketplace should follow demonstrated utility and trust, not precede them.

## Current focus

The immediate focus is Phase 0 and Phase 1: complete the foundation documents, add schemas, and create validation examples before implementing a large runtime or marketplace.
