import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.embedding import TEIEmbeddingFunction
from mcp_server.knowledge_base import KnowledgeBase


# ── TEIEmbeddingFunction ───────────────────────────────────────────────────────

def make_emb_fn(embeddings_per_call=None):
    """Return a TEIEmbeddingFunction with a mocked OpenAI client."""
    fake_settings = MagicMock(tei_base_url="http://x", tei_model="test-model")
    with patch("mcp_server.embedding.OpenAI"):
        emb = TEIEmbeddingFunction(fake_settings)
    emb._model = "test-model"
    mock_item = MagicMock()
    mock_item.embedding = [0.1, 0.2, 0.3]
    emb._client = MagicMock()
    emb._client.embeddings.create.return_value = MagicMock(
        data=embeddings_per_call or [mock_item]
    )
    return emb


def test_tei_name():
    emb = make_emb_fn()
    assert emb.name() == "tei-embedding-function"


def test_tei_single_batch():
    mock_item = MagicMock()
    mock_item.embedding = [0.1, 0.2, 0.3]
    emb = make_emb_fn([mock_item] * 3)
    result = emb(["a", "b", "c"])
    assert len(result) == 3
    assert emb._client.embeddings.create.call_count == 1


def test_tei_batches_at_8():
    """20 inputs → 3 API calls: 8 + 8 + 4."""
    emb = make_emb_fn()

    def side_effect(input, model):
        return MagicMock(data=[MagicMock(embedding=[0.0])] * len(input))

    emb._client.embeddings.create.side_effect = side_effect

    result = emb(["text"] * 20)
    assert len(result) == 20
    assert emb._client.embeddings.create.call_count == 3


def test_tei_empty_input():
    emb = make_emb_fn([])
    result = emb([])
    assert result == []
    emb._client.embeddings.create.assert_not_called()


# ── KnowledgeBase.retrieve ─────────────────────────────────────────────────────

def make_kb(ids, documents, metadatas, distances=None):
    """Return a KnowledgeBase backed by mock collection and embedding function."""
    mock_emb = MagicMock(return_value=[[0.1, 0.2, 0.3]])
    mock_col = MagicMock()
    mock_col.query.return_value = {
        "ids": [ids],
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances] if distances else None,
    }
    return KnowledgeBase(collection=mock_col, emb=mock_emb)


def test_retrieve_returns_correct_shape():
    kb = make_kb(
        ids=["id_0", "id_1"],
        documents=["doc A", "doc B"],
        metadatas=[{"source": "NIST"}, {"source": "CIS"}],
        distances=[0.1, 0.3],
    )
    results = kb.retrieve("firewall", top_k=2)
    assert len(results) == 2
    assert results[0]["text"] == "doc A"
    assert results[0]["source"] == "NIST"
    assert results[0]["score"] == pytest.approx(0.1)


def test_retrieve_score_defaults_to_zero_when_no_distances():
    kb = make_kb(
        ids=["id_0"],
        documents=["doc A"],
        metadatas=[{"source": "NIST"}],
        distances=None,
    )
    results = kb.retrieve("test", top_k=1)
    assert results[0]["score"] == 0.0


def test_retrieve_passes_top_k():
    kb = make_kb(["id_0"], ["doc"], [{}], [0.0])
    kb.retrieve("query", top_k=7)
    kb.collection.query.assert_called_once_with(
        query_embeddings=[[0.1, 0.2, 0.3]], n_results=7
    )