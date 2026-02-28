from pathlib import Path
import os
from src.config import get_config
from src.models import create_model
from src.tools import create_boto_client_tool
import modal

from smolagents import CodeAgent
from smolagents.remote_executors import ModalExecutor
from smolagents.monitoring import AgentLogger, LogLevel
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


def cora_agent(use_sandbox_execution=True, aws_regions: list[str] = ['us-east-2'] ) -> CodeAgent:
    config = get_config()
    model = create_model()

    tools = []
    additional_authorized_imports = ["boto3"]
    instructions = (
        f"""AWS Regions that are relevant: {", ".join(aws_regions)}."""
    )
    if config.has_aws_profile() and not use_sandbox_execution:
        instructions += """Use the create_boto_client tool for creating a boto client, as boto3 library is not available to you."""
        tools.append(create_boto_client_tool())
        additional_authorized_imports.remove("boto3")

    agent_kwargs = {
        "tools": tools,
        "model": model,
        "prompt_templates": AWS_AGENT_SYSTEM_PROMPT,
        "instructions": instructions,
        "use_structured_outputs_internally": True,
        "stream_outputs": True,
        "planning_interval": 3,
        "max_steps": 15,
        "additional_authorized_imports": additional_authorized_imports,
    }

    if use_sandbox_execution:
        logger = AgentLogger(level=LogLevel.INFO)
        executor = ModalExecutor(
            additional_imports=[],
            logger=logger,
            app_name="cora-smolagent-execution",
            create_kwargs={
                "secrets": [modal.Secret.from_name("notisphere-read")],
                "image": modal.Image.debian_slim().uv_pip_install(
                    "boto3", "jupyter", "jupyter_kernel_gateway"
                ),
            },
        )
        agent_kwargs['executor'] = executor
        agent_kwargs['tools']= []

    agent = CodeAgent(**agent_kwargs)
    return agent
