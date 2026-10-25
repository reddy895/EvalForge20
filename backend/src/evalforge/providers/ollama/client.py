"""Asynchronous HTTP client for Ollama local REST API."""

from typing import Any, Optional

import httpx

from src.evalforge.core.config import get_settings
from src.evalforge.core.errors import (
    ModelNotFoundError,
    ProviderConnectionError,
    ProviderError,
)
from src.evalforge.core.logging import get_logger

logger = get_logger("evalforge.providers.ollama.client")

_ollama_client_instance: Optional["OllamaClient"] = None


class OllamaClient:
    """Async HTTP client managing connections to the local Ollama daemon."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS
        self._http_client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                headers={"User-Agent": "EvalForge20-Client/2.0"},
            )
        return self._http_client

    async def check_health(self) -> bool:
        """Ping Ollama API to verify daemon connectivity."""
        try:
            client = self._get_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except (httpx.ConnectError, httpx.ConnectTimeout):
            return False
        except Exception as exc:
            logger.warning("Ollama health check encounter unexpected error: %s", exc)
            return False

    async def diagnose(self, requested_model: str | None = None) -> Any:
        """Run comprehensive connectivity diagnostics against configured endpoint."""
        from src.evalforge.providers.ollama.diagnostics import run_ollama_diagnostics

        return await run_ollama_diagnostics(
            base_url=self.base_url,
            requested_model=requested_model,
            timeout=min(self.timeout, 5.0),
        )

    async def get_version(self) -> str:
        """Fetch version string from Ollama daemon."""
        client = self._get_client()
        try:
            response = await client.get("/api/version")
            response.raise_for_status()
            data = response.json()
            return data.get("version", "unknown")
        except httpx.ConnectError:
            raise ProviderConnectionError(
                "Could not connect to Ollama daemon.",
                provider="ollama",
                base_url=self.base_url,
            )
        except Exception as exc:
            raise ProviderError(f"Failed to get Ollama version: {exc}", provider="ollama")

    async def list_tags(self) -> dict[str, Any]:
        """Fetch list of locally installed models."""
        client = self._get_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise ProviderConnectionError(
                "Could not connect to Ollama daemon.",
                provider="ollama",
                base_url=self.base_url,
            )
        except httpx.TimeoutException:
            raise ProviderError(
                f"Ollama request to list models timed out after {self.timeout}s.",
                provider="ollama",
            )
        except Exception as exc:
            raise ProviderError(f"Failed to query Ollama models: {exc}", provider="ollama")

    async def show_model(self, model_name: str) -> dict[str, Any]:
        """Fetch detailed parameters, license, and template for a specific model."""
        client = self._get_client()
        try:
            response = await client.post("/api/show", json={"name": model_name})
            if response.status_code == 404:
                raise ModelNotFoundError(model_name, provider="ollama")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise ProviderConnectionError(
                "Could not connect to Ollama daemon.",
                provider="ollama",
                base_url=self.base_url,
            )
        except ModelNotFoundError:
            raise
        except Exception as exc:
            raise ProviderError(
                f"Failed to show metadata for model '{model_name}': {exc}",
                provider="ollama",
            )

    async def generate(self, payload: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        """Execute a text completion generation request."""
        client = self._get_client()
        # Force stream=False for non-streaming batch evaluations
        payload["stream"] = False
        effective_timeout = timeout if timeout is not None else self.timeout
        try:
            response = await client.post("/api/generate", json=payload, timeout=effective_timeout)
            if response.status_code == 404:
                raise ModelNotFoundError(payload.get("model", "unknown"), provider="ollama")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            err_text = ""
            try:
                err_json = exc.response.json()
                if isinstance(err_json, dict) and "error" in err_json:
                    err_text = str(err_json["error"])
            except Exception:
                err_text = exc.response.text[:200] if exc.response else ""
            if exc.response.status_code == 404:
                raise ModelNotFoundError(payload.get("model", "unknown"), provider="ollama")
            raise ProviderError(
                f"Ollama returned HTTP {exc.response.status_code}: {err_text or exc}",
                provider="ollama",
                status_code=exc.response.status_code,
            )
        except httpx.ConnectError:
            raise ProviderConnectionError(
                "Could not connect to Ollama daemon.",
                provider="ollama",
                base_url=self.base_url,
            )
        except httpx.TimeoutException:
            raise ProviderError(
                f"Ollama generation timed out after {effective_timeout}s.",
                provider="ollama",
            )
        except ModelNotFoundError:
            raise
        except Exception as exc:
            raise ProviderError(f"Ollama generation failed: {exc}", provider="ollama")

    async def chat(self, payload: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        """Execute a multi-turn chat request with optional tool calling."""
        client = self._get_client()
        payload["stream"] = False
        effective_timeout = timeout if timeout is not None else self.timeout
        try:
            response = await client.post("/api/chat", json=payload, timeout=effective_timeout)
            if response.status_code == 404:
                raise ModelNotFoundError(payload.get("model", "unknown"), provider="ollama")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            err_text = ""
            try:
                err_json = exc.response.json()
                if isinstance(err_json, dict) and "error" in err_json:
                    err_text = str(err_json["error"])
            except Exception:
                err_text = exc.response.text[:200] if exc.response else ""
            if exc.response.status_code == 404:
                raise ModelNotFoundError(payload.get("model", "unknown"), provider="ollama")
            raise ProviderError(
                f"Ollama returned HTTP {exc.response.status_code}: {err_text or exc}",
                provider="ollama",
                status_code=exc.response.status_code,
            )
        except httpx.ConnectError:
            raise ProviderConnectionError(
                "Could not connect to Ollama daemon.",
                provider="ollama",
                base_url=self.base_url,
            )
        except httpx.TimeoutException:
            raise ProviderError(
                f"Ollama chat request timed out after {effective_timeout}s.",
                provider="ollama",
            )
        except ModelNotFoundError:
            raise
        except Exception as exc:
            raise ProviderError(f"Ollama chat failed: {exc}", provider="ollama")

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None


def get_ollama_client(base_url: str | None = None) -> OllamaClient:
    """Return shared or customized OllamaClient instance."""
    global _ollama_client_instance
    if _ollama_client_instance is None or base_url is not None:
        client = OllamaClient(base_url=base_url)
        if base_url is None:
            _ollama_client_instance = client
        return client
    return _ollama_client_instance


async def close_ollama_client() -> None:
    """Close the shared Ollama client instance if active."""
    global _ollama_client_instance
    if _ollama_client_instance:
        await _ollama_client_instance.close()
        _ollama_client_instance = None
