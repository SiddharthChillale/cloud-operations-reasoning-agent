import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path.home() / ".config" / "cora"
CONFIG_FILE = "config.yaml"
REPO_CONFIG_FILE = Path(__file__).parent.parent / ".config" / "cora.yaml"


def _load_yaml_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def _get_env_or_config(
    config: dict, *keys: str, env_var: Optional[str] = None
) -> Optional[str]:
    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            value = None
            break
    if value:
        return str(value)
    if env_var:
        return os.getenv(env_var)
    return None


def load_config() -> dict:
    config = _load_yaml_config(CONFIG_DIR / CONFIG_FILE)
    if not config:
        config = _load_yaml_config(REPO_CONFIG_FILE)
    return config


class Config:
    _instance: Optional["Config"] = None
    _config: dict = {}

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_config()
        return cls._instance

    @property
    def aws_profile(self) -> Optional[str]:
        return _get_env_or_config(self._config, "aws_profile", env_var="AWS_PROFILE")

    @property
    def llm_provider(self) -> str:
        return (
            _get_env_or_config(self._config, "llm", "provider", env_var="LLM_PROVIDER")
            or "openrouter"
        )

    @property
    def llm_model_id(self) -> str:
        return (
            _get_env_or_config(self._config, "llm", "model_id", env_var="LLM_MODEL_ID")
            or "qwen/qwen3-coder"
        )

    @property
    def llm_api_base(self) -> Optional[str]:
        return _get_env_or_config(
            self._config, "llm", "api_base", env_var="LLM_API_BASE"
        )

    @property
    def llm_api_key(self) -> Optional[str]:
        provider = self.llm_provider
        if provider == "openrouter":
            return _get_env_or_config(
                self._config, "llm", "api_key", env_var="OPENROUTER_KEY"
            )
        elif provider == "huggingface":
            return _get_env_or_config(
                self._config, "llm", "api_key", env_var="HF_TOKEN"
            )
        elif provider == "anthropic":
            return _get_env_or_config(
                self._config, "llm", "api_key", env_var="ANTHROPIC_KEY"
            )
        return _get_env_or_config(self._config, "llm", "api_key", env_var="LLM_API_KEY")

    def has_aws_profile(self) -> bool:
        return self.aws_profile is not None

    @property
    def langfuse_secret_key(self) -> Optional[str]:
        return _get_env_or_config(
            self._config, "langfuse", "secret_key", env_var="LANGFUSE_SECRET_KEY"
        )

    @property
    def langfuse_public_key(self) -> Optional[str]:
        return _get_env_or_config(
            self._config, "langfuse", "public_key", env_var="LANGFUSE_PUBLIC_KEY"
        )

    @property
    def langfuse_base_url(self) -> Optional[str]:
        return _get_env_or_config(
            self._config, "langfuse", "base_url", env_var="LANGFUSE_BASE_URL"
        )

    def has_langfuse(self) -> bool:
        return (
            self.langfuse_secret_key is not None
            and self.langfuse_public_key is not None
        )


def get_config() -> Config:
    return Config()
