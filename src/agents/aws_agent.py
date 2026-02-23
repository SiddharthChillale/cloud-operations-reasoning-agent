from pathlib import Path
import os
import re
from src.config import get_config
from src.models import create_model
from src.tools import create_boto_client_tool

from smolagents import CodeAgent, PromptTemplates
from yaml import safe_load


vars = {
    "aws_region": os.getenv("AWS_REGION", "us-east-2"),
    "aws_profile": os.getenv("AWS_PROFILE", "default"),
}

# prompt_file_path = Path(__file__).parent / "prompts.yaml"
prompt_file_path = Path(__file__).parent / "aws_core_agent" / "prompts" / "v2.yaml"

with open(prompt_file_path) as f:
    AWS_AGENT_SYSTEM_PROMPT = safe_load(f)


# def render_prompts(data):
#     if isinstance(data, dict):
#         for k, v in data.items():
#             data[k] = render_prompts(v)
#     elif isinstance(data, str):
#         pattern = r"\{\{\s*aws_region\s*(?:\|.*?)?\}\}"
#         data = re.sub(pattern, vars["aws_region"], data)

#         pattern = r"\{\{\s*aws_profile\s*(?:\|.*?)?\}\}"
#         data = re.sub(pattern, vars["aws_profile"], data)
#     return data


# rendered_prompt = render_prompts(AWS_AGENT_SYSTEM_PROMPT)
# # prompt_templates = PromptTemplates(**rendered_yaml)


def cora_agent() -> CodeAgent:
    config = get_config()
    model = create_model()

    tools = [create_boto_client_tool()]
    additional_authorized_imports = ["botocore.exceptions", "json"]
    if not config.has_aws_profile():
        additional_authorized_imports.extend(["boto3", "botocore"])
        tools.pop(0)

    agent = CodeAgent(
        tools=tools,
        model=model,
        prompt_templates=AWS_AGENT_SYSTEM_PROMPT,
        instructions="""All resources are in us-east-2 region unless specified otherwise""",
        use_structured_outputs_internally=True,
        stream_outputs=True,
        planning_interval=2,
        max_steps=10,
        additional_authorized_imports=additional_authorized_imports,
    )
    return agent
