from textual.app import ComposeResult, RenderResult, App
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Button, RichLog
from textual.screen import Screen
from textual.binding import Binding
from textual import on
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from smolagents import CodeAgent, OpenAIModel
import os
from dotenv import load_dotenv
import boto3
from smolagents import tool
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import sys
import pyfiglet
from pyfiglet import figlet_format
from datetime import datetime

CORPUS_ASCII = figlet_format("CORA", font="slant")

load_dotenv()

# Setup logging to both file and console
log_file = f"tui_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_file}")

# Setup
HF_TOKEN = os.getenv("HF_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

openrouter_model = OpenAIModel(
    model_id="qwen/qwen3-coder",
    api_base="https://openrouter.ai/api/v1/",
    api_key=OPENROUTER_KEY,
)


@tool
def create_boto_client(service_name: str) -> object:
    """
    Create a boto3 client with a specified AWS profile.

    Args:
        service_name: The AWS service name (e.g., 's3', 'ec2', 'dynamodb')

    Returns:
        A boto3 client for the specified service
    """
    session = boto3.Session(profile_name="notisphere")
    return session.client(service_name)


class ChatMessage(Static):
    """A styled chat message."""

    def __init__(self, message: str, is_user: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.is_user = is_user

    def render(self) -> RenderResult:
        if self.is_user:
            text = Text(f"You: {self.message}", style="bold green")
        else:
            text = Text(f"Agent: {self.message}", style="bold blue")
        return text


class ChatHistoryPanel(RichLog):
    """Panel that displays chat history."""

    def __init__(self, **kwargs):
        super().__init__(auto_scroll=True, wrap=True, **kwargs)

    def add_user_message(self, message: str):
        """Add a user message to the chat history."""
        self.write(Text(f"You: {message}", style="bold green"))

    def add_agent_message(self, message: str):
        """Add an agent message to the chat history."""
        self.write(Text(f"Agent: {message}", style="bold blue"))

    def add_system_message(self, message: str):
        """Add a system message to the chat history."""
        self.write(Text(f"[System] {message}", style="dim yellow"))


class ChatScreen(Screen):
    """Main chat interface for the agent."""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.agent = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.show_welcome = True

    def compose(self) -> ComposeResult:
        """Compose the layout."""
        with Vertical(id="main-container"):
            # Header with ASCII art - only shown initially
            with Container(id="welcome-header"):
                yield Static(Align.center(CORPUS_ASCII), id="ascii-header")
                yield Static(
                    "[dim]Press Enter to send. Ctrl+C to quit.[/dim]", id="help-text"
                )

            # Chat history - takes full available area
            yield ChatHistoryPanel(id="chat-history")

            # Input area
            with Horizontal(id="input-area"):
                yield Input("Type your query...", id="query-input")
                yield Button("⏎", id="send-btn", variant="primary")

    def on_mount(self) -> None:
        """Initialize the chat when the screen mounts."""
        try:
            self.agent = CodeAgent(
                tools=[create_boto_client],
                model=openrouter_model,
                additional_authorized_imports=["botocore.exceptions"],
            )
            logger.info("Agent initialized successfully")

            chat_history = self.query_one("#chat-history", ChatHistoryPanel)
            chat_history.add_system_message("Agent initialized. Ready to chat!")

            # Focus on input
            query_input = self.query_one("#query-input", Input)
            query_input.focus()
        except Exception as e:
            logger.exception("Failed to initialize agent")
            chat_history = self.query_one("#chat-history", ChatHistoryPanel)
            chat_history.add_system_message(f"Failed to initialize agent: {str(e)}")

    @on(Input.Submitted, "#query-input")
    def _handle_input_submit(self, event: Input.Submitted) -> None:
        """Handle when user presses Enter in the input field."""
        if self.show_welcome:
            self._hide_welcome()
        self._process_query()

    @on(Button.Pressed, "#send-btn")
    def _handle_button_press(self, event: Button.Pressed) -> None:
        """Handle when user clicks the Send button."""
        if self.show_welcome:
            self._hide_welcome()
        self._process_query()

    def _hide_welcome(self) -> None:
        """Hide the welcome ASCII art header."""
        self.show_welcome = False
        header = self.query_one("#welcome-header")
        header.display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle when user clicks the Send button."""
        if event.button.id == "send-btn":
            self._process_query()

    def _process_query(self) -> None:
        """Process the user's query."""
        query_input = self.query_one("#query-input", Input)
        chat_history = self.query_one("#chat-history", ChatHistoryPanel)

        query = query_input.value.strip()

        if not query:
            return

        # Add user message
        chat_history.add_user_message(query)
        query_input.value = ""

        # Process with agent in background
        self.run_worker(
            self._run_agent(query),
            exclusive=True,
        )

    async def _run_agent(self, query: str) -> None:
        """Run the agent query in a worker thread."""
        chat_history = self.query_one("#chat-history", ChatHistoryPanel)

        try:
            chat_history.add_system_message("Agent is thinking...")

            # Run agent in thread pool to avoid blocking the TUI
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.executor, self.agent.run, query)

            chat_history.add_agent_message(str(response))
        except Exception as e:
            logger.exception(f"Error processing query: {query}")
            chat_history.add_system_message(f"Error: {str(e)}")
        finally:
            # Re-focus input
            query_input = self.query_one("#query-input", Input)
            query_input.focus()


class ChatApp(App):
    """Main Textual application."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        dock: top;
    }
    
    #welcome-header {
        dock: top;
        height: auto;
        padding: 1 2;
        background: $surface;
    }
    
    #chat-history {
        height: 100%;
        border: solid $surface-darken-1;
        margin: 1 2;
    }
    
    #input-area {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: $surface;
        border-top: solid $surface-darken-1;
    }
    
    #query-input {
        width: 100%;
    }
    
    #send-btn {
        min-width: 4;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Mount the chat screen."""
        self.push_screen(ChatScreen())


def main():
    """Launch the Textual TUI application."""
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
