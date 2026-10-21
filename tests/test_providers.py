"""Comprehensive unit tests for provider abstraction, Ollama client, and mock provider."""

import json

import httpx
import pytest
from httpx import Response
from starlette.testclient import TestClient

from src.evalforge.core.errors import ModelNotFoundError, ProviderConnectionError, ProviderError
from src.evalforge.main import app
from src.evalforge.providers.mock import MockProvider
from src.evalforge.providers.ollama.capabilities import detect_capabilities, parse_model_info
from src.evalforge.providers.ollama.client import OllamaClient
from src.evalforge.providers.registry import ProviderRegistry
from src.evalforge.providers.schemas import (
    InferenceRequest,
    ToolDefinition,
)


@pytest.mark.asyncio
async def test_mock_provider_basic_inference() -> None:
    provider = MockProvider(latency_seconds=0.001)
    req = InferenceRequest(
        model="mock-llama-3.1-8b",
        prompt="Explain quantum entanglement briefly.",
        temperature=0.5,
    )
    resp = await provider.generate(req)
    assert resp.model == "mock-llama-3.1-8b"
    assert resp.provider == "mock"
    assert resp.latency_ms > 0
    assert resp.usage is not None
    assert resp.usage.total_tokens > 0
    assert "Mock response" in resp.text


@pytest.mark.asyncio
async def test_mock_provider_structured_json() -> None:
    provider = MockProvider(latency_seconds=0.0)
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "active": {"type": "boolean"},
        },
        "required": ["name", "age"],
    }
    req = InferenceRequest(
        model="mock-qwen-2.5-7b",
        prompt="Extract person details.",
        json_schema=schema,
    )
    resp = await provider.generate(req)
    data = json.loads(resp.text)
    assert "name" in data
    assert data["age"] == 42
    assert data["active"] is True


@pytest.mark.asyncio
async def test_mock_provider_tool_calling() -> None:
    provider = MockProvider(latency_seconds=0.0)
    tools = [
        ToolDefinition(
            name="calculator",
            description="Performs arithmetic",
            parameters={"type": "object", "properties": {"expression": {"type": "string"}}},
        )
    ]
    req = InferenceRequest(
        model="mock-llama-3.1-8b",
        prompt="Please call tool calculator to add 5 and 7.",
        tools=tools,
    )
    resp = await provider.generate(req)
    assert resp.tool_calls is not None
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "calculator"
    assert "expression" in resp.tool_calls[0].arguments


@pytest.mark.asyncio
async def test_mock_provider_model_validation() -> None:
    provider = MockProvider(latency_seconds=0.0)
    req = InferenceRequest(model="nonexistent-model", prompt="Hello")
    with pytest.raises(ModelNotFoundError):
        await provider.generate(req)


@pytest.mark.asyncio
async def test_ollama_client_mock_transport_tags() -> None:
    mock_tags_payload = {
        "models": [
            {
                "name": "llama3.2:3b",
                "size": 2019393152,
                "details": {
                    "family": "llama",
                    "parameter_size": "3B",
                    "quantization_level": "Q4_K_M",
                },
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return Response(200, json=mock_tags_payload)
        return Response(404)

    client = OllamaClient(base_url="http://mock-ollama:11434")
    client._http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://mock-ollama:11434"
    )

    tags = await client.list_tags()
    assert len(tags["models"]) == 1
    model_info = parse_model_info(tags["models"][0])
    assert model_info.id == "llama3.2:3b"
    assert model_info.parameter_size == "3B"

    capabilities = detect_capabilities(
        {"details": {"family": "llama"}, "template": "{{- if .Tools }}...{{ end }}"},
        "llama3.2:3b",
    )
    assert capabilities.supports_tools is True
    assert capabilities.supports_structured_output is True


@pytest.mark.asyncio
async def test_ollama_client_unreachable_connection_error() -> None:
    # Use non-existent port to verify connection error handling
    client = OllamaClient(base_url="http://127.0.0.1:54321", timeout_seconds=1.0)
    is_healthy = await client.check_health()
    assert is_healthy is False

    with pytest.raises(ProviderConnectionError) as exc_info:
        await client.get_version()
    assert "Could not connect to Ollama daemon" in str(exc_info.value)


@pytest.mark.asyncio
async def test_provider_registry() -> None:
    registry = ProviderRegistry()
    assert "ollama" in registry.list_names()
    assert "mock" in registry.list_names()

    mock_p = registry.get("mock")
    assert isinstance(mock_p, MockProvider)

    with pytest.raises(ProviderError):
        registry.get("invalid_provider_name")


def test_api_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "EvalForge20"
        assert "ollama_base_url" in data


def test_api_providers_endpoints() -> None:
    with TestClient(app) as client:
        # List providers
        res = client.get("/api/v1/providers")
        assert res.status_code == 200
        data = res.json()
        names = [p["name"] for p in data["providers"]]
        assert "ollama" in names
        assert "mock" in names

        # Ollama health
        res = client.get("/api/v1/providers/ollama/health")
        assert res.status_code == 200
        health_data = res.json()
        assert "base_url" in health_data
        assert "reachable" in health_data
