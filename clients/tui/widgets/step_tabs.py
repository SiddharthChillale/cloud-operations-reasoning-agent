import logging
from typing import Any

from rich.syntax import Syntax
from textual.containers import Vertical, VerticalScroll
from textual.widgets import (
    Markdown as TextualMarkdown,
    Static,
    TabbedContent,
    TabPane,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class StepsTabbedContent(Vertical):
    """Container for step tabs with dynamic tab management."""

    DEFAULT_CSS = """
    StepsTabbedContent {
        height: 30vh;
        border: solid $panel;
        margin: 1 0;
    }
    
    StepsTabbedContent > TabbedContent {
        height: 100%;
    }
    
    StepsTabbedContent > TabbedContent > TabPane {
        height: 100%;
        padding: 1;
    }
    
    StepsTabbedContent > TabbedContent > TabPane VerticalScroll {
        height: 100%;
        scrollbar-size-vertical: 1;
    }
    
    StepsTabbedContent .section-label {
        color: $accent;
        text-style: bold;
        margin-top: 1;
        padding: 0 1;
    }
    
    StepsTabbedContent .thought-text {
        color: $text-muted;
        padding: 0 1;
    }
    
    StepsTabbedContent .code-text {
        background: $surface;
        padding: 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._step_counter = 0
        self._plan_counter = 0
        self._tabbed_content: TabbedContent | None = None
        self._step_panes: dict[str, dict[str, Any]] = {}
        self._is_mounted = False

    def compose(self):
        logger.debug("StepsTabbedContent: compose called")
        yield TabbedContent(id="steps-tabs")

    def on_mount(self) -> None:
        logger.debug("StepsTabbedContent: on_mount called")
        self._tabbed_content = self.query_one("#steps-tabs", TabbedContent)
        self._is_mounted = True
        logger.debug(
            f"StepsTabbedContent: _tabbed_content set to {self._tabbed_content}"
        )

    def add_planning_tab(self, plan_text: str = "") -> str:
        """Add a new planning tab. Returns the tab id."""
        if not self._tabbed_content:
            logger.warning(
                "StepsTabbedContent: _tabbed_content is None in add_planning_tab, scheduling delayed add"
            )

            def delayed_add():
                self.add_planning_tab(plan_text)

            self.call_later(delayed_add)
            return ""

        self._plan_counter += 1
        tab_id = f"plan-{self._plan_counter}"
        tab_label = f"Plan {self._plan_counter}"

        logger.debug(
            f"StepsTabbedContent: Adding planning tab {tab_id}, plan_text={plan_text[:50] if plan_text else 'empty'}..."
        )

        pane = TabPane(tab_label, id=tab_id)
        self._tabbed_content.add_pane(pane)

        pane_content = VerticalScroll(id=f"{tab_id}-content")
        pane.mount(pane_content)

        markdown_widget = None
        if plan_text:
            markdown_widget = TextualMarkdown(plan_text, id=f"{tab_id}-markdown")
            pane_content.mount(markdown_widget)

        self._step_panes[tab_id] = {
            "type": "planning",
            "pane": pane,
            "content": pane_content,
            "markdown": markdown_widget,
        }

        try:
            self._tabbed_content.active = tab_id
        except Exception as e:
            logger.warning(f"Could not set active tab: {e}")

        logger.debug(f"StepsTabbedContent: Added planning tab {tab_id}")

        return tab_id

    def add_action_tab(self, step_number: int) -> str:
        """Add a new action step tab. Returns the tab id."""
        if not self._tabbed_content:
            logger.warning(
                "StepsTabbedContent: _tabbed_content is None in add_action_tab, scheduling delayed add"
            )

            def delayed_add():
                self.add_action_tab(step_number)

            self.call_later(delayed_add)
            return ""

        tab_id = f"step-{step_number}"
        tab_label = f"Step {step_number}"

        logger.debug(f"StepsTabbedContent: Adding action tab {tab_id}")

        pane = TabPane(tab_label, id=tab_id)
        self._tabbed_content.add_pane(pane)

        pane_content = VerticalScroll(id=f"{tab_id}-content", classes="step-content")
        pane.mount(pane_content)

        pane_content.mount(Static("Thought:", classes="section-label"))
        thought_display = Static(id=f"{tab_id}-thought", classes="thought-text")
        pane_content.mount(thought_display)

        pane_content.mount(Static("Code:", classes="section-label"))
        code_display = Static("", id=f"{tab_id}-code", classes="code-text")
        pane_content.mount(code_display)

        pane_content.mount(Static("Observations:", classes="section-label"))
        obs_markdown = TextualMarkdown("", id=f"{tab_id}-observations")
        pane_content.mount(obs_markdown)

        self._step_panes[tab_id] = {
            "type": "action",
            "pane": pane,
            "content": pane_content,
            "thought": thought_display,
            "code": code_display,
            "observations": obs_markdown,
        }

        logger.debug(f"StepsTabbedContent: Added action tab {tab_id}")

        return tab_id

    def update_planning_content(self, tab_id: str, plan_text: str) -> None:
        """Update the content of a planning tab."""
        if tab_id not in self._step_panes:
            return

        pane_data = self._step_panes[tab_id]
        content = pane_data["content"]

        if pane_data.get("markdown"):
            pane_data["markdown"].update(plan_text)
        else:
            md = TextualMarkdown(plan_text, id=f"{tab_id}-markdown")
            content.mount(md)
            pane_data["markdown"] = md

    def update_action_tab(
        self,
        tab_id: str,
        thought: str = "",
        code: str = "",
        observations: str = "",
    ) -> None:
        """Update the content of an action step tab."""
        if tab_id not in self._step_panes:
            return

        pane_data = self._step_panes[tab_id]

        if thought and pane_data.get("thought"):
            pane_data["thought"].update(thought)

        if code and pane_data.get("code"):
            syntax = Syntax(code, "python", theme="monokai", indent_guides=True)
            pane_data["code"].update(syntax)

        if observations and pane_data.get("observations"):
            pane_data["observations"].update(observations)

    def append_observations(self, tab_id: str, observations: str) -> None:
        """Append observations to an action step tab."""
        if tab_id not in self._step_panes:
            return

        pane_data = self._step_panes[tab_id]
        obs_widget = pane_data.get("observations")
        if obs_widget:
            current = obs_widget.source or ""
            new_content = current + "\n" + observations if current else observations
            obs_widget.update(new_content)

    def clear(self) -> None:
        """Clear all tabs."""
        if self._tabbed_content:
            self._tabbed_content.clear_panes()
        self._step_panes.clear()
        self._step_counter = 0
        self._plan_counter = 0
