import asyncio
from concurrent.futures import ThreadPoolExecutor

from pyfiglet import figlet_format
from rich.align import Align
from rich.panel import Panel
from rich.text import Text
from smolagents.memory import ActionStep, FinalAnswerStep, PlanningStep
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Collapsible,
    Input,
    LoadingIndicator,
    Markdown,
    Static,
)

from src.agents import create_aws_agent
from src.utils import setup_logger

CORPUS_ASCII = Text(figlet_format("CORA", font="slant"), style="bold green")

logger = setup_logger(__name__)


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
        widget.styles.color = "aliceblue"
        self.mount(widget)

    def add_system_message(self, message: str):
        """Add a system message to the chat history."""
        widget = Static(f"\n[System] {message}", classes="system-msg")
        widget.styles.color = "#666666"
        self.mount(widget)
        return widget

    def add_thinking(self, step_number: int, model_output: str, code_action: str):
        """Add a collapsible thinking box for a step."""
        header = f"Step #{step_number}"

        widgets = []
        if model_output:
            widgets.append(Static(f"Thought: {model_output}", classes="thought-text"))
        if code_action:
            widgets.append(Markdown(f"```python\n{code_action}\n```"))

        collapsible = Collapsible(
            *widgets, title=header, collapsed=True, classes="thinking-box"
        )
        self.mount(collapsible)

        return collapsible

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
        self._agent_running = False

    def on_unmount(self) -> None:
        """Clean up executor when screen unmounts."""
        self.executor.shutdown(wait=False)

    def compose(self) -> ComposeResult:
        """Compose the layout."""
        with Vertical(id="main-container"):
            with Container(id="welcome-header"):
                yield Static(Align.center(CORPUS_ASCII), id="ascii-header")
                yield Static(
                    "[dim]Press Enter to send. Ctrl+C to quit.[/dim]", id="help-text"
                )

            yield ChatHistoryPanel(id="chat-history")

            with Horizontal(id="model-info"):
                yield Static("qwen/qwen3-coder", id="model-name")
                yield Static("", id="query-time")

            with Horizontal(id="input-area"):
                yield Input("Type your query...", id="query-input")
                yield Button("⏎", id="send-btn", variant="primary")

            with Horizontal(id="status-bar"):
                yield LoadingIndicator(id="spinner")
                yield Static(
                    Text("ctrl+c ", style="white") + Text("exit", style="#666666"),
                    id="exit-hint",
                )

    def on_mount(self) -> None:
        """Initialize the chat when the screen mounts."""
        try:
            self.agent = create_aws_agent()
            logger.info("Agent initialized successfully")

            chat_history = self.query_one("#chat-history", ChatHistoryPanel)

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

        chat_history.add_user_message(query)
        query_input.value = ""

        spinner.display = True

        self._agent_running = True
        self.run_worker(
            self._run_agent(query),
            exclusive=True,
        )

    async def _run_agent(self, query: str) -> None:
        """Run the agent query in a worker thread with streaming."""
        chat_history = self.query_one("#chat-history", ChatHistoryPanel)
        spinner = self.query_one("#spinner")
        query_time = self.query_one("#query-time", Static)

        try:
            import time

            start_time = time.time()

            def stream_agent():
                """Run agent in thread and yield steps."""
                return self.agent.run(query, stream=True)

            loop = asyncio.get_event_loop()
            stream_gen = await loop.run_in_executor(self.executor, stream_agent)

            def get_next_step():
                """Get next step from generator in thread."""
                try:
                    return next(stream_gen)
                except StopIteration:
                    return None
                except Exception as e:
                    logger.error(f"Error getting next step: {e}")
                    return None

            while self._agent_running:
                step = await loop.run_in_executor(self.executor, get_next_step)

                if step is None:
                    break

                if isinstance(step, PlanningStep):
                    continue

                elif isinstance(step, ActionStep):
                    step_number = step.step_number

                    model_output = None
                    if step.model_output:
                        thought = step.model_output
                        if isinstance(thought, str):
                            model_output = thought
                        else:
                            model_output = str(thought)

                    code_action = step.code_action

                    if model_output or code_action:

                        def add_thinking():
                            chat_history.add_thinking(
                                step_number, model_output or "", code_action or ""
                            )
                            self.screen.refresh()

                        self.call_later(add_thinking)

                elif isinstance(step, FinalAnswerStep):

                    def finish():
                        chat_history.add_agent_message(str(step.output))
                        self.screen.refresh()

                    self.call_later(finish)
                    break

                await asyncio.sleep(0)

            elapsed = time.time() - start_time
            if elapsed < 60:
                time_str = f"{elapsed:.1f}s"
            else:
                mins = int(elapsed // 60)
                secs = elapsed % 60
                time_str = f"{mins}m {secs:.0f}s"

            def update_time():
                query_time.update(f"{time_str}")

            self.call_later(update_time)

        except Exception as e:
            logger.exception(f"Error processing query: {query}")

            def show_error():
                chat_history.add_system_message(f"Error: {str(e)}")

            self.call_later(show_error)
        finally:
            self._agent_running = False

            def hide_spinner():
                spinner.display = False
                chat_history.clear_pending_border()
                query_input_widget = self.query_one("#query-input", Input)
                query_input_widget.focus()

            self.call_later(hide_spinner)


class ChatApp(App):
    """Main Textual application."""

    CSS = """
    Screen {
        background: #000000;
    }
    
    #main-container {
        height: 100%;
        dock: top;
    }
    
    #welcome-header {
        dock: top;
        height: auto;
        padding: 1 2;
        background: #000000;
    }
    
    #chat-history {
        height: 100%;
        margin: 1 2;
        overflow-y: auto;
        scrollbar-gutter: stable;
        scrollbar-size-vertical: 1;
        scrollbar-background: #000000;
        scrollbar-color: lavenderblush;
    }
    
    #model-info {
        dock: bottom;
        height: auto;
        padding: 0 2;
        background: $surface;
        color: #666666;
    }
    
    #input-area {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: #000000;
    }
    
    #model-info {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: $surface;
        color: #aaaaaa;
    }
    
    #model-name {
        width: 80%;
    }
    
    #query-time {
        width: 20%;
        text-align: right;
    }
    
    #status-bar {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: #000000;
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
        min-height: 6;
        max-height: 12;
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
        padding: 1 2 1 2;
    }
    
    .user-msg {
        padding: 0 2;
    }
    
    .agent-msg {
        padding: 0 2;
    }
    
    .thinking-box {
        background: #1a1a1a;
        margin: 1 0;
    }
    
    .thinking-box > Collapsible {
        background: #1a1a1a;
    }
    
    .thinking-box Collapsible {
        border: solid #333333;
        margin: 1 0;
    }
    
    .thinking-box Collapsible > .collapsible--title {
        color: #00ff00;
        text-style: bold;
        padding: 0 1;
    }
    
    .thinking-box Collapsible > .collapsible--title:hover {
        background: #333333;
    }
    
    .thinking-box Collapsible .collapsible--toggle {
        color: #00ff00;
    }
    
    .thought-text {
        color: #888888;
        padding: 0 1;
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
