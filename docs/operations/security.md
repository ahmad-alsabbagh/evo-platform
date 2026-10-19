# Security

Evo Platform treats prompts, skills, agents, workflows, tools, memory,
datasets, and model adapters as software that can affect behavior. Security
controls apply to both content and execution.

Security is ongoing work. It is not a status granted once when a capability is
published.

## Trust boundaries

Treat these sources as untrusted by default:

- User-provided documents and files.
- Web pages and retrieved content.
- Tool responses.
- Imported capabilities.
- External memory.
- Third-party dependencies.
- Generated code and configuration.

Untrusted content must not override system, developer, or policy instructions.

## Prompt and context injection

Capabilities should separate instructions from data, preserve source
boundaries, and be tested against adversarial content. Retrieved text should
include provenance and trust information before it enters an execution context.

## Tool security

Every tool should declare:

- Input and output schemas.
- Required permissions.
- Read and write side effects.
- Network and filesystem scope.
- Authentication requirements.
- Failure behavior.
- Approval requirements.

High-impact and destructive actions must be disabled by default and require
explicit authorization.

## Privacy

Capabilities should collect as little data as possible, avoid unnecessary
retention, and document data flows. Do not place sensitive data in public
datasets, traces, examples, or logs without an approved privacy process.

## Supply-chain security

Review imported capabilities for:

- License and provenance.
- Dependencies.
- Secrets.
- Suspicious scripts.
- Unexpected network access.
- Permission escalation.
- Obfuscated content.
- Conflicting or shadowed instructions.

Releases should support immutable digests, signed artifacts, software bills of
materials, and revocation.

## Sandboxing

Untrusted scripts, tools, and generated code should run in a restricted
environment with bounded resources, network controls, isolated credentials, and
explicit filesystem access.

## Provenance and audit

Record the source, author or publisher, version, parent artifact, dependencies,
evaluation context, approvals, and material changes. Record security-relevant
tool calls and policy decisions in an access-controlled audit trail.

## Human approval

Require human review for high-risk domains, external writes, destructive
actions, sensitive data processing, capability publication, and policy
exceptions.

## Incident response

Security incidents need a way to contain the problem, quarantine a capability,
rotate credentials, preserve evidence, decide on notifications, remediate the
issue, and update evaluations afterward.

## Release gates

Do not promote a capability when it has an unresolved critical vulnerability,
unverifiable provenance, missing license information, unauthorized side
effects, or a failed required safety evaluation.

Security claims apply to a specific version, runtime, configuration, and
evaluation coverage. They are not permanent guarantees.
