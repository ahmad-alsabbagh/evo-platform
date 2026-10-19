# Documentation

Evo Platform runs AI agents with authorization, audit logging, and support for
local language models.

## Common tasks

- [Architecture](architecture.md) explains how the platform fits together.
- [Homelab integration](how-to/integrations/homelab.md) explains how to connect
  agents to Kubernetes, Proxmox, monitoring, Home Assistant, MCP services, or
  cloud providers.
- [Agent Skills](skills/agent-skills.md) covers skill packages and validation.
- [Skill Runner](skills/skill-runner.md) covers skill-aware agent execution.

## Operations

- [Security](operations/security.md)
- [Evaluation](operations/evaluation.md)
- [Roadmap](operations/roadmap.md)

## Explanation

- [Capability model](explanation/capability-model.md)
- [Interoperability](explanation/interoperability.md)
- [Artifact lineage](explanation/lineage.md)
- [Experimentation and rollouts](explanation/experimentation.md)
- [Vision](explanation/vision.md)
- [Production engineering baseline](explanation/production-baseline.md)

## Conventions

Documentation is kept beside the code and reviewed in pull requests. Each page
answers one question. Credentials, authorization decisions, and destructive
operations are handled by the server, not by the model or the user request.
