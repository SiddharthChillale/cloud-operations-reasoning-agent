import logging
import pickle
from concurrent.futures import ThreadPoolExecutor

from textual.app import App
from textual.binding import Binding

from clients.tui.screens import WelcomeScreen
from src.agents import cora_agent
from src.config import get_config
from src.session import SessionManager
from src.themes import BUILT_IN_THEMES

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ChatApp(App):
    """Main Textual application."""

    CSS_PATH = [
        "styles.tcss",
        "modals/configure_modal.tcss",
        "modals/theme_picker.tcss",
        "modals/session_picker.tcss",
    ]

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.session_manager: SessionManager = SessionManager()
        self.agent = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._current_session_id: int | None = None

    async def on_mount(self) -> None:
        self._register_themes()
        await self.session_manager.initialize()
        self.agent = cora_agent()
        logger.info("Agent initialized successfully")
        self.push_screen(WelcomeScreen(self.session_manager, self.agent, self))

    async def on_shutdown(self) -> None:
        logger.info("Saving sessions before shutdown")
        if self.agent and self._current_session_id:
            try:
                agent_steps = pickle.dumps(self.agent.memory.steps)
                await self.session_manager.save_agent_steps(
                    self._current_session_id, agent_steps
                )
                logger.info(
                    f"Saved {len(self.agent.memory.steps)} steps for session {self._current_session_id}"
                )
            except Exception as e:
                logger.warning(f"Could not save agent steps: {e}")
        await self.session_manager.load_sessions()
        self.executor.shutdown(wait=False)

    def _register_themes(self) -> None:
        config = get_config()
        saved_theme = config.theme
        if saved_theme in BUILT_IN_THEMES:
            self.theme = saved_theme
        else:
            self.theme = "nord"

    async def switch_to_session(self, session_id: int) -> None:
        if self._current_session_id and self.agent:
            try:
                agent_steps = pickle.dumps(self.agent.memory.steps)
                await self.session_manager.save_agent_steps(
                    self._current_session_id, agent_steps
                )
            except Exception as e:
                logger.warning(f"Could not save agent steps: {e}")

        await self.session_manager.switch_session(session_id)
        self._current_session_id = session_id

        if self.agent:
            saved_steps = await self.session_manager.get_agent_steps(session_id)
            if saved_steps:
                try:
                    self.agent.memory.steps = pickle.loads(saved_steps)
                except Exception as e:
                    logger.warning(f"Could not restore agent steps: {e}")

        session = self.session_manager.get_current_session()
        if session and session.id:
            self._current_session_id = session.id


def main():
    """Launch the Textual TUI application."""
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
