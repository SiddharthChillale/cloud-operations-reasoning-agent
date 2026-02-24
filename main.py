from dotenv import load_dotenv

load_dotenv()

# from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from src.config import get_config
from src.utils import setup_logging

# SmolagentsInstrumentor().instrument()

logger = setup_logging()

import typer

config = get_config()
# if config.has_langfuse():
#     from langfuse import Langfuse

#     langfuse = Langfuse(
#         secret_key=config.langfuse_secret_key,
#         public_key=config.langfuse_public_key,
#         host=config.langfuse_base_url,
#     )
#     if langfuse.auth_check():
#         logger.info("Langfuse client is authenticated and ready!")
#     else:
#         logger.warning("Langfuse setup failed. Please check your credentials and host.")
# else:
#     langfuse = None
#     logger.info("Langfuse not configured. Observability disabled.")


def run_tui():
    """Launch the Textual TUI application."""
    from clients.tui.app import ChatApp

    app = ChatApp()
    app.run()


def main():
    """Launch the Textual TUI application."""
    run_tui()


if __name__ == "__main__":
    typer.run(main)
