from typing import Optional
from smolagents import OpenAIModel
from src.config import get_config

AI_GATEWAY_BASE_URL = "https://ai-gateway.vercel.sh/v1"

MODELS = {
    "gpt-4o": {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "openai/gpt-4o",
    },
    "gpt-4o-mini": {
        "id": "gpt-4o-mini",
        "name": "GPT-4o mini",
        "provider": "openai/gpt-4o-mini",
    },
    "claude-haiku-4.5": {
        "id": "claude-haiku-4.5",
        "name": "Claude 4.5 Haiku",
        "provider": "anthropic/claude-haiku-4.5",
    },
}

DEFAULT_MODEL_ID = "gpt-4o"


def create_model(model_id: str = DEFAULT_MODEL_ID) -> OpenAIModel:
    config = get_config()
    model_config = MODELS.get(model_id)

    if not model_config:
        raise ValueError(
            f"Invalid model_id: {model_id}. Available: {list(MODELS.keys())}"
        )

    return OpenAIModel(
        model_id=model_config["provider"],
        api_base=AI_GATEWAY_BASE_URL,
        api_key=config.ai_gateway_api_key,
    )


def get_available_models() -> list[dict]:
    return [{"id": m["id"], "name": m["name"]} for m in MODELS.values()]


__all__ = ["create_model", "get_available_models", "MODELS", "DEFAULT_MODEL_ID"]
