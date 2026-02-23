import logging

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from src.session import SessionManager

logger = logging.getLogger(__name__)


class SessionPickerModal(ModalScreen[None]):
    """Modal screen for picking a session."""

    CSS = """
    SessionPickerModal {
        align: center middle;
    }

    #picker-container {
        width: 60;
        height: 20;
        border: solid $primary;
        background: $surface;
    }

    #picker-header {
        dock: top;
        height: auto;
        padding: 1 2;
        background: $primary-background;
        color: $text;
        text-style: bold;
    }

    #session-list {
        padding: 1 2;
    }

    .session-item {
        padding: 0 1;
    }

    .session-item.selected {
        background: $primary-background;
        color: $text;
    }

    #picker-footer {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: $surface;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "open_session", "Open"),
        Binding("up", "move_up", "Up"),
        Binding("down", "move_down", "Down"),
    ]

    def __init__(self, session_manager: SessionManager):
        super().__init__()
        self.session_manager = session_manager
        self._selected_index = 0
        # Load sessions synchronously before compose runs
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, schedule it
                asyncio.create_task(self._reload_sessions())
            else:
                loop.run_until_complete(self._reload_sessions())
        except Exception as e:
            logger.warning(f"Could not pre-load sessions: {e}")

    def on_mount(self) -> None:
        """Reload sessions from database when picker opens."""
        logger.debug("Session picker opened, reloading sessions from DB")
        self.run_worker(self._reload_sessions(), exclusive=False)

    async def _reload_sessions(self) -> None:
        """Reload sessions from database."""
        await self.session_manager.load_sessions()
        self._selected_index = 0
        self._refresh_list()
        sessions = self.session_manager.get_all_sessions()
        logger.debug(f"Reloaded {len(sessions)} sessions")

    def compose(self) -> ComposeResult:
        sessions = self.session_manager.get_all_sessions()
        logger.debug(f"Composing session picker with {len(sessions)} sessions")

        with Vertical(id="picker-container"):
            yield Static(
                "Sessions (↑↓ to navigate, Enter to open, Esc to close)",
                id="picker-header",
            )
            with Vertical(id="session-list"):
                if not sessions:
                    yield Static("No sessions available")
                else:
                    for i, session in enumerate(sessions):
                        is_selected = i == self._selected_index
                        prefix = "> " if is_selected else "  "
                        yield Static(
                            f"{prefix}[{session.id}] {session.title}",
                            classes="session-item selected"
                            if is_selected
                            else "session-item",
                        )
            yield Static("/new: new session", id="picker-footer")

    def action_move_up(self) -> None:
        sessions = self.session_manager.get_all_sessions()
        if not sessions:
            return
        self._selected_index = (self._selected_index - 1) % len(sessions)
        self._refresh_list()
        logger.debug(f"Moved selection up to index {self._selected_index}")

    def action_move_down(self) -> None:
        sessions = self.session_manager.get_all_sessions()
        if not sessions:
            return
        self._selected_index = (self._selected_index + 1) % len(sessions)
        self._refresh_list()
        logger.debug(f"Moved selection down to index {self._selected_index}")

    def _refresh_list(self) -> None:
        sessions = self.session_manager.get_all_sessions()
        container = self.query_one("#session-list", Vertical)
        container.remove_children()
        for i, session in enumerate(sessions):
            is_selected = i == self._selected_index
            prefix = "> " if is_selected else "  "
            container.mount(
                Static(
                    f"{prefix}[{session.id}] {session.title}",
                    classes="session-item selected" if is_selected else "session-item",
                )
            )

    def action_open_session(self) -> None:
        sessions = self.session_manager.get_all_sessions()
        logger.debug(
            f"Opening session, selected_index={self._selected_index}, sessions_count={len(sessions)}"
        )

        if not sessions:
            logger.warning("No sessions available to open")
            return

        if 0 <= self._selected_index < len(sessions):
            session = sessions[self._selected_index]
            logger.info(f"Opening session {session.id}: {session.title}")
            self.run_worker(self._switch_and_open(session.id), exclusive=True)
        else:
            logger.warning(f"Invalid selected_index: {self._selected_index}")

    async def _switch_and_open(self, session_id: int) -> None:
        logger.info(f"Switching to session {session_id}")
        await self.app.switch_to_session(session_id)
        self.app.pop_screen()
        from clients.tui.app import ChatScreen

        self.app.push_screen(ChatScreen(self.session_manager, self.app.agent))

    def action_close(self) -> None:
        logger.debug("Closing session picker")
        self.app.pop_screen()
