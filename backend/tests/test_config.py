from app.config import get_settings


def test_get_settings_has_database_url() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert isinstance(settings.database_url, str)
    assert settings.database_url != ""
