from smolagents import CodeAgent

from src.config import get_config
from src.models import create_model, DEFAULT_MODEL_ID


def diagramer_agent(
    use_sandbox_execution=True,
    model_id: str = DEFAULT_MODEL_ID,
) -> CodeAgent:
    """Create a Diagramer agent that generates architecture diagrams from AWS resources."""
    config = get_config()
    model = create_model(model_id)

    additional_authorized_imports = ["diagrams.*", "PIL.*", "io.*", "base64"]

    agent_kwargs = {
        "tools": [],
        "model": model,
        "use_structured_outputs_internally": True,
        "stream_outputs": True,
        "planning_interval": 2,
        "max_steps": 10,
        "additional_authorized_imports": additional_authorized_imports,
    }

    if use_sandbox_execution:
        from smolagents.remote_executors import ModalExecutor
        from smolagents.monitoring import AgentLogger, LogLevel
        import modal

        logger = AgentLogger(level=LogLevel.INFO)
        executor = ModalExecutor(
            additional_imports=[],
            logger=logger,
            app_name="diagramer-smolagent-execution",
            create_kwargs={
                "secrets": [modal.Secret.from_name(config.modal_aws_secret_name)],
                "image": modal.Image.debian_slim().uv_pip_install(
                    "diagrams", "Pillow", "jupyter", "jupyter_kernel_gateway"
                ),
            },
        )
        agent_kwargs["executor"] = executor

    agent = CodeAgent(**agent_kwargs)
    return agent
