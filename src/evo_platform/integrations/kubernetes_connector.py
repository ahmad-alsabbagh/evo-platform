"""Read-only Kubernetes diagnostics connector.

Credentials and the allowed-tool list are server-owned configuration. This
connector exposes narrow diagnostic operations only; it never provides shell
execution, secret access, or write access to the cluster.
"""
from __future__ import annotations

from typing import Any

import httpx


class KubernetesConnectorError(RuntimeError):
    """Raised when a Kubernetes API request fails or returns an unexpected response."""


class KubernetesConnector:
    """Read-only diagnostics client for a Kubernetes API server."""

    ALLOWED_TOOLS = frozenset(
        {
            "k8s_list_pods",
            "k8s_get_pod_events",
            "k8s_get_deployment_status",
        }
    )

    def __init__(
        self,
        *,
        name: str,
        api_server: str,
        service_account_token: str,
        allowed_tools: list[str],
        client: httpx.Client | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        if not name:
            raise ValueError("Connector name is required")
        if not api_server:
            raise ValueError("Kubernetes API server URL is required")
        if not service_account_token:
            raise ValueError("A service account token reference is required")
        if not allowed_tools:
            raise ValueError("At least one explicitly allowed tool is required")

        invalid = set(allowed_tools) - self.ALLOWED_TOOLS
        if invalid:
            raise ValueError(f"Unsupported or unsafe tools: {sorted(invalid)}")

        self.name = name
        self.api_server = api_server.rstrip("/")
        self.allowed_tools = frozenset(allowed_tools)
        self.timeout_s = timeout_s
        self._client = client or httpx.Client(
            base_url=self.api_server,
            headers={
                "Authorization": f"Bearer {service_account_token}",
                "Accept": "application/json",
            },
            timeout=timeout_s,
        )

    def _require_tool(self, tool_name: str) -> None:
        if tool_name not in self.allowed_tools:
            raise PermissionError(f"Tool '{tool_name}' is not enabled for connector '{self.name}'")

    def _request(self, tool_name: str, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        self._require_tool(tool_name)
        try:
            response = self._client.get(path, params=params or {})
        except httpx.HTTPError as exc:
            raise KubernetesConnectorError(f"Kubernetes API request failed: {exc}") from exc

        if response.status_code >= 400:
            raise KubernetesConnectorError(
                f"Kubernetes API returned {response.status_code} for {path}"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise KubernetesConnectorError("Kubernetes API returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise KubernetesConnectorError("Kubernetes API returned an unexpected payload")
        return payload

    def list_pods(
        self, *, namespace: str, label_selector: str | None = None
    ) -> dict[str, Any]:
        if not namespace:
            raise ValueError("Namespace is required")
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        return self._request(
            "k8s_list_pods",
            f"/api/v1/namespaces/{namespace}/pods",
            params=params,
        )

    def get_pod_events(self, *, namespace: str, pod_name: str) -> dict[str, Any]:
        if not namespace or not pod_name:
            raise ValueError("Namespace and pod name are required")
        return self._request(
            "k8s_get_pod_events",
            f"/api/v1/namespaces/{namespace}/events",
            params={
                "fieldSelector": f"involvedObject.name={pod_name},involvedObject.namespace={namespace}",
            },
        )

    def get_deployment_status(self, *, namespace: str, name: str) -> dict[str, Any]:
        if not namespace or not name:
            raise ValueError("Namespace and deployment name are required")
        return self._request(
            "k8s_get_deployment_status",
            f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}",
        )
