from smolagents import CodeAgent

from src.config import get_config
from src.models import create_model
from src.tools import create_boto_client_tool


def cora_agent() -> CodeAgent:
    config = get_config()
    model = create_model()

    tools = []
    if config.has_aws_profile():
        tools.append(create_boto_client_tool())

    return CodeAgent(
        tools=tools,
        model=model,
        additional_authorized_imports=["botocore.exceptions"],
    )
