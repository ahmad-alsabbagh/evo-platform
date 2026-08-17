from evo_platform.observability.logging import redact_sensitive


def test_nested_sensitive_values_are_redacted() -> None:
    event = redact_sensitive(None, "info", {"payload": {"Prompt": "secret", "items": [{"token": "abc"}]}})
    assert event["payload"]["Prompt"] == "[REDACTED]"
    assert event["payload"]["items"][0]["token"] == "[REDACTED]"
