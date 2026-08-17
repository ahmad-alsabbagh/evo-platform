from fastapi.testclient import TestClient

from evo_platform.api.app import app
from evo_platform.observability.logging import redact_sensitive


def test_request_id_is_returned() -> None:
    client = TestClient(app)
    response = client.get("/healthz", headers={"X-Request-ID": "test-request-001"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-001"


def test_request_id_is_generated() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_sensitive_fields_are_redacted() -> None:
    event = redact_sensitive(None, "info", {"token": "secret", "message": "safe"})
    assert event == {"token": "[REDACTED]", "message": "safe"}
