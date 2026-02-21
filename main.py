from smolagents import CodeAgent, InferenceClientModel, ApiModel, OpenAIModel
import os
from dotenv import load_dotenv

load_dotenv()

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

HF_TOKEN = os.getenv("HF_TOKEN")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

from langfuse import get_client

langfuse = get_client()

# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")


from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from smolagents import tool
import boto3

SmolagentsInstrumentor().instrument()

model = InferenceClientModel(model_id="Qwen/Qwen3-Coder-Next", api_key=HF_TOKEN)
# gemini_model = ApiModel(
#     model_id="gemini-2.5-flash-lite",
#     client="google/gemini"
# )
ollama_model = OpenAIModel(
    model_id="qwen2.5-coder:7b",
    api_base="http://localhost:11434/v1/",
    api_key="ollama",
)

openrouter_model = OpenAIModel(
    model_id="qwen/qwen3-coder",
    api_base="https://openrouter.ai/api/v1/",
    api_key=OPENROUTER_KEY
)


def prepend_query_with(prompt: str, query: str):
    return f"{prompt} | {query}"

console = Console()
@tool
def create_boto_client(service_name: str) -> object:
    """
    Create a boto3 client with a specified AWS profile.
    
    Args:
        service_name: The AWS service name (e.g., 's3', 'ec2', 'dynamodb')
    
    Returns:
        A boto3 client for the specified service
    """
    session = boto3.Session(profile_name='notisphere')
    return session.client(service_name)

def main():
    """Start an interactive chat session with the CodeAgent."""
    console.print(
        Panel(
            "[bold cyan]CodeAgent Chat[/bold cyan]\nType 'exit' or 'quit' to end the session.",
            expand=False,
        )
    )
    

    with CodeAgent(
        tools=[create_boto_client],
        model=openrouter_model,
        additional_authorized_imports=["botocore.exceptions"],
    ) as agent:
        while True:
            try:
                query = console.input("\n[bold green]You:[/bold green] ")

                if query.lower() in ["exit", "quit", "q"]:
                    console.print("[bold yellow]Goodbye![/bold yellow]")
                    break

                if not query.strip():
                    continue
                
                modified_query = prepend_query_with("""
                                                    NEVER USE the boto3 client directly. Use only the provided tool `create_boto_client` for getting the boto3 client
                                                    """, query)
                console.print("[bold blue]Agent:[/bold blue]\n", end=" ")
                response = agent.run(query)
                console.print(response)

            except KeyboardInterrupt:
                console.print("\n[bold yellow]Chat interrupted. Goodbye![/bold yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    typer.run(main)
