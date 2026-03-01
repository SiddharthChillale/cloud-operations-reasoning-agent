import typer

from src.config import get_config
from src.utils import setup_logging

logger = setup_logging()

config = get_config()


def run_api():
    """Launch the FastAPI server."""
    from src.fastapi.app import app

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    """Launch the FastAPI server."""
    run_api()


if __name__ == "__main__":
    typer.run(main)
