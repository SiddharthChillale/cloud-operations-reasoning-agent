# from smolagents import CodeAgent
# from .agents.aws_core_agent import cora_manager_agent

# def manager_agent() -> CodeAgent:
#     agent = CodeAgent(
#         name="ManagerAgent",
#         description="This agent redefines the user query, plans it, and breaks it down. If required it will parallely spin up another agent to check only the logs",
#         stream_outputs=True,
#         managed_agents=[cora_manager_agent],
#     )
#     return agent
