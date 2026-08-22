# Interoperability

EvoPlatform keeps a native capability contract and exposes adapters at the boundary.

- MCP is used for tool and resource interoperability.
- Agent Skills are used for portable procedural knowledge and packaged instructions.
- API and CLI adapters provide host integration.
- OCI or archive packaging may carry immutable capability artifacts.

Adapters must preserve capability ID, version, permissions, provenance, license, evaluation references, and limitations. Unsupported features must be reported instead of silently dropped.
