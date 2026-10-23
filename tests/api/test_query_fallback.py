from __future__ import annotations

from backend.api import query as query_api
from backend.config import Settings
from backend.rag.embedder import FakeEmbedder
from backend.rag.generator import FakeGenerator
from backend.rag.retriever import FakeRetriever


def test_get_query_service_falls_back_to_fake_generator_when_llm_key_missing(monkeypatch):
    settings = Settings(
        database_url="sqlite:///./data/test.db",
        openai_api_key="",
        anthropic_api_key="",
    )

    retriever = FakeRetriever()
    monkeypatch.setattr(query_api, "create_generator", lambda _settings: (_ for _ in ()).throw(ValueError("OpenAI API key is required.")))
    monkeypatch.setattr(query_api, "_get_embedder_or_503", lambda: FakeEmbedder())
    monkeypatch.setattr(query_api, "_get_retriever_or_503", lambda _settings: retriever)

    service = query_api.get_query_service(settings)

    assert isinstance(service._generator, FakeGenerator)


def test_mock_mode_reuses_initialized_retriever(monkeypatch):
    settings = Settings(
        database_url="sqlite:///./data/test.db",
        mock_llm=True,
    )
    retriever = FakeRetriever()
    embedder = FakeEmbedder()
    monkeypatch.setattr(query_api, "_get_embedder_or_503", lambda: embedder)
    monkeypatch.setattr(query_api, "_get_retriever_or_503", lambda _settings: retriever)

    first = query_api.get_query_service(settings)
    second = query_api.get_query_service(settings)

    assert first._retriever is retriever
    assert second._retriever is retriever
    assert first._embedder is embedder
