import asyncio

from pyfiglet import figlet_format
from rich.align import Align
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, LoadingIndicator, Static

from clients.tui.screens import ChatScreen
from clients.tui.modals import SessionPickerModal, ThemePickerModal
from src.session import SessionManager

CORPUS_ASCII = Text(figlet_format("CORA", font="slant"), style="bold green")


class WelcomeScreen(Screen):
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, session_manager: SessionManager, agent, app_ref):
        super().__init__()
        self.session_manager = session_manager
        self.agent = agent
        self.app_ref = app_ref

    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            with Container(id="welcome-center"):
                with Container(id="welcome-message"):
                    yield Static(Align.center(CORPUS_ASCII), id="ascii-header")
                    yield Static(
                        "[dim]Press Enter to send. Ctrl+C to quit.[/dim]",
                        id="help-text",
                    )
                    yield Static("", id="welcome-status")

                with Container(id="welcome-input-area"):
                    yield Input("", id="query-input")

            with Horizontal(id="status-bar"):
                yield LoadingIndicator(id="spinner")
                from src.config import get_config

                config = get_config()
                yield Static(config.llm_model_id, id="model-id")
                yield Static(config.llm_provider, id="provider")
                yield Static("In: 0", id="input-tokens")
                yield Static("Out: 0", id="output-tokens")
                yield Static(
                    Text(
                        "/new /sessions /help /theme /quit",
                        style="$text-muted",
                    ),
                    id="exit-hint",
                )

    def on_mount(self) -> None:
        query_input = self.query_one("#query-input", Input)
        query_input.focus()

    @on(Input.Submitted, "#query-input")
    def _handle_input_submit(self, event: Input.Submitted) -> None:
        self._process_query()

    def _process_query(self) -> None:
        query_input = self.query_one("#query-input", Input)
        query = query_input.value.strip()

        if not query:
            return

        if query.startswith("/"):
            self._handle_slash_command(query)
            return

        query_input.value = ""

        title = query[:50] + "..." if len(query) > 50 else query

        self.app_ref.call_later(self._create_session_and_navigate, query, title)

    def _handle_slash_command(self, query: str) -> None:
        parts = query.split(None, 1)
        command = parts[0].lower()
        status_widget = self.query_one("#welcome-status", Static)
        query_input = self.query_one("#query-input", Input)
        query_input.value = ""

        if command == "/new":
            status_widget.update("[dim]Already on welcome screen[/dim]")
        elif command == "/sessions":
            self.app_ref.push_screen(SessionPickerModal(self.session_manager))
        elif command == "/theme":
            self.app_ref.push_screen(ThemePickerModal())
        elif command == "/help":
            help_text = """
[bold]Available commands:[/bold]
[cyan]/new[/cyan]      - Create a new session
[cyan]/sessions[/cyan] - Open session picker
[cyan]/theme[/cyan]    - Open theme picker
[cyan]/quit[/cyan]     - Quit the application
[cyan]/help[/cyan]     - Show this help message

[dim]Enter a query and press Enter to start chatting.[/dim]
"""
            status_widget.update(help_text.strip())
        elif command == "/quit":
            self.app_ref.exit()
        else:
            status_widget.update(
                f"[dim]Command '{command}' not available on welcome screen. Enter a query to start chatting.[/dim]"
            )

    async def _create_session_and_navigate(self, query: str, title: str) -> None:
        await self.session_manager.create_session(title)

        chat_screen = ChatScreen(self.session_manager, self.agent)
        self.app_ref.pop_screen()
        self.app_ref.push_screen(chat_screen)

        await asyncio.sleep(0.1)

        chat_screen.run_query_on_mount(query)
