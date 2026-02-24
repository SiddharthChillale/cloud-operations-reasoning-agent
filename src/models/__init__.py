from typing import Optional

from smolagents import OpenAIModel

from src.config import get_config


def _get_openrouter_model(
    api_key: str, model_id: Optional[str], api_base: Optional[str]
) -> OpenAIModel:
    return OpenAIModel(
        model_id=model_id or "qwen/qwen3-coder",
        api_base=api_base or "https://openrouter.ai/api/v1/",
        api_key=api_key,
    )


def _get_huggingface_model(
    api_key: str, model_id: Optional[str], api_base: Optional[str]
) -> OpenAIModel:
    return OpenAIModel(
        model_id=model_id or "Qwen/Qwen2.5-Coder-32B-Instruct",
        api_base=api_base or "https://api-inference.huggingface.co/",
        api_key=api_key,
    )


def _get_anthropic_model(
    api_key: str, model_id: Optional[str], api_base: Optional[str]
) -> OpenAIModel:
    return OpenAIModel(
        model_id=model_id or "anthropic/claude-3.5-sonnet",
        api_base=api_base or "https://api.anthropic.com/v1/",
        api_key=api_key,
    )


def create_model() -> OpenAIModel:
    config = get_config()
    provider = config.llm_provider
    api_key = config.llm_api_key
    model_id = config.llm_model_id
    api_base = config.llm_api_base
    if not api_key:
        raise ValueError(f"No API key configured for provider: {provider}")

    if provider == "openrouter":
        return _get_openrouter_model(api_key, model_id, api_base)
    elif provider == "huggingface":
        return _get_huggingface_model(api_key, model_id, api_base)
    elif provider == "anthropic":
        return _get_anthropic_model(api_key, model_id, api_base)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


openrouter_model = create_model()

__all__ = ["openrouter_model", "create_model"]
