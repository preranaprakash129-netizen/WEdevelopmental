import pytest

from app.conversation import get_store
from app.retrieval import reset_retriever_cache


@pytest.fixture(autouse=True)
def isolated_service_state(monkeypatch):
    """Each test starts in mock mode with an empty corpus cache and no history."""
    for name in ("ADVISORY_MODE", "ADVISORY_CORPUS_DIR", "BHASHINI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    reset_retriever_cache()
    get_store().clear()
    yield
    reset_retriever_cache()
    get_store().clear()
