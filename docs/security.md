# Security Foundations

## Security posture

EvoPlatform treats prompts, skills, agents, workflows, tools, memory, datasets, and model adapters as potentially influential software artifacts. Security controls apply to both content and execution.

Security is a lifecycle property, not a badge granted once at publication.

## Trust boundaries

The following sources are untrusted by default:

- User-provided documents and files.
- Web pages and retrieved content.
- Tool responses.
- Imported capabilities.
- External memory.
- Third-party dependencies.
- Generated code and generated configuration.

Untrusted content must not override system, developer, or policy instructions.

## Prompt and context injection

Capabilities must distinguish instructions from data, preserve source boundaries, and test adversarial content. Retrieved text should be labeled with provenance and trust metadata before it enters an execution context.

## Tool security

Every tool must declare:

- Input and output schemas.
- Required permissions.
- Read and write side effects.
- Network and filesystem scope.
- Authentication requirements.
- Failure behavior.
- Approval requirements.

High-impact and destructive actions must be disabled by default and require explicit authorization.

## Privacy

Capabilities must minimize data collection, avoid unnecessary retention, and document data flows. Sensitive data must not be placed in public datasets, traces, examples, or logs without an approved privacy process.

## Supply-chain security

Imported capabilities should be inspected for:

- License and provenance.
- Dependencies.
- Secrets.
- Suspicious scripts.
- Unexpected network access.
- Permission escalation.
- Obfuscated content.
- Conflicting or shadowed instructions.

Releases should support immutable digests, signed artifacts, software bills of materials, and revocation.

## Sandboxing

Untrusted scripts, tools, and generated code should run in a restricted environment with bounded resources, network controls, isolated credentials, and explicit filesystem access.

## Provenance and audit

Record the source, author or publisher, version, parent artifact, dependencies, evaluation context, approvals, and material changes. Record security-relevant tool calls and policy decisions in an access-controlled audit trail.

## Human approval

Require human review for high-risk domains, external writes, destructive actions, sensitive data processing, capability publication, and policy exceptions.

## Incident response

Security incidents must support containment, capability quarantine, credential rotation, evidence preservation, notification decisions, remediation, and post-incident evaluation updates.

## Release gates

A capability must not be promoted when it has an unresolved critical vulnerability, unverifiable provenance, missing license information, unauthorized side effects, or a failed mandatory safety evaluation.

Security claims are scoped to a version, runtime, configuration, and evaluation coverage. They are not permanent guarantees.
