from pathlib import Path
import os
from src.config import get_config
from src.models import create_model
from src.tools import create_boto_client_tool
import modal

from smolagents import CodeAgent
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
    instructions = """All resources are in us-east-2 region unless specified otherwise"""
    isTrue = config.has_aws_profile()
    isTrue = False
    if not config.has_aws_profile():
        additional_authorized_imports.extend(["boto3", "botocore"])
        instructions += """Use the create_boto_client tool for creating a boto client, as boto3 library is not available to you."""
        tools.pop(0)
    
    agent_kwargs = {
        "tools": tools,
        "model": model,
        "prompt_templates": AWS_AGENT_SYSTEM_PROMPT,
        "instructions": instructions,
        "use_structured_outputs_internally": True,
        "stream_outputs": True,
        "planning_interval": 2,
        "max_steps": 15,
        "additional_authorized_imports": additional_authorized_imports,
    }

    # if True:
    #     agent_kwargs["executor_type"] = "modal"
    #     agent_kwargs["executor_kwargs"] = {
    #         "app_name": "cora-smolagent-execution",
    #         "create_kwargs": {
    #             "secrets": [modal.Secret.from_name('notisphere-read')],
    #             "image": modal.Image.debian_slim().uv_pip_install(
    #                 "boto3",
    #                 "jupyter",
    #                 "jupyter_kernel_gateway"
    #             )
    #         }
    #     }

    agent = CodeAgent(**agent_kwargs)
    return agent
