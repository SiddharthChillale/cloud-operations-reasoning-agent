from rich.syntax import Syntax
from rich.text import Text
from textual import on
from textual.containers import Container, Horizontal
from textual.widgets import Button, RichLog, Static


class StepWidget(Container):
    """A collapsible step widget with RichLog for live terminal-style output."""

    DEFAULT_CSS = """
    StepWidget {
        height: auto;
        margin: 1 0;
    }
    
    StepWidget > .step-header {
        layout: horizontal;
        height: auto;
        padding: 0 1;
    }
    
    StepWidget .step-title {
        color: $accent;
        text-style: bold;
        width: auto;
    }
    
    StepWidget .expand-btn {
        min-width: 3;
        width: 3;
    }
    
    StepWidget .step-log {
        height: auto;
        max-height: 20;
        margin: 0;
        padding: 0;
    }
    
    StepWidget .step-log-container {
        border: solid $panel;
        margin: 1 0;
    }
    
    StepWidget .thought-label {
        color: $accent;
        text-style: italic;
    }
    
    StepWidget .thought-content {
        color: $text-muted;
        padding: 0 1;
    }
    
    StepWidget .code-label {
        color: $accent;
    }
    
    StepWidget .result-label {
        color: $success;
    }
    
    StepWidget .result-error {
        color: $error;
    }
    """

    def __init__(self, step_number: int, is_planning: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.step_number = step_number
        self.is_planning = is_planning
        self._expanded = not is_planning  # Planning steps start expanded
        self._log_container: Container | None = None
        self._rich_log: RichLog | None = None
        self._pending_thought: str | None = None
        self._pending_code: str | None = None
        self._pending_result: str | None = None
        self._pending_is_error: bool = False
        self._pending_plan: str | None = None

    def compose(self):
        title = "Plan Step" if self.is_planning else f"Step {self.step_number}"
        with Horizontal(classes="step-header"):
            yield Static(title, classes="step-title")
            if not self.is_planning:
                yield Button("▼", id="expand-btn", classes="expand-btn")
            else:
                yield Button("▼", id="expand-btn", classes="expand-btn")

        yield Container(classes="step-log-container", id="log-container")

    def on_mount(self) -> None:
        self._log_container = self.query_one("#log-container", Container)
        self._rich_log = RichLog(
            id="step-log",
            classes="step-log",
            markup=True,
            auto_scroll=True,
            highlight=True,
        )
        self._log_container.mount(self._rich_log)

        # Set initial display state (expanded for planning, collapsed for action)
        if not self._expanded and self._log_container:
            self._log_container.display = False
            btn = self.query_one("#expand-btn", Button)
            btn.label = "▶"

        self._flush_pending()

    def _flush_pending(self) -> None:
        """Write any pending content to the RichLog after mount."""
        if self._pending_plan:
            self._write_plan_impl(self._pending_plan)
            self._pending_plan = None
        if self._pending_thought:
            self._write_thought_impl(self._pending_thought)
            self._pending_thought = None
        if self._pending_code:
            self._write_code_impl(self._pending_code)
            self._pending_code = None
        if self._pending_result:
            self._write_result_impl(self._pending_result, self._pending_is_error)
            self._pending_result = None

    def write_plan(self, plan: str) -> None:
        """Write the planning step content."""
        if not plan:
            return
        if self._rich_log:
            self._write_plan_impl(plan)
        else:
            self._pending_plan = plan

    def _write_plan_impl(self, plan: str) -> None:
        """Internal implementation of write_plan."""
        plan_label = Text("Plan: ", style="bold $accent")
        plan_text = Text(plan, style="$text")
        self._rich_log.write(plan_label + plan_text)

    @on(Button.Pressed, "#expand-btn")
    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        btn = self.query_one("#expand-btn", Button)

        if self._expanded:
            self._log_container.display = True
            btn.label = "▼"
        else:
            self._log_container.display = False
            btn.label = "▶"

    def write_thought(self, thought: str) -> None:
        """Write the agent's thought in italics."""
        if not thought:
            return
        if self._rich_log:
            self._write_thought_impl(thought)
        else:
            self._pending_thought = thought

    def _write_thought_impl(self, thought: str) -> None:
        """Internal implementation of write_thought."""
        thought_label = Text("Thought: ", style="bold italic $accent")
        thought_text = Text(thought, style="italic $text-muted")
        self._rich_log.write(thought_label + thought_text)

    def write_code(self, code: str) -> None:
        """Write the code action as a syntax-highlighted block."""
        if not code:
            return
        if self._rich_log:
            self._write_code_impl(code)
        else:
            self._pending_code = code

    def _write_code_impl(self, code: str) -> None:
        """Internal implementation of write_code."""
        code_label = Text("Code:\n", style="bold $accent")
        syntax = Syntax(code, "python", theme="monokai", indent_guides=True)
        self._rich_log.write(code_label)
        self._rich_log.write(syntax, shrink=False, expand=True)

    def write_result(self, result: str, is_error: bool = False) -> None:
        """Write the execution result in terminal style."""
        if not result:
            return
        if self._rich_log:
            self._write_result_impl(result, is_error)
        else:
            self._pending_result = result
            self._pending_is_error = is_error

    def _write_result_impl(self, result: str, is_error: bool) -> None:
        """Internal implementation of write_result."""
        if is_error:
            result_label = Text("Error: ", style="bold $error")
            result_style = "$error"
        else:
            result_label = Text("Result: ", style="bold $success")
            result_style = "$text"

        result_text = Text(result, style=result_style)
        self._rich_log.write(result_label + result_text)

    def write_line(self, line: str) -> None:
        """Write a raw line to the log."""
        if self._rich_log:
            self._rich_log.write(line, scroll_end=True)
        else:
            self._pending_result = (self._pending_result or "") + line + "\n"

    def write_code_start(self) -> None:
        """Write the code section header."""
        if self._rich_log:
            code_label = Text("Code:\n", style="bold $accent")
            self._rich_log.write(code_label, scroll_end=True)

    def write_result_start(self, is_error: bool = False) -> None:
        """Write the result section header."""
        if self._rich_log:
            if is_error:
                result_label = Text("Error: ", style="bold $error")
            else:
                result_label = Text("Result: ", style="bold $success")
            self._rich_log.write(result_label, scroll_end=True)

    def collapse(self) -> None:
        """Collapse the step to show only the header."""
        if self._expanded and self._log_container:
            self._expanded = False
            self._log_container.display = False
            btn = self.query_one("#expand-btn", Button)
            btn.label = "▶"

    def expand_content(self) -> None:
        """Expand the step to show full content."""
        if not self._expanded and self._log_container:
            self._expanded = True
            self._log_container.display = True
            btn = self.query_one("#expand-btn", Button)
            btn.label = "▼"

    @property
    def is_expanded(self) -> bool:
        return self._expanded
