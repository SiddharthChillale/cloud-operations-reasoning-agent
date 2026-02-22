import pytest
from unittest.mock import MagicMock, patch


class TestModelImports:
    def test_openrouter_model_import(self):
        from src.models import openrouter_model
        from smolagents import OpenAIModel

        assert openrouter_model is not None
        assert isinstance(openrouter_model, OpenAIModel)

    def test_create_model_import(self):
        from src.models import create_model

        assert callable(create_model)

    def test_models_module_exports(self):
        from src.models import __all__

        assert "openrouter_model" in __all__
        assert "create_model" in __all__


class TestCreateModel:
    @patch("src.models.get_config")
    def test_create_model_with_openrouter(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.llm_provider = "openrouter"
        mock_config.llm_api_key = "test-key"
        mock_config.llm_model_id = "qwen/qwen3-coder"
        mock_config.llm_api_base = "https://openrouter.ai/api/v1/"
        mock_get_config.return_value = mock_config

        from src.models import create_model

        with patch("src.models._get_openrouter_model") as mock_get_model:
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            result = create_model()

            mock_get_model.assert_called_once_with(
                "test-key", "qwen/qwen3-coder", "https://openrouter.ai/api/v1/"
            )
            assert result == mock_model

    @patch("src.models.get_config")
    def test_create_model_with_huggingface(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.llm_provider = "huggingface"
        mock_config.llm_api_key = "hf-test-key"
        mock_config.llm_model_id = "Qwen/Qwen2.5-Coder-32B-Instruct"
        mock_config.llm_api_base = "https://api-inference.huggingface.co/"
        mock_get_config.return_value = mock_config

        from src.models import create_model

        with patch("src.models._get_huggingface_model") as mock_get_model:
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            result = create_model()

            mock_get_model.assert_called_once_with(
                "hf-test-key",
                "Qwen/Qwen2.5-Coder-32B-Instruct",
                "https://api-inference.huggingface.co/",
            )
            assert result == mock_model

    @patch("src.models.get_config")
    def test_create_model_with_anthropic(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.llm_provider = "anthropic"
        mock_config.llm_api_key = "anthropic-test-key"
        mock_config.llm_model_id = "anthropic/claude-3.5-sonnet"
        mock_config.llm_api_base = "https://api.anthropic.com/v1/"
        mock_get_config.return_value = mock_config

        from src.models import create_model

        with patch("src.models._get_anthropic_model") as mock_get_model:
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            result = create_model()

            mock_get_model.assert_called_once_with(
                "anthropic-test-key",
                "anthropic/claude-3.5-sonnet",
                "https://api.anthropic.com/v1/",
            )
            assert result == mock_model

    @patch("src.models.get_config")
    def test_create_model_raises_without_api_key(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.llm_provider = "openrouter"
        mock_config.llm_api_key = None
        mock_get_config.return_value = mock_config

        from src.models import create_model

        with pytest.raises(ValueError, match="No API key configured for provider"):
            create_model()

    @patch("src.models.get_config")
    def test_create_model_raises_for_unknown_provider(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.llm_provider = "unknown_provider"
        mock_config.llm_api_key = "some-key"
        mock_get_config.return_value = mock_config

        from src.models import create_model

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_model()


class TestOpenRouterModel:
    def test_openrouter_model_is_defined(self):
        from src.models import openrouter_model
        from smolagents import OpenAIModel

        assert openrouter_model is not None
        assert isinstance(openrouter_model, OpenAIModel)
