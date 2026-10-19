# Connecting Evo Platform to a Homelab or Service Provider

Evo Platform connects to infrastructure through **server-registered tools**,
not by giving an agent direct access to servers, clusters, or provider APIs.

A tool is a narrow, typed operation with an explicit authorization requirement.
The agent can request a tool; the platform decides whether that request is
allowed, requires human approval, or is denied.

## Integration model

```text
User request
  -> AgentRunner / SkillAgentRunner
  -> Registered tool adapter
  -> Homelab service or provider API
  -> Scoped result returned to the agent
```

Rules:

- Credentials live in server configuration or a secret store, never in prompts,
  skill files, request bodies, or model context.
- Tools declare their scope: read-only, approval-required, or denied.
- Agents receive only the minimum data needed for the task.
- Destructive operations must require explicit human approval.
- A tool failure is returned as a structured error; it must not be interpreted
  as successful task completion.

## Supported connection patterns

| Target | Connection method | Recommended initial scope |
|---|---|---|
| Kubernetes / Talos | Kubernetes API through a dedicated ServiceAccount | Read pods, events, deployments, nodes |
| Proxmox VE | Proxmox API token | Read VMs, nodes, storage, tasks |
| Prometheus / Grafana | HTTP API with scoped credentials | Read alerts, metrics, dashboards |
| Home Assistant | Long-lived access token | Read states; automate only with approval |
| MCP-compatible services | MCP client/server integration | Depends on the exposed MCP tools |
| Cloud providers | Provider SDK/API with least-privilege credentials | Read-only inventory and health first |

## Kubernetes / Talos example

Create a dedicated ServiceAccount with read-only access. Do not reuse an
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

Expose only narrow tools to the agent, for example:

- `k8s_list_pods`
- `k8s_get_pod_events`
- `k8s_get_deployment_status`
- `k8s_get_node_summary`

Do not expose `kubectl exec`, arbitrary command execution, secret reading,
or cluster-wide write operations.

## Proxmox VE example

Use a dedicated Proxmox API token with the minimum privileges required.

Recommended initial tools:

- `proxmox_list_nodes`
- `proxmox_list_vms`
- `proxmox_get_vm_status`
- `proxmox_list_storage`
- `proxmox_get_task_status`

Operations such as VM shutdown, migration, snapshot deletion, or configuration
changes must be approval-gated and should never be exposed as general-purpose
commands.

## Monitoring example

For Prometheus or Grafana, start with read-only API access.

Useful tools:

- `prom_query`
- `prom_get_alerts`
- `grafana_search_dashboards`
- `grafana_get_dashboard`

The agent can answer questions such as:

> Which services have elevated error rates in the last hour?

It should not be able to modify dashboards, silence alerts, or change data
sources unless that capability is explicitly implemented and approved.

## Home Assistant example

Use a long-lived access token limited to the required integration.

Recommended initial tools:

- `ha_get_state`
- `ha_list_entities`
- `ha_get_automation`

Actions such as turning devices on or off, unlocking doors, or changing climate
settings must require approval and should be constrained to explicitly allowed
entity IDs.

## MCP integration

For services exposing Model Context Protocol tools, register the MCP server as
a provider and expose only selected tools to Evo Platform.

Do not forward every MCP tool automatically. Review each tool for:

- Data exposure
- Write or destructive behavior
- Authentication scope
- Cost or rate limits
- Whether its output may contain credentials or private data

## Registering a connector

A connector should be configured on the server, for example:

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

Then bind selected tools to an agent configuration:

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

The allowed tool list is server-owned configuration. A client request must not
be able to add tools, replace credentials, or increase its authorization tier.

## Authorization levels

| Level | Examples | Platform behavior |
|---|---|---|
| Read-only | List pods, read VM status, query metrics | Execute and audit |
| Approval-required | Restart deployment, migrate VM, toggle device | Park in approval queue |
| Denied | Read secrets, execute shell, delete storage | Reject before execution |

Use `OBSERVE` for read-only dashboards, `RECOMMEND` for advice-only workflows,
and `ACT_WITH_APPROVAL` for any state-changing operation.

## Example: homelab diagnostic agent

A safe first integration is a diagnostic agent that can investigate but not
modify the homelab.

User asks:

> Why is the vLLM pod pending?

Agent flow:

1. Calls `k8s_list_pods` for the relevant namespace.
2. Calls `k8s_get_pod_events` for the pending pod.
3. Reads recent events and node capacity.
4. Returns a diagnosis and a recommended action.
5. If the recommendation is `restart deployment`, it does **not** execute it;
   it creates an approval request instead.

This keeps the agent useful without granting it infrastructure control.

## Security checklist

Before enabling a connector:

- Use a dedicated credential or ServiceAccount per integration.
- Grant the minimum permissions and resources.
- Keep credentials in a secret manager or Kubernetes Secret, not in Git.
- Restrict network access to the required service endpoints.
- Audit every tool invocation, including denied attempts.
- Require approval for any write or destructive action.
- Do not place credentials, tokens, or raw infrastructure output containing
  secrets into model context.
- Review tool outputs for sensitive data before storing or displaying them.

## Current implementation status

This document describes the intended integration boundary. The repository
already contains the execution, authorization, approval, audit, and provider
layers; production connectors must be implemented and tested separately.

Do not enable infrastructure access until a connector has explicit tests,
least-privilege credentials, audit coverage, and approval handling for every
state-changing operation.
