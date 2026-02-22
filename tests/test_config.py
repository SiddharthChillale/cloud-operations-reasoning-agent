import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_config():
    import src.config

    src.config.Config._instance = None
    src.config.Config._config = {}
    yield


class TestConfigAwsProfile:
    @patch("src.config._load_yaml_config")
    def test_config_aws_profile_from_env(self, mock_load):
        mock_load.return_value = {}

        with patch.dict(os.environ, {"AWS_PROFILE": "my-profile"}):
            from src.config import Config

            config = Config()
            assert config.aws_profile == "my-profile"

    @patch("src.config._load_yaml_config")
    def test_config_aws_profile_from_yaml(self, mock_load):
        mock_load.return_value = {"aws_profile": "yaml-profile"}

        from src.config import Config

        config = Config()
        assert config.aws_profile == "yaml-profile"

    @patch("src.config._load_yaml_config")
    def test_config_yaml_takes_precedence_over_env(self, mock_load):
        mock_load.return_value = {"aws_profile": "yaml-profile"}

        with patch.dict(os.environ, {"AWS_PROFILE": "env-profile"}):
            from src.config import Config

            config = Config()
            assert config.aws_profile == "yaml-profile"

    @patch("src.config._load_yaml_config")
    def test_config_has_aws_profile_true(self, mock_load):
        mock_load.return_value = {"aws_profile": "test-profile"}

        from src.config import Config

        config = Config()
        assert config.has_aws_profile() is True


class TestConfigLlm:
    @patch("src.config._load_yaml_config")
    def test_config_llm_provider_default(self, mock_load):
        mock_load.return_value = {}

        from src.config import Config

        config = Config()
        assert config.llm_provider == "openrouter"

    @patch("src.config._load_yaml_config")
    def test_config_llm_provider_from_env(self, mock_load):
        mock_load.return_value = {}

        with patch.dict(os.environ, {"LLM_PROVIDER": "huggingface"}):
            from src.config import Config

            config = Config()
            assert config.llm_provider == "huggingface"

    @patch("src.config._load_yaml_config")
    def test_config_llm_provider_from_yaml(self, mock_load):
        mock_load.return_value = {"llm": {"provider": "anthropic"}}

        from src.config import Config

        config = Config()
        assert config.llm_provider == "anthropic"

    @patch("src.config._load_yaml_config")
    def test_config_llm_api_key_openrouter(self, mock_load):
        mock_load.return_value = {}

        with patch.dict(os.environ, {"OPENROUTER_KEY": "or-key"}):
            from src.config import Config

            config = Config()
            assert config.llm_api_key == "or-key"

    @patch("src.config._load_yaml_config")
    def test_config_llm_api_key_huggingface(self, mock_load):
        mock_load.return_value = {"llm": {"provider": "huggingface"}}

        with patch.dict(os.environ, {"HF_TOKEN": "hf-key"}):
            from src.config import Config

            config = Config()
            assert config.llm_api_key == "hf-key"

    @patch("src.config._load_yaml_config")
    def test_config_llm_api_key_anthropic(self, mock_load):
        mock_load.return_value = {"llm": {"provider": "anthropic"}}

        with patch.dict(os.environ, {"ANTHROPIC_KEY": "anthropic-key"}):
            from src.config import Config

            config = Config()
            assert config.llm_api_key == "anthropic-key"

    @patch("src.config._load_yaml_config")
    def test_config_llm_model_id_default(self, mock_load):
        mock_load.return_value = {}

        from src.config import Config

        config = Config()
        assert config.llm_model_id == "qwen/qwen3-coder"

    @patch("src.config._load_yaml_config")
    def test_config_llm_model_id_from_yaml(self, mock_load):
        mock_load.return_value = {"llm": {"model_id": "custom/model"}}

        from src.config import Config

        config = Config()
        assert config.llm_model_id == "custom/model"

    @patch("src.config._load_yaml_config")
    def test_config_llm_api_base_from_yaml(self, mock_load):
        mock_load.return_value = {"llm": {"api_base": "https://custom.api.com/"}}

        from src.config import Config

        config = Config()
        assert config.llm_api_base == "https://custom.api.com/"


class TestConfigLangfuse:
    @patch("src.config._load_yaml_config")
    def test_config_langfuse_config(self, mock_load):
        mock_load.return_value = {
            "langfuse": {
                "secret_key": "secret",
                "public_key": "public",
                "base_url": "https://cloud.langfuse.com",
            }
        }

        from src.config import Config

        config = Config()
        assert config.langfuse_secret_key == "secret"
        assert config.langfuse_public_key == "public"
        assert config.langfuse_base_url == "https://cloud.langfuse.com"

    @patch("src.config._load_yaml_config")
    def test_config_has_langfuse_true(self, mock_load):
        mock_load.return_value = {
            "langfuse": {
                "secret_key": "secret",
                "public_key": "public",
            }
        }

        from src.config import Config

        config = Config()
        assert config.has_langfuse() is True


class TestGetConfig:
    @patch("src.config._load_yaml_config")
    def test_get_config_returns_singleton(self, mock_load):
        mock_load.return_value = {}

        from src.config import get_config

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2
