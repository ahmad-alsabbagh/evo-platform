"""Offline tests for the read-only Kubernetes diagnostics connector."""
import unittest
from unittest.mock import Mock

from evo_platform.integrations.kubernetes_connector import (
    KubernetesConnector,
    KubernetesConnectorError,
)


def response(status_code=200, payload=None):
    mock = Mock()
    mock.status_code = status_code
    mock.json.return_value = payload if payload is not None else {}
    return mock


class KubernetesConnectorTests(unittest.TestCase):
    def setUp(self):
        self.http = Mock()
        self.connector = KubernetesConnector(
            name="homelab-k8s",
            api_server="https://kubernetes.example",
            service_account_token="server-owned-token",
            allowed_tools=[
                "k8s_list_pods",
                "k8s_get_pod_events",
                "k8s_get_deployment_status",
            ],
            client=self.http,
        )

    def test_list_podsUsesScopedPathAndSelector(self):
        self.http.get.return_value = response({"items": []})
        result = self.connector.list_pods(namespace="ai", label_selector="app=vllm")
        self.assertEqual(result, {"items": []})
        args, kwargs = self.http.get.call_args
        self.assertEqual(args[0], "/api/v1/namespaces/ai/pods")
        self.assertEqual(kwargs["params"], {"labelSelector": "app=vllm"})

    def test_get_pod_eventsUsesFieldSelector(self):
        self.http.get.return_value = response({"items": []})
        self.connector.get_pod_events(namespace="ai", pod_name="vllm-0")
        args, kwargs = self.http.get.call_args
        self.assertEqual(args[0], "/api/v1/namespaces/ai/events")
        self.assertIn("involvedObject.name=vllm-0", kwargs["params"]["fieldSelector"])

    def test_get_deployment_statusUsesAppsApi(self):
        self.http.get.return_value = response({"metadata": {"name": "vllm"}})
        result = self.connector.get_deployment_status(namespace="ai", name="vllm")
        self.assertEqual(result["metadata"]["name"], "vllm")
        args, _ = self.http.get.call_args
        self.assertEqual(args[0], "/apis/apps/v1/namespaces/ai/deployments/vllm")

    def test_disallowed_tool_is_rejected(self):
        connector = KubernetesConnector(
            name="homelab-k8s",
            api_server="https://kubernetes.example",
            service_account_token="server-owned-token",
            allowed_tools=["k8s_list_pods"],
            client=self.http,
        )
        with self.assertRaises(PermissionError):
            connector.get_pod_events(namespace="ai", pod_name="vllm-0")
        self.http.get.assert_not_called()

    def test_unsafe_tool_is_rejected_at_configuration(self):
        with self.assertRaises(ValueError):
            KubernetesConnector(
                name="homelab-k8s",
                api_server="https://kubernetes.example",
                service_account_token="server-owned-token",
                allowed_tools=["k8s_exec_pod"],
                client=self.http,
            )

    def test_api_error_is_structured(self):
        self.http.get.return_value = response(status_code=403, payload={})
        with self.assertRaises(KubernetesConnectorError):
            self.connector.list_pods(namespace="ai")

    def test_missing_credentials_rejected(self):
        with self.assertRaises(ValueError):
            KubernetesConnector(
                name="homelab-k8s",
                api_server="https://kubernetes.example",
                service_account_token="",
                allowed_tools=["k8s_list_pods"],
                client=self.http,
            )


if __name__ == "__main__":
    unittest.main()
