from rich.console import Console
from rich.panel import Panel

from src.agents import cora_agent


def prepend_query_with(prompt: str, query: str):
    return f"{prompt} | {query}"


console = Console()


def run():
    """Start the CLI chat session."""
    console.print(
        Panel(
            "[bold cyan]CodeAgent Chat[/bold cyan]\nType 'exit' or 'quit' to end the session.",
            expand=False,
        )
    )

    with cora_agent() as agent:
        while True:
            try:
                query = console.input("\n[bold green]You:[/bold green] ")

                if query.lower() in ["exit", "quit", "q"]:
                    console.print("[bold yellow]Goodbye![/bold yellow]")
                    break

                if not query.strip():
                    continue

                prepend_query_with(
                    """
                    NEVER USE the boto3 client directly. Use only the provided tool `create_boto_client` for getting the boto3 client
                    """,
                    query,
                )
                console.print("[bold blue]Agent:[/bold blue]\n", end=" ")
                response = agent.run(query)
                console.print(response)

            except KeyboardInterrupt:
                console.print("\n[bold yellow]Chat interrupted. Goodbye![/bold yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
