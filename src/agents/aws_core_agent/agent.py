# from pathlib import Path

# from src.config import get_config
# from src.models import create_model
# from src.tools import create_boto_client_tool


# from smolagents import ManagedAgent, CodeAgent, PromptTemplates
# from yaml import safe_load

# prompt_file_path = Path(__file__)/ "prompts" / "v1.yaml"

# with open(prompt_file_path) as f:
#     AWS_AGENT_SYSTEM_PROMPT = safe_load(f)

# def cora_manager_agent() -> ManagedAgent:
#     agent = ManagedAgent(
#         name="CoraManagerAgent",
#         model=create_model(),
#         description="This agent redefines the user query, plans it, and breaks it down.",
#         stream_outputs=True,
#         managed_agents=[cora_agent],
#     )
#     return agent

# def cora_agent() -> CodeAgent:
#     config = get_config()
#     model = create_model()

#     tools = [create_boto_client_tool()]
#     additional_authorized_imports = ["botocore.exceptions", "json"]
#     if not config.has_aws_profile():
#         additional_authorized_imports.extend(["boto3", "botocore"])
#         tools.pop(0)

#     agent = CodeAgent(
#         tools=tools,
#         model=model,
#         planning_interval=5,
#         prompt_templates=AWS_AGENT_SYSTEM_PROMPT,
#         instructions="""All resources are in us-east-2 region unless specified otherwise""",
#         use_structured_outputs_internally=True,
#         stream_outputs=True,
#         additional_authorized_imports=additional_authorized_imports,
#     )
#     return agent
