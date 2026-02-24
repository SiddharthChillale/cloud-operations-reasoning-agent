from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import ListItem, ListView, Static

from src.config import get_config
from src.themes import BUILT_IN_THEMES


class ThemePickerModal(ModalScreen[None]):
    """Modal overlay for selecting theme."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._previous_theme: str | None = None

    def on_mount(self) -> None:
        self._previous_theme = self.app.theme
        list_view = self.query_one("#theme-list", ListView)
        list_view.focus()

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.action_close()
            event.prevent_default()
        elif event.key in ("up", "down"):
            list_view = self.query_one("#theme-list", ListView)
            current_index = list_view.index
            if current_index is None:
                return
            children = list_view.children
            if event.key == "down":
                new_index = current_index + 1
                if new_index >= len(children):
                    new_index = 0
            else:  # up
                new_index = current_index - 1
                if new_index < 0:
                    new_index = len(children) - 1
            if 0 <= new_index < len(children):
                selected_item = children[new_index]
                selected_theme = selected_item.id
                if selected_theme:
                    self.app.theme = selected_theme
                    self._update_checkmarks(selected_theme)

    def action_close(self) -> None:
        config = get_config()
        config.save_theme(self.app.theme)
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        config = get_config()
        current_theme = config.theme

        with Vertical(id="theme-picker"):
            yield Static("Choose Theme", id="title")
            with ListView(id="theme-list"):
                for theme_name in BUILT_IN_THEMES:
                    is_current = theme_name == current_theme
                    prefix = "[✓] " if is_current else "    "
                    yield ListItem(Static(f"{prefix}{theme_name}"), id=theme_name)
            yield Static("[Esc] Close", id="hint")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_theme = event.item.id
        if selected_theme:
            self.app.theme = selected_theme
            self._update_checkmarks(selected_theme)

    def _update_checkmarks(self, current: str) -> None:
        list_view = self.query_one("#theme-list", ListView)
        for item in list_view.children:
            theme_id = item.id
            prefix = "[✓] " if theme_id == current else "    "
            static_widget = item.query_one("Static")
            static_widget.update(f"{prefix}{theme_id}")
