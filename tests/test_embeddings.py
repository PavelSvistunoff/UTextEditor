"""Embedding protocol validation without Ollama or network access."""

from dataclasses import replace
from unittest.mock import patch

import pytest

from app.ai.embeddings import EmbeddingError, EmbeddingIdentity, embedding_input, normalized_vector
from app.ai.ollama_client import OllamaClient, OllamaError
from test_ollama_client import response_with


def model_metadata(dimensions=3):
    return {"capabilities": ["embedding"], "model_info": {"general.architecture": "test", "test.embedding_length": dimensions}}


def test_identity_uses_installed_digest_and_embedding_capability():
    client = OllamaClient(model="test")
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with({"models": [{"name": "test:latest", "digest": "digest-v1"}]})), patch.object(client, "_post", return_value=model_metadata()):
        assert client.embedding_identity() == EmbeddingIdentity(client.host, "test:latest", "digest-v1", 3)


@pytest.mark.parametrize("metadata", [{}, {"models": []}, {"models": [None]}, {"models": [{"name":"test:latest"}]}])
def test_missing_malformed_model_identity_refuses_without_pulling(metadata):
    client = OllamaClient(model="test")
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with(metadata)), patch.object(client, "_post", return_value=model_metadata()):
        with pytest.raises(EmbeddingError):
            client.embedding_identity()


def test_generation_only_model_is_not_assumed_to_support_embeddings():
    client = OllamaClient(model="gemma4:12b")
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with({"models": [{"name":"gemma4:12b", "digest":"generation"}]})), patch.object(client, "_post", return_value={"capabilities":["completion"]}):
        with pytest.raises(EmbeddingError, match="embedding support"):
            client.embedding_identity()


def test_embed_uses_separate_model_endpoint_no_truncation_and_normalizes():
    client = OllamaClient(host="https://embedding.example", model="test")
    identity = EmbeddingIdentity(client.host, "test:latest", "v1", 3)
    with patch.object(client, "embedding_identity", return_value=identity), patch.object(client, "_post", return_value={"model":"test:latest", "embeddings":[[0,3,4]]}) as post:
        assert client.embed(("story text",), identity) == ((0.0, 0.6, 0.8),)
        post.assert_called_once_with("/api/embed", {"model":"test:latest", "input":["story text"], "truncate":False})


@pytest.mark.parametrize("values", [[], [[1,0]], [[0,0,0]], [[True,0,1]], [[float("nan"),1,0]], [[float("inf"),1,0]], [["x",1,0]], [[1,0,0],[1,0,0]]])
def test_embed_rejects_invalid_partial_and_mismatched_vectors(values):
    client = OllamaClient(model="test")
    identity = EmbeddingIdentity(client.host, "test:latest", "v1", 3)
    with patch.object(client, "embedding_identity", return_value=identity), patch.object(client, "_post", return_value={"model":"test", "embeddings":values}):
        with pytest.raises(EmbeddingError):
            client.embed(("story text",), identity)


@pytest.mark.parametrize("stage", ["before", "after"])
def test_mutable_model_tag_is_checked_on_both_sides_of_embed(stage):
    client = OllamaClient(model="test")
    identity = EmbeddingIdentity(client.host, "test:latest", "v1", 3)
    changed = replace(identity, digest="v2")
    with patch.object(client, "embedding_identity", side_effect=[changed] if stage == "before" else [identity, changed]), patch.object(client, "_post", return_value={"model":"test", "embeddings":[[1,0,0]]}) as post:
        with pytest.raises(EmbeddingError, match="model changed"):
            client.embed(("text",), identity)
        assert post.call_count == (stage == "after")


@pytest.mark.parametrize("texts", [(), ("",), ("x"*8193,), ("x",)*9, ("x"*8192,)*8])
def test_input_limits_refuse_before_network(texts):
    client = OllamaClient(model="test")
    identity = EmbeddingIdentity(client.host,"test","v1",3)
    with patch.object(client,"embedding_identity") as metadata:
        with pytest.raises(EmbeddingError):
            client.embed(texts,identity)
        metadata.assert_not_called()


def test_embedding_failure_does_not_retry_another_host_or_model():
    client = OllamaClient(model="test")
    identity = EmbeddingIdentity(client.host,"test","v1",3)
    with patch.object(client,"embedding_identity",return_value=identity), patch.object(client,"_post",side_effect=OllamaError("timeout")) as post:
        with pytest.raises(EmbeddingError,match="no model or destination was changed"):
            client.embed(("text",),identity)
        assert post.call_count == 1


def test_model_specific_prefixes_and_safe_normalization():
    assert embedding_input("embeddinggemma:latest","text",query=True).startswith("task: search result")
    assert embedding_input("embeddinggemma","text",query=False) == "title: none | text: text"
    assert embedding_input("qwen3-embedding:0.6b","text",query=True).startswith("Instruct:")
    assert embedding_input("qwen3-embedding:0.6b","text",query=False) == "text"
    assert embedding_input("other","text",query=True) == "text"
    assert normalized_vector((1e300,1e300),2) == pytest.approx((0.70710678,0.70710678))
