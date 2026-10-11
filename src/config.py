import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    _instance: Optional["Config"] = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def database_url(self) -> str:
        return _get_required_env("DATABASE_URL")

    @property
    def ai_gateway_api_key(self) -> str:
        return _get_required_env("AI_GATEWAY_API_KEY")

    @property
    def ai_gateway_base_url(self) -> str:
        return os.getenv("AI_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh/v1")

    @property
    def modal_token_id(self) -> str:
        return _get_required_env("MODAL_TOKEN_ID")

    @property
    def modal_token_secret(self) -> str:
        return _get_required_env("MODAL_TOKEN_SECRET")

    @property
    def modal_user_secret(self) -> str:
        return _get_required_env("MODAL_USER_SECRET")

    @property
    def modal_aws_secret_name(self) -> str:
        return _get_required_env("MODAL_AWS_SECRET_NAME")

    @property
    def aws_profile(self) -> Optional[str]:
        return os.getenv("AWS_PROFILE")

    @property
    def langfuse_secret_key(self) -> Optional[str]:
        return os.getenv("LANGFUSE_SECRET_KEY")

    @property
    def langfuse_public_key(self) -> Optional[str]:
        return os.getenv("LANGFUSE_PUBLIC_KEY")

    @property
    def langfuse_base_url(self) -> Optional[str]:
        return os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    def has_langfuse(self) -> bool:
        return bool(self.langfuse_secret_key and self.langfuse_public_key)

    def has_aws_profile(self) -> bool:
        return self.aws_profile is not None


def get_config() -> Config:
    return Config()
