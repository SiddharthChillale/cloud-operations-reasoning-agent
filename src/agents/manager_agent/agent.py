from pathlib import Path
from smolagents import CodeAgent
from yaml import safe_load

from src.config import get_config
from src.models import create_model, DEFAULT_MODEL_ID
from src.agents.aws_agent import cora_agent
from src.agents.diagramer_agent.agent import diagramer_agent


config = get_config()

prompt_file_path = Path(__file__).parent / "prompts" / "v1.yaml"

with open(prompt_file_path) as f:
    MANAGER_AGENT_SYSTEM_PROMPT = safe_load(f)


def manager_agent(
    use_sandbox_execution=True,
    model_id: str = DEFAULT_MODEL_ID,
) -> CodeAgent:
    """Create a Manager Agent that orchestrates AWS and Diagramer agents."""
    model = create_model(model_id)

    aws_sub_agent = cora_agent(
        use_sandbox_execution=use_sandbox_execution,
        model_id=model_id,
    )
    aws_sub_agent.name = "aws_agent"
    aws_sub_agent.description = (
        "AWS infrastructure specialist. Use this agent to query, audit, "
        "diagnose, or troubleshoot AWS resources, services, and configurations."
    )

    diagramer_sub_agent = diagramer_agent(
        use_sandbox_execution=use_sandbox_execution,
        model_id=model_id,
    )
    diagramer_sub_agent.name = "diagramer_agent"
    diagramer_sub_agent.description = (
        "Architecture diagram specialist. Use this agent to create visual "
        "diagrams of AWS resources and infrastructure."
    )

    agent_kwargs = {
        "tools": [],
        "model": model,
        "prompt_templates": MANAGER_AGENT_SYSTEM_PROMPT,
        "managed_agents": [aws_sub_agent, diagramer_sub_agent],
        "use_structured_outputs_internally": True,
        "stream_outputs": True,
        "planning_interval": 3,
        "max_steps": 20,
        "additional_authorized_imports": [
            "PIL",
        ],
    }

    if use_sandbox_execution:
        from smolagents.remote_executors import ModalExecutor
        from smolagents.monitoring import AgentLogger, LogLevel
        import modal

        logger = AgentLogger(level=LogLevel.INFO)
        executor = ModalExecutor(
            additional_imports=[],
            logger=logger,
            app_name="manager-smolagent-execution",
            create_kwargs={
                "secrets": [modal.Secret.from_name(config.modal_aws_secret_name)],
                "image": modal.Image.debian_slim().uv_pip_install(
                    "Pillow", "jupyter", "jupyter_kernel_gateway"
                ),
            },
        )
        agent_kwargs["executor"] = executor

    agent = CodeAgent(**agent_kwargs)
    return agent
