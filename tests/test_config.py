import os

from src.config import Settings


def test_settings_default():
    """Test that default settings are loaded correctly."""
    os.environ["GOOGLE_API_KEY"] = "fake-key"
    os.environ["LLM_MODEL"] = "gemini-2.0-flash"
    os.environ["EMBEDDING_MODEL"] = "text-embedding-004"
    os.environ["ENABLE_GOOGLE_SEARCH"] = "true"

    settings = Settings()
    assert settings.google_api_key == "fake-key"
    assert settings.llm_model == "gemini-2.0-flash"
    assert settings.embedding_model == "text-embedding-004"
    assert settings.enable_google_search is True
    assert settings.google_cloud_location == "europe-west1"
