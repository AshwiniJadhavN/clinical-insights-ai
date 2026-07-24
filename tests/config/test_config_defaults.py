from backend.config import Settings


def test_settings_load_non_secret_defaults_from_yaml_config() -> None:
    settings = Settings(database_url="sqlite:///./data/test.db")

    assert settings.embedding_model == "all-MiniLM-L6-v2"
    assert settings.chunk_size == 512
    assert settings.sync_mode == "DUAL_WRITE"
    assert settings.log_level == "INFO"
