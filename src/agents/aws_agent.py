from pathlib import Path
import os
import modal
from smolagents import CodeAgent
from smolagents.remote_executors import ModalExecutor
from smolagents.monitoring import AgentLogger, LogLevel
from yaml import safe_load

from src.config import get_config
from src.models import create_model
from src.tools import create_boto_client_tool


# Load configuration strictly from environment variables via Config
config = get_config()

# Define relevant variables for prompt rendering
vars = {
    "aws_region": os.getenv("AWS_REGION", "us-east-2"),  # Fallback for local prompt var
    "aws_profile": config.aws_profile or "default",
}

# Define prompt file path
prompt_file_path = Path(__file__).parent / "aws_core_agent" / "prompts" / "v2.yaml"

with open(prompt_file_path) as f:
    AWS_AGENT_SYSTEM_PROMPT = safe_load(f)


def cora_agent(
    use_sandbox_execution=True, aws_regions: list[str] = ["us-east-2"]
) -> CodeAgent:
    model = create_model()

    tools = []
    additional_authorized_imports = ["boto3", "botocore.exceptions"]
    instructions = f"""AWS Regions that are relevant: {", ".join(aws_regions)}."""

    if config.aws_profile and not use_sandbox_execution:
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
        # Use a Modal executor with credentials from the environment config
        logger = AgentLogger(level=LogLevel.INFO)
        executor = ModalExecutor(
            additional_imports=[],
            logger=logger,
            app_name="cora-smolagent-execution",
            create_kwargs={
                # The secret name is now strictly coming from MODAL_AWS_SECRET_NAME
                "secrets": [modal.Secret.from_name(config.modal_aws_secret_name)],
                "image": modal.Image.debian_slim().uv_pip_install(
                    "boto3", "jupyter", "jupyter_kernel_gateway"
                ),
            },
        )
        agent_kwargs["executor"] = executor
        agent_kwargs["tools"] = []

    agent = CodeAgent(**agent_kwargs)
    return agent
