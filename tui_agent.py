from textual.app import ComposeResult, RenderResult, App
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Button, RichLog, LoadingIndicator
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

CORPUS_ASCII = Text(figlet_format("CORA", font="slant"), style="bold green")

load_dotenv()

# Setup logging to both file and console
log_file = f"tui_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
    ],
)
logger = logging.getLogger(__name__)
# logger.info(f"Logging to {log_file}")

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


class ChatHistoryPanel(Static):
    """Panel that displays chat history."""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.pending_query_widget = None

    def add_user_message(self, message: str):
        """Add a user message to the chat history."""
        widget = Static(
            f"\nYou: {message}", classes="user-msg pending-query", markup=False
        )
        widget.styles.color = "yellow"
        self.mount(widget)
        self.pending_query_widget = widget
        return widget

    def add_agent_message(self, message: str):
        """Add an agent message to the chat history."""
        widget = Static(f"\nAgent: {message}", classes="agent-msg")
        widget.styles.color = "green"
        self.mount(widget)

    def add_system_message(self, message: str):
        """Add a system message to the chat history."""
        widget = Static(f"\n[System] {message}", classes="system-msg")
        widget.styles.color = "#666666"
        self.mount(widget)
        return widget

    def clear_pending_border(self):
        """Remove the green border from the pending query."""
        if self.pending_query_widget:
            self.pending_query_widget.remove_class("pending-query")
            self.pending_query_widget = None


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

            # Model info row
            with Horizontal(id="model-info"):
                yield Static("qwen/qwen3-coder", id="model-name")
                yield Static("", id="query-time")

            # Input area
            with Horizontal(id="input-area"):
                yield Input("Type your query...", id="query-input")
                yield Button("⏎", id="send-btn", variant="primary")

            # Status bar with spinner and exit hint
            with Horizontal(id="status-bar"):
                yield LoadingIndicator(id="spinner")
                yield Static(
                    Text("ctrl+c ", style="white") + Text("exit", style="#666666"),
                    id="exit-hint",
                )

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
        spinner = self.query_one("#spinner")

        query = query_input.value.strip()

        if not query:
            return

        # Add user message
        chat_history.add_user_message(query)
        query_input.value = ""

        # Show spinner
        spinner.display = True

        # Process with agent in background
        self.run_worker(
            self._run_agent(query),
            exclusive=True,
        )

    async def _run_agent(self, query: str) -> None:
        """Run the agent query in a worker thread."""
        chat_history = self.query_one("#chat-history", ChatHistoryPanel)
        spinner = self.query_one("#spinner")
        query_time = self.query_one("#query-time", Static)

        try:
            thinking_msg = chat_history.add_system_message("Agent is thinking...")

            import time

            start_time = time.time()

            # Run agent in thread pool to avoid blocking the TUI
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.executor, self.agent.run, query)

            elapsed = time.time() - start_time
            if elapsed < 60:
                time_str = f"{elapsed:.1f}s"
            else:
                mins = int(elapsed // 60)
                secs = elapsed % 60
                time_str = f"{mins}m {secs:.0f}s"
            query_time.update(f"{time_str}")

            # Remove thinking message
            thinking_msg.remove()

            chat_history.add_agent_message(str(response))
        except Exception as e:
            logger.exception(f"Error processing query: {query}")
            chat_history.add_system_message(f"Error: {str(e)}")
        finally:
            # Hide spinner
            spinner.display = False
            # Clear pending border
            chat_history.clear_pending_border()
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
    
    #model-info {
        dock: bottom;
        height: auto;
        padding: 0 2;
        background: $surface;
        color: #666666;
    }
    
    #model-name {
        width: 100%;
    }
    
    #query-time {
        width: 100%;
        text-align: right;
    }
    
    #status-bar {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: $surface;
        color: #aaaaaa;
    }
    
    #spinner {
        width: 20;
        display: none;
    }
    
    #spinner.active {
        display: block;
    }
    
    #exit-hint {
        width: 100%;
        text-align: right;
    }
    
    #query-input {
        width: 100%;
        min-height: 3;
        max-height: 8;
        background: #333333;
        border-left: thick green;
        border-top: none;
        border-right: none;
        border-bottom: none;
        color: white;
        padding: 1 2;
    }
    
    #send-btn {
        min-width: 4;
    }
    
    .pending-query {
        border-left: thick green;
        border-top: none;
        border-right: none;
        border-bottom: none;
        padding: 0 2;
    }
    
    .user-msg {
        padding: 0 2;
    }
    
    .agent-msg {
        padding: 0 2;
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
