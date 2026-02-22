from smolagents import CodeAgent

from src.models import openrouter_model
from src.tools import create_boto_client


def cora_agent() -> CodeAgent:
    return CodeAgent(
        tools=[create_boto_client],
        model=openrouter_model,
        additional_authorized_imports=["botocore.exceptions"],
    )
