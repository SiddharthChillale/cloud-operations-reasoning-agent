import os
from dotenv import load_dotenv

load_dotenv()

import typer

from langfuse import get_client
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

SmolagentsInstrumentor().instrument()

langfuse = get_client()

if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")


def run_tui():
    """Launch the Textual TUI application."""
    from clients.tui.app import ChatApp

    app = ChatApp()
    app.run()


def run_cli():
    """Launch the CLI application."""
    from clients.cli.app import run

    run()


def main(tui: bool = typer.Option(False, "--tui", help="Launch TUI interface")):
    """Route to the appropriate client interface."""
    if tui:
        run_tui()
    else:
        run_cli()


if __name__ == "__main__":
    typer.run(main)
