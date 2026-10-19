# Connecting Evo Platform to a homelab or service provider

Evo Platform connects to infrastructure through tools registered on the server.
An agent does not get direct access to servers, clusters, or provider APIs.

A tool is a small, specific operation with its own authorization rule. The
agent can ask to use a tool. The platform then allows it, requires approval, or
rejects it.

## How connections work

```text
User request
  -> AgentRunner or SkillAgentRunner
  -> Registered tool
  -> Homelab service or provider API
  -> Result returned to the agent
```

A few rules apply to every connection:

- Credentials are stored in server configuration or a secret store. They are
  never placed in prompts, skill files, or request bodies.
- Each tool has a clear scope: read-only, approval required, or denied.
- The agent receives only the data it needs.
- Destructive operations require human approval.
- A failed tool call is reported as a failure. It is never treated as a
  completed task.

## Supported connections

| Target | Connection method | Start with |
|---|---|---|
| Kubernetes or Talos | Kubernetes API with a dedicated ServiceAccount | Read pods, events, deployments, and nodes |
| Proxmox VE | Proxmox API token | Read VMs, nodes, storage, and tasks |
| Prometheus or Grafana | HTTP API | Read alerts, metrics, and dashboards |
| Home Assistant | Long-lived access token | Read entity states |
| MCP-compatible services | MCP client | Only reviewed tools |
| Cloud providers | Provider API with limited credentials | Read-only inventory and health |

## Kubernetes and Talos

Use a dedicated ServiceAccount with read-only permissions. Do not reuse an
administrator kubeconfig.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: evo-platform-readonly
  namespace: evo-platform
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: evo-platform-readonly
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "events", "services", "nodes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: evo-platform-readonly
subjects:
  - kind: ServiceAccount
    name: evo-platform-readonly
    namespace: evo-platform
roleRef:
  kind: ClusterRole
  name: evo-platform-readonly
  apiGroup: rbac.authorization.k8s.io
```

Expose only narrow tools, such as:

- `k8s_list_pods`
- `k8s_get_pod_events`
- `k8s_get_deployment_status`
- `k8s_get_node_summary`

Do not expose `kubectl exec`, arbitrary command execution, secret access, or
cluster-wide write permissions.

## Proxmox VE

Use a dedicated API token with the smallest set of privileges needed.

Useful read-only tools include:

- `proxmox_list_nodes`
- `proxmox_list_vms`
- `proxmox_get_vm_status`
- `proxmox_list_storage`
- `proxmox_get_task_status`

Shutting down a VM, migrating it, deleting a snapshot, or changing its
configuration must require approval. These operations should not be exposed as
general-purpose commands.

## Monitoring

For Prometheus or Grafana, begin with read-only API access.

Useful tools include:

- `prom_query`
- `prom_get_alerts`
- `grafana_search_dashboards`
- `grafana_get_dashboard`

This allows an agent to answer questions such as:

> Which services had a higher error rate in the last hour?

It should not be able to change dashboards, silence alerts, or modify data
sources unless that is explicitly implemented and approved.

## Home Assistant

Use a long-lived access token limited to the required integration.

Useful read-only tools include:

- `ha_get_state`
- `ha_list_entities`
- `ha_get_automation`

Turning devices on or off, unlocking doors, or changing climate settings must
require approval. Restrict these actions to explicitly allowed entity IDs.

## MCP services

For services that expose Model Context Protocol tools, register the MCP server
as a provider and expose only the tools you have reviewed.

Do not forward every MCP tool automatically. Check each one for data exposure,
write or destructive behavior, authentication scope, cost, rate limits, and
whether its output may contain private data.

## Registering a connector

A connector is configured on the server:

```python
connector = KubernetesConnector(
    name="homelab-k8s",
    api_server="https://kubernetes.default.svc",
    service_account_token_ref="evo-platform-readonly-token",
    allowed_tools=[
        "k8s_list_pods",
        "k8s_get_pod_events",
        "k8s_get_deployment_status",
    ],
)
```

Then bind the allowed tools to an agent:

```python
agent = AgentConfig(
    agent_id="homelab-diagnostic",
    allowed_tools=[
        "k8s_list_pods",
        "k8s_get_pod_events",
        "k8s_get_deployment_status",
    ],
)
```

The allowed tool list belongs to server configuration. A client request cannot
add tools, replace credentials, or raise its authorization level.

## Authorization levels

| Level | Examples | Behavior |
|---|---|---|
| Read-only | List pods, read VM status, query metrics | Run and audit |
| Approval required | Restart a deployment, migrate a VM, toggle a device | Wait for approval |
| Denied | Read secrets, run shell commands, delete storage | Reject before execution |

Use `OBSERVE` for read-only dashboards, `RECOMMEND` for advice-only workflows,
and `ACT_WITH_APPROVAL` for anything that changes state.

## Example: homelab diagnostic agent

A good first integration is a diagnostic agent that can investigate the
homelab but cannot change it.

For example, a user asks:

> Why is the vLLM pod pending?

The agent can:

1. List pods in the relevant namespace.
2. Read events for the pending pod.
3. Check recent events and node capacity.
4. Explain the likely cause and recommend a fix.

If the recommendation is to restart a deployment, the agent does not run it.
It creates an approval request instead.

## Security checklist

Before enabling a connector:

- Use a separate credential or ServiceAccount for each integration.
- Grant only the permissions and resources needed.
- Store credentials in a secret manager or Kubernetes Secret, not in Git.
- Restrict network access to the required endpoints.
- Audit every tool call, including rejected ones.
- Require approval for writes and destructive actions.
- Keep credentials and sensitive infrastructure output out of model context.

## Implementation status

This document describes the intended integration boundary. The repository
includes the execution, authorization, approval, audit, and provider layers.
Production connectors still need to be implemented and tested separately.

Do not enable infrastructure access until a connector has tests, limited
credentials, audit coverage, and approval handling for every state-changing
operation.
