import logging

from textual.containers import Vertical
from textual.widgets import Static

from clients.tui.widgets import StepsTabbedContent

logger = logging.getLogger(__name__)


class ChatHistoryPanel(Static):
    """Panel that displays chat history with query sections."""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self._query_sections: list[Vertical] = []

    def add_query_section(
        self, query_text: str, query_number: int
    ) -> tuple[Vertical, "StepsTabbedContent", Static]:
        """Create a new query section with tabs. Returns (container, steps_tabs, final_container)."""
        query_section = Vertical(
            id=f"query-section-{query_number}", classes="query-section"
        )

        self.mount(query_section)

        query_section.mount(Static(f"> {query_text}", classes="query-text"))

        steps_tabs = StepsTabbedContent(id=f"steps-tabs-{query_number}")
        query_section.mount(steps_tabs)

        final_container = Static(
            id=f"final-answer-{query_number}", classes="final-answer-section"
        )
        query_section.mount(final_container)

        self._query_sections.append(query_section)

        logger.debug(f"ChatHistoryPanel: added query section {query_number}")

        return query_section, steps_tabs, final_container

    def add_system_message(self, message: str) -> Static:
        """Add a system message to the chat history."""
        widget = Static(f"\n[System] {message}", classes="system-msg")
        self.mount(widget)
        return widget

    def clear_pending_border(self) -> None:
        """No-op for compatibility."""
        pass
