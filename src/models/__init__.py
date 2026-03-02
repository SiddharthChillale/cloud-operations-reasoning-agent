from typing import Optional
from smolagents import OpenAIModel
from src.config import get_config


def create_model() -> OpenAIModel:
    config = get_config()

    # Smolagents OpenAIModel can be used for most providers as long as they
    # provide an OpenAI-compatible interface (like OpenRouter, Anthropic proxy, etc.)
    return OpenAIModel(
        model_id=config.llm_model_id,
        api_base=config.llm_api_base,
        api_key=config.llm_api_key,
    )


# Instantiate the model
# NOTE: This will fail at import time if required environment variables are missing
# because get_config() is called during create_model()
try:
    openrouter_model = create_model()
except RuntimeError as e:
    # Log the error but don't prevent the module from being imported
    # though any subsequent use of openrouter_model will fail
    import logging

    logging.getLogger(__name__).warning(f"Failed to initialize LLM: {e}")
    openrouter_model = None

__all__ = ["openrouter_model", "create_model"]
