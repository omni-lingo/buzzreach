"""Tests for src.backend.services.ai.client — AiClient wrapper around Anthropic SDK."""

from unittest.mock import MagicMock, patch

import pytest

from src.backend.services.ai.client import (
    HAIKU,
    SONNET,
    AiClient,
    AiProviderError,
)


class TestModelConstants:
    """Model ID constants are correct and accessible."""

    def test_haiku_model_id(self) -> None:
        assert HAIKU == "claude-haiku-4-5-20251001"

    def test_sonnet_model_id(self) -> None:
        assert SONNET == "claude-sonnet-4-6"


class TestAiClientInit:
    """AiClient initialises from settings, never hardcoding a key."""

    def test_creates_anthropic_client_with_api_key(self) -> None:
        with patch("src.backend.services.ai.client.Anthropic") as mock_cls:
            client = AiClient(api_key="sk-ant-test-key-123")
            mock_cls.assert_called_once_with(api_key="sk-ant-test-key-123")
            assert client._client is mock_cls.return_value


class TestAiClientComplete:
    """AiClient.complete builds the SDK request and parses the text response."""

    def _make_client(self) -> tuple[AiClient, MagicMock]:
        with patch("src.backend.services.ai.client.Anthropic") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            client = AiClient(api_key="sk-ant-test-key")
        return client, mock_sdk

    def test_complete_returns_text(self) -> None:
        client, mock_sdk = self._make_client()

        mock_block = MagicMock()
        mock_block.text = "Generated response"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_sdk.messages.create.return_value = mock_response

        result = client.complete(
            model=HAIKU,
            system="You are a scorer.",
            user="Score this thread.",
            max_tokens=256,
        )

        assert result == "Generated response"

    def test_complete_passes_correct_params(self) -> None:
        client, mock_sdk = self._make_client()

        mock_block = MagicMock()
        mock_block.text = "ok"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_sdk.messages.create.return_value = mock_response

        client.complete(
            model=SONNET,
            system="Draft a reply.",
            user="Here is the thread.",
            max_tokens=1024,
        )

        call_kwargs = mock_sdk.messages.create.call_args.kwargs
        assert call_kwargs["model"] == SONNET
        assert call_kwargs["max_tokens"] == 1024
        assert call_kwargs["messages"] == [
            {"role": "user", "content": "Here is the thread."},
        ]

    def test_complete_enables_prompt_caching(self) -> None:
        client, mock_sdk = self._make_client()

        mock_block = MagicMock()
        mock_block.text = "cached"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_sdk.messages.create.return_value = mock_response

        client.complete(
            model=HAIKU,
            system="Reused system prompt.",
            user="Input text.",
            max_tokens=100,
        )

        call_kwargs = mock_sdk.messages.create.call_args.kwargs
        system_arg = call_kwargs["system"]
        assert isinstance(system_arg, list)
        assert len(system_arg) == 1
        assert system_arg[0]["type"] == "text"
        assert system_arg[0]["text"] == "Reused system prompt."
        assert system_arg[0]["cache_control"] == {"type": "ephemeral"}


class TestAiClientErrors:
    """Hard SDK failures raise AiProviderError with the correct code."""

    def _make_client(self) -> tuple[AiClient, MagicMock]:
        with patch("src.backend.services.ai.client.Anthropic") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            client = AiClient(api_key="sk-ant-test-key")
        return client, mock_sdk

    def test_api_error_raises_ai_provider_error(self) -> None:
        client, mock_sdk = self._make_client()
        mock_sdk.messages.create.side_effect = Exception("connection refused")

        with pytest.raises(AiProviderError) as exc_info:
            client.complete(
                model=HAIKU,
                system="sys",
                user="usr",
                max_tokens=100,
            )

        assert exc_info.value.code == "AI_PROVIDER_ERROR"
        assert "connection refused" in exc_info.value.message

    def test_empty_response_raises_ai_provider_error(self) -> None:
        client, mock_sdk = self._make_client()
        mock_response = MagicMock()
        mock_response.content = []
        mock_sdk.messages.create.return_value = mock_response

        with pytest.raises(AiProviderError) as exc_info:
            client.complete(
                model=HAIKU,
                system="sys",
                user="usr",
                max_tokens=100,
            )

        assert exc_info.value.code == "AI_PROVIDER_ERROR"


class TestAiClientRetry:
    """Rate-limit errors are retried before raising."""

    def test_retries_on_rate_limit_then_succeeds(self) -> None:
        with patch("src.backend.services.ai.client.Anthropic") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            client = AiClient(api_key="sk-ant-test-key")

        rate_limit_err = _make_rate_limit_error()

        mock_block = MagicMock()
        mock_block.text = "success after retry"
        mock_ok = MagicMock()
        mock_ok.content = [mock_block]

        mock_sdk.messages.create.side_effect = [rate_limit_err, mock_ok]

        with patch("src.backend.services.ai.client.time.sleep"):
            result = client.complete(
                model=HAIKU,
                system="sys",
                user="usr",
                max_tokens=100,
            )

        assert result == "success after retry"
        assert mock_sdk.messages.create.call_count == 2

    def test_raises_after_max_retries(self) -> None:
        with patch("src.backend.services.ai.client.Anthropic") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            client = AiClient(api_key="sk-ant-test-key")

        rate_limit_err = _make_rate_limit_error()
        mock_sdk.messages.create.side_effect = [
            rate_limit_err,
            rate_limit_err,
            rate_limit_err,
            rate_limit_err,
        ]

        with (
            patch("src.backend.services.ai.client.time.sleep"),
            pytest.raises(AiProviderError) as exc_info,
        ):
            client.complete(
                model=HAIKU,
                system="sys",
                user="usr",
                max_tokens=100,
            )

        assert exc_info.value.code == "AI_PROVIDER_ERROR"


def _make_rate_limit_error() -> Exception:
    """Create a mock anthropic.RateLimitError."""
    from unittest.mock import MagicMock

    import anthropic

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {}
    return anthropic.RateLimitError(
        message="rate limited",
        response=mock_response,
        body={"error": {"message": "rate limited", "type": "rate_limit_error"}},
    )
