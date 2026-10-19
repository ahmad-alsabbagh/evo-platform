# Capability model

A capability is a versioned, testable unit that lets an AI system perform a
defined task with explicit inputs, outputs, policies, and operational limits.

A capability can be a single prompt or a composed system. It should describe
what it does, what it needs, what it produces, and how it is evaluated.

## Capability types

### Prompt

A reusable instruction or message template. A prompt should declare its
variables, intended behavior, output expectations, and known limitations.

### Skill

A portable package of instructions, resources, and optional scripts that teaches
an agent a specialized procedure or domain capability.

### Agent

An execution component that interprets goals, selects actions, uses tools,
manages context, and produces results under policy.

### Workflow

An explicit graph or sequence of steps connecting prompts, agents, tools,
memory, validators, and human approvals.

### Tool

A callable interface to an external action or data source. Tools must declare
permissions, input and output schemas, side effects, and failure behavior.

### Evaluator

A deterministic, model-based, or human procedure that scores outputs or traces
against defined criteria.

### Policy

A rule set that limits data access, tool use, safety behavior, privacy,
retention, promotion, or deployment.

### Dataset

A versioned collection of examples used for development, evaluation, regression
testing, or safety testing.

### Adapter

A translation layer that maps a capability contract to a model provider,
runtime, protocol, or host application.

### Memory

A governed store of facts, experiences, procedures, or context that a
capability may read or update under explicit retention and privacy rules.

## Required contract

Every distributable capability should declare:

- Stable identifier and version.
- Purpose and intended users.
- Inputs and validation rules.
- Outputs and output schema.
- Required context and dependencies.
- Tools and permissions.
- Memory behavior.
- Safety and privacy requirements.
- Evaluation datasets and metrics.
- Supported runtimes or model adapters.
- Provenance and license information.
- Known limitations.

## Composition

Capabilities can be composed without losing their individual identities:

```text
Workflow
  -> Prompt or Skill
  -> Context or Memory
  -> Agent
  -> Tool
  -> Evaluator
  -> Human approval
```

Composition must preserve provenance, permissions, and evaluation boundaries.
A composed capability must not silently inherit broader permissions than its
components need.

## Lifecycle

```text
Draft
  -> Normalized
  -> Scanned
  -> Evaluated
  -> Reviewed
  -> Candidate
  -> Canary
  -> Promoted
  -> Deprecated
  -> Revoked
```

Promotion requires passing the applicable quality, safety, licensing,
compatibility, and regression gates.

## Trust levels

- Unverified: imported or newly created without enough evidence.
- Inspected: metadata, licenses, dependencies, and permissions reviewed.
- Evaluated: test datasets and metrics are available.
- Reviewed: a qualified person reviewed the capability.
- Verified: quality and safety gates passed for a declared scope.
- Production: approved for a defined runtime and operational environment.

Trust applies to a version, runtime, model set, dataset, and declared use case.
It is not a permanent guarantee.

## Versioning

Changes to behavior, permissions, tools, schemas, dependencies, or evaluation
results require a new version. Releases should keep lineage to their parent and
record why the change was made.
