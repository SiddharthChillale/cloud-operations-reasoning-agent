from pathlib import Path

from src.config import get_config
from src.models import create_model
from src.tools import create_boto_client_tool


from smolagents import CodeAgent, PromptTemplates
from yaml import safe_load

prompt_file_path = Path(__file__).parent / "prompts.yaml"

with open(prompt_file_path) as f:
    AWS_AGENT_SYSTEM_PROMPT = safe_load(f)


def cora_agent() -> CodeAgent:
    config = get_config()
    model = create_model()

    tools = []
    if config.has_aws_profile():
        tools.append(create_boto_client_tool())

    agent = CodeAgent(
        tools=tools,
        model=model,
        planning_interval=5,
        prompt_templates=AWS_AGENT_SYSTEM_PROMPT,
        use_structured_outputs_internally=True,
        stream_outputs=True,
        additional_authorized_imports=["botocore.exceptions"],
    )
    return agent
