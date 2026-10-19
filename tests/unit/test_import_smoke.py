def test_application_imports() -> None:
    from evo_platform.api.app import app

    assert app.title == "evo-platform"
