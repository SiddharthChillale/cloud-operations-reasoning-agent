import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from pyfiglet import figlet_format
from rich.align import Align
from rich.text import Text
from smolagents.memory import ActionStep, PlanningStep
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Input,
    LoadingIndicator,
    Static,
)

from clients.tui.step_widget import StepWidget
from src.agents import cora_agent
from src.config import get_config
from src.session import SessionManager, MessageRole
from src.themes import BUILT_IN_THEMES

CORPUS_ASCII = Text(figlet_format("CORA", font="slant"), style="bold green")

logger = logging.getLogger(__name__)


class ChatHistoryPanel(Static):
    """Panel that displays chat history."""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.pending_query_widget = None

    def add_user_message(self, message: str):
        """Add a user message to the chat history."""
        widget = Static(f"\n{message}", classes="user-msg pending-query", markup=False)
        self.mount(widget)
        self.pending_query_widget = widget
        return widget

    def add_agent_message(self, message: str, message_class: str = "agent-msg"):
        """Add an agent message to the chat history."""
        widget = Static(f"\n{message}", classes=message_class)
        self.mount(widget)

    def add_system_message(self, message: str):
        """Add a system message to the chat history."""
        widget = Static(f"\n[System] {message}", classes="system-msg")
        self.mount(widget)
        return widget

    def add_thinking(
        self,
        step_number: int,
        model_output: str = "",
        code_action: str = "",
        execution_result: str = "",
    ):
        """Add a step widget with RichLog for live terminal-style output."""
        step_widget = StepWidget(step_number, classes="thinking-box")
        self.mount(step_widget)

        if model_output:
            step_widget.write_thought(model_output)
        if code_action:
            step_widget.write_code(code_action)
        if execution_result:
            is_error = "error" in execution_result.lower()
            step_widget.write_result(execution_result, is_error=is_error)

        return step_widget

    def add_planning(self, step_number: int, plan_text: str = ""):
        """Add a planning step widget with RichLog (expanded by default)."""
        step_widget = StepWidget(step_number, is_planning=True, classes="thinking-box")
        self.mount(step_widget)

        if plan_text:
            step_widget.write_plan(plan_text)

        return step_widget

    def stream_step_content(
        self,
        step_widget,
        thought: str,
        code: str,
        result: str,
        is_error: bool = False,
    ):
        """Stream step content line by line to an existing step widget."""
        if thought:
            step_widget.write_thought(thought)

        if code:
            step_widget.write_code_start()
            for line in code.split("\n"):
                step_widget.write_line(line + "\n")

        if result:
            step_widget.write_result_start(is_error)
            for line in result.split("\n"):
                step_widget.write_line(line + "\n")

    def add_step(self, step_number: int):
        """Create a new step widget for incremental updates."""
        step_widget = StepWidget(step_number, classes="thinking-box")
        self.mount(step_widget)
        return step_widget

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

    def __init__(self, session_manager: SessionManager, agent):
        super().__init__()
        self.session_manager = session_manager
        self.agent = agent
        self.show_welcome = True
        self._agent_running = False
        self._first_query_sent = False

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
                yield Input("", id="query-input")
                yield Button("⏎", id="send-btn", variant="primary")

            with Horizontal(id="status-bar"):
                yield LoadingIndicator(id="spinner")
                yield Static("", id="model-id")
                yield Static("", id="provider")
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
        """Initialize the chat when the screen mounts."""
        try:
            chat_history = self.query_one("#chat-history", ChatHistoryPanel)
            query_input = self.query_one("#query-input", Input)
            query_input.focus()

            # Set status bar model info
            config = get_config()
            model_id = self.query_one("#model-id", Static)
            provider = self.query_one("#provider", Static)
            model_id.update(config.llm_model_id)
            provider.update(config.llm_provider)

            # Reload session data and display chat history
            self.run_worker(self._load_session_and_history(), exclusive=False)

        except Exception as e:
            logger.exception("Failed to initialize chat screen")
            chat_history = self.query_one("#chat-history", ChatHistoryPanel)
            chat_history.add_system_message(f" {str(e)}")

    async def _load_session_and_history(self) -> None:
        """Load session from DB and display chat history."""
        session = self.session_manager.get_current_session()

        if session and session.id:
            # Reload session from DB to get latest messages
            fresh_session = await self.session_manager.get_session(session.id)
            if fresh_session:
                self.session_manager._current_session = fresh_session
                session = fresh_session
                logger.debug(
                    f"Reloaded session {session.id} with {len(session.messages)} messages"
                )

            # Load agent memory steps from DB
            saved_steps = await self.session_manager.get_agent_steps(session.id)
            if saved_steps:
                import pickle

                try:
                    self.agent.memory.steps = pickle.loads(saved_steps)
                    logger.info(
                        f"Restored {len(self.agent.memory.steps)} steps for session {session.id}"
                    )
                except Exception as e:
                    logger.warning(f"Could not restore agent steps: {e}")

            # Load cumulative token counts from DB
            metrics = await self.session_manager.get_metrics(session.id)
            if metrics:

                def update_tokens():
                    try:
                        input_widget = self.query_one("#input-tokens", Static)
                        output_widget = self.query_one("#output-tokens", Static)
                        input_widget.update(f"In: {metrics.get('input_tokens', 0)}")
                        output_widget.update(f"Out: {metrics.get('output_tokens', 0)}")
                    except Exception:
                        pass

                self.call_later(update_tokens)
                logger.info(
                    f"Loaded cumulative tokens: in={metrics.get('input_tokens', 0)}, out={metrics.get('output_tokens', 0)}"
                )

        # Load chat history
        chat_history = self.query_one("#chat-history", ChatHistoryPanel)
        chat_history.remove_children()

        if session and session.messages:
            for msg in session.messages:
                if msg.role == MessageRole.USER:
                    chat_history.add_user_message(msg.content)
                elif msg.role == MessageRole.AGENT:
                    chat_history.add_agent_message(msg.content)
                elif msg.role == MessageRole.SYSTEM:
                    chat_history.add_system_message(msg.content)
            if session.messages:
                self.show_welcome = False
                self.call_later(self._hide_welcome)
                logger.debug(
                    f"Displayed {len(session.messages)} messages in chat history"
                )

        # Restore step widgets from agent memory steps
        if (
            hasattr(self, "agent")
            and self.agent
            and hasattr(self.agent.memory, "steps")
        ):
            for step in self.agent.memory.steps:
                if isinstance(step, PlanningStep):
                    # Handle PlanningStep
                    plan_text = (
                        step.plan
                        if hasattr(step, "plan") and step.plan
                        else "Planning..."
                    )

                    def add_planning_widget():
                        chat_history.add_planning(0, plan_text)

                    self.call_later(add_planning_widget)

                elif isinstance(step, ActionStep):
                    step_number = step.step_number

                    logger.info(
                        "model_output: "
                        + str(step.model_output)
                        + " type: "
                        + str(type(step.model_output))
                    )
                    # Extract thought
                    model_output = None
                    if step.model_output:
                        thought = step.model_output
                        if isinstance(thought, str):
                            model_output = thought
                        elif isinstance(thought, dict):
                            model_output = (
                                thought.get("thought")
                                or thought.get("text")
                                or str(thought)
                            )
                        else:
                            model_output = str(thought)

                    code_action = step.code_action or ""
                    execution_result = step.observations or ""

                    # Create step widget (collapsed by default for historical steps)
                    def add_step_widget():
                        step_widget = chat_history.add_thinking(
                            step_number,
                            model_output or "",
                            code_action,
                            execution_result,
                        )
                        # Collapse historical steps
                        if step_widget:
                            step_widget.collapse()

                    self.call_later(add_step_widget)

        else:
            logger.debug("No messages to display")

        if self._agent_running:
            spinner = self.query_one("#spinner")
            spinner.display = True

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

        query_input.value = ""

        if query.startswith("/"):
            self._handle_slash_command(query, chat_history)
            return

        if not self._first_query_sent:
            self._first_query_sent = True
            title = query[:50] + "..." if len(query) > 50 else query
            session = self.session_manager.get_current_session()
            if session and session.id:
                # Update locally immediately for display
                session.title = title
                # Also save to DB synchronously (await directly)
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're in an async context, create a task
                        asyncio.create_task(
                            self._update_session_title(session.id, title)
                        )
                    else:
                        # Run synchronously if possible
                        loop.run_until_complete(
                            self._update_session_title(session.id, title)
                        )
                except Exception as e:
                    logger.warning(f"Could not update session title: {e}")

        chat_history.add_user_message(query)

        session = self.session_manager.get_current_session()
        if session and session.id:
            # Save message to DB synchronously
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._add_user_message(session.id, query))
                else:
                    loop.run_until_complete(self._add_user_message(session.id, query))
            except Exception as e:
                logger.warning(f"Could not save user message: {e}")

        spinner = self.query_one("#spinner")
        spinner.display = True

        self._agent_running = True
        self.run_worker(
            self._run_agent(query),
            exclusive=True,
        )

    def _handle_slash_command(self, query: str, chat_history: ChatHistoryPanel) -> None:
        """Handle slash commands."""
        parts = query.split(None, 1)
        command = parts[0].lower()

        if command == "/new":
            chat_history.add_system_message("Creating new session...")
            self.app.call_later(self._create_new_session)
        elif command == "/sessions":
            chat_history.add_system_message("Opening session picker...")
            self.app.call_later(self._open_session_picker)
        elif command == "/theme":
            chat_history.add_system_message("Opening theme picker...")
            self.app.call_later(self._open_theme_picker)
        elif command == "/quit":
            chat_history.add_system_message("Quitting...")
            self.app.call_later(self.app.exit)
        elif command == "/help":
            help_text = """
Available commands:
/new      - Create a new session
/sessions - Open session picker
/theme    - Open theme picker
/quit     - Quit the application
/help     - Show this help message
/debug    - Show debug info (session state, agent state)

Any other command starting with / will be sent to the AI agent.
"""
            chat_history.add_system_message(help_text.strip())
        elif command == "/debug":
            self._show_debug_info(chat_history)
        else:
            chat_history.add_user_message(query)
            self._send_to_agent(query, chat_history)

    async def _create_new_session(self) -> None:
        await self.session_manager.create_session()
        from clients.tui.app import ChatScreen

        self.app.pop_screen()
        self.app.push_screen(ChatScreen(self.session_manager, self.app.agent))

    def _open_session_picker(self) -> None:
        from clients.tui.session_picker import SessionPickerModal

        self.app.push_screen(SessionPickerModal(self.session_manager))

    def _open_theme_picker(self) -> None:
        from clients.tui.theme_picker import ThemePickerModal

        self.app.push_screen(ThemePickerModal())

    def _show_debug_info(self, chat_history: ChatHistoryPanel) -> None:
        """Show debug info about current session state."""
        session = self.session_manager.get_current_session()

        debug_lines = ["=== DEBUG INFO ==="]

        debug_lines.append(f"Current session: {session.id if session else 'None'}")
        debug_lines.append(f"Current title: {session.title if session else 'N/A'}")
        debug_lines.append(f"Messages count: {len(session.messages) if session else 0}")
        debug_lines.append(f"Agent running: {self._agent_running}")

        if self.agent:
            debug_lines.append(f"Agent memory steps: {len(self.agent.memory.steps)}")
        else:
            debug_lines.append("Agent: None")

        debug_lines.append("")
        debug_lines.append("All sessions:")
        all_sessions = self.session_manager.get_all_sessions()
        for s in all_sessions:
            debug_lines.append(f"  [{s.id}] {s.title} (active: {s.is_active})")

        debug_lines.append("=================")

        chat_history.add_system_message("\n".join(debug_lines))

        logger.debug(
            f"Debug info: session={session.id if session else 'None'}, "
            f"title={session.title if session else 'N/A'}, "
            f"messages={len(session.messages) if session else 0}, "
            f"agent_running={self._agent_running}, "
            f"memory_steps={len(self.agent.memory.steps) if self.agent else 0}"
        )

    def _send_to_agent(self, query: str, chat_history: ChatHistoryPanel) -> None:
        """Send query to agent (for unrecognized slash commands)."""
        spinner = self.query_one("#spinner")
        spinner.display = True

        session = self.session_manager.get_current_session()
        if session and session.id:
            self.run_worker(
                self._add_user_message(session.id, query),
                exclusive=False,
            )

        self._agent_running = True
        self.run_worker(
            self._run_agent(query),
            exclusive=True,
        )

    async def _update_session_title(self, session_id: int, title: str) -> None:
        await self.session_manager.update_session_title(session_id, title)

    async def _add_user_message(self, session_id: int, content: str) -> None:
        await self.session_manager.add_message(MessageRole.USER, content)

    async def _add_agent_message(self, session_id: int, content: str) -> None:
        await self.session_manager.add_message(MessageRole.AGENT, content)

    async def _save_agent_step(self, session_id: int, content: str) -> None:
        """Save agent step to database - works even if session not active."""
        try:
            await self.app.session_manager.add_message(
                MessageRole.AGENT, content, session_id
            )
            logger.debug(f"Saved agent step to session {session_id}")
        except Exception as e:
            logger.warning(f"Could not save agent step: {e}")

    async def _update_token_counts(self) -> None:
        """Get token counts from agent monitor and update status bar."""
        try:
            token_counts = self.agent.monitor.get_total_token_counts()
            input_tokens = token_counts.input_tokens
            output_tokens = token_counts.output_tokens

            def update_ui():
                try:
                    input_widget = self.query_one("#input-tokens", Static)
                    output_widget = self.query_one("#output-tokens", Static)
                    input_widget.update(f"In: {input_tokens}")
                    output_widget.update(f"Out: {output_tokens}")
                except Exception:
                    pass

            self.call_later(update_ui)

            session = self.session_manager.get_current_session()
            if session and session.id:
                asyncio.create_task(
                    self.session_manager.save_metrics(
                        session.id,
                        get_config().llm_model_id,
                        get_config().llm_provider,
                        input_tokens,
                        output_tokens,
                    )
                )
        except Exception as e:
            logger.debug(f"Could not get token counts: {e}")

    async def _run_agent(self, query: str) -> None:
        """Run the agent query in a worker thread with streaming."""
        chat_history = self.query_one("#chat-history", ChatHistoryPanel)
        spinner = self.query_one("#spinner")
        query_time = self.query_one("#query-time", Static)

        # Log agent memory state before running
        logger.info("=== AGENT MEMORY BEFORE RUN ===")
        logger.info(f"Memory steps count: {len(self.agent.memory.steps)}")
        for i, step in enumerate(self.agent.memory.steps):
            logger.info(f"  Step {i}: {type(step).__name__}")
        logger.info("===============================")

        try:
            import time

            start_time = time.time()

            def stream_agent():
                """Run agent in thread and yield steps."""
                return self.agent.run(query, stream=True)

            loop = asyncio.get_event_loop()
            stream_gen = await loop.run_in_executor(self.app.executor, stream_agent)

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
                step = await loop.run_in_executor(self.app.executor, get_next_step)

                if step is None:
                    break

                if isinstance(step, PlanningStep):
                    plan_text = (
                        step.plan
                        if hasattr(step, "plan") and step.plan
                        else "Planning..."
                    )

                    # Create planning step widget (expanded by default)
                    # Use 0 for planning steps since they don't have step_number
                    def add_planning():
                        chat_history.add_planning(0, plan_text)
                        self.screen.refresh()

                    self.call_later(add_planning)
                    continue

                elif isinstance(step, ActionStep):
                    step_number = step.step_number

                    # Extract thought from model_output
                    model_output = None
                    if step.model_output:
                        thought = step.model_output
                        if isinstance(thought, str):
                            # Try to parse as JSON in case it's a JSON string
                            import json

                            try:
                                parsed = json.loads(thought)
                                if isinstance(parsed, dict):
                                    thought = (
                                        parsed.get("thought")
                                        or parsed.get("text")
                                        or parsed.get("reasoning")
                                        or thought
                                    )
                            except (json.JSONDecodeError, TypeError):
                                pass  # Not JSON, use as-is
                            model_output = thought
                        elif isinstance(thought, dict):
                            model_output = (
                                thought.get("thought")
                                or thought.get("text")
                                or thought.get("reasoning")
                                or str(thought)
                            )
                        else:
                            model_output = str(thought)

                    code_action = step.code_action
                    execution_result = step.observations if step.observations else None
                    is_error = bool(
                        execution_result and "error" in execution_result.lower()
                    )

                    current_step_widget = None

                    if model_output or code_action or execution_result:
                        # Create step widget with thought first
                        def add_thinking():
                            nonlocal current_step_widget
                            current_step_widget = chat_history.add_thinking(
                                step_number,
                                model_output or "",
                                "",
                                "",
                            )
                            self.screen.refresh()

                        self.call_later(add_thinking)

                        # Write code with syntax highlighting first (for proper highlighting)
                        if code_action:

                            def write_code(code=code_action):
                                if current_step_widget and code:
                                    current_step_widget.write_code(code)

                            self.call_later(write_code)

                        # Stream result line by line with 10ms delay
                        if execution_result:
                            result_lines = execution_result.split("\n")
                            for i, line in enumerate(result_lines):

                                def write_result_line(
                                    line=line, is_last=(i == len(result_lines) - 1)
                                ):
                                    if current_step_widget:
                                        if i == 0:
                                            current_step_widget.write_result_start(
                                                is_error
                                            )
                                        current_step_widget.write_line(line + "\n")
                                        if is_last:
                                            current_step_widget.collapse()

                                self.call_later(write_result_line)
                                await asyncio.sleep(0.01)
                        elif code_action:
                            # Collapse after code if no result
                            def collapse_after_code():
                                if current_step_widget:
                                    current_step_widget.collapse()

                            self.call_later(collapse_after_code)

                        # If no code or result, just collapse after thought
                        if not code_action and not execution_result:

                            def collapse_after_thought():
                                if current_step_widget:
                                    current_step_widget.collapse()

                            self.call_later(collapse_after_thought)

                        # Save step to database - works even if session not active
                        session = self.session_manager.get_current_session()
                        if session and session.id:
                            content = f"Step {step_number}"
                            if model_output:
                                content += f"\n{model_output}"
                            if code_action:
                                content += f"\nCode: {code_action}"
                            if execution_result:
                                content += f"\nResult: {execution_result}"
                            asyncio.create_task(
                                self._save_agent_step(session.id, content)
                            )

                elif hasattr(step, "is_final_answer") and step.is_final_answer:
                    # Use action_output if available (ActionStep), otherwise output (FinalAnswerStep)
                    answer_text = getattr(step, "action_output", None) or getattr(
                        step, "output", ""
                    )
                    session = self.session_manager.get_current_session()
                    if session and session.id:
                        answer_content = f"Final Answer:\n{answer_text}"
                        asyncio.create_task(
                            self._save_agent_step(session.id, answer_content)
                        )

                    # Update token counts after final answer
                    await self._update_token_counts()

                    def finish():
                        chat_history.add_agent_message(
                            "Final Answer:\n" + str(answer_text),
                            message_class="final-answer",
                        )
                        self.screen.refresh()

                    self.call_later(finish)
                    break

                # Update token counts after each step
                await self._update_token_counts()

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

        except Exception as exc:
            logger.exception(f"Error processing query: {query}")

            error_msg = str(exc)

            def show_error():
                chat_history.add_system_message(f"Error: {error_msg}")

            self.call_later(show_error)
        finally:
            # Log agent memory state after running
            logger.info("=== AGENT MEMORY AFTER RUN ===")
            logger.info(f"Memory steps count: {len(self.agent.memory.steps)}")
            for i, step in enumerate(self.agent.memory.steps):
                logger.info(f"  Step {i}: {type(step).__name__}")
            logger.info("===============================")

            # Save agent memory to DB
            session = self.session_manager.get_current_session()
            if session and session.id:
                import pickle

                try:
                    agent_steps = pickle.dumps(self.agent.memory.steps)
                    await self.session_manager.save_agent_steps(session.id, agent_steps)
                    logger.info(
                        f"Saved {len(self.agent.memory.steps)} steps to session {session.id}"
                    )
                except Exception as e:
                    logger.warning(f"Could not save agent steps: {e}")

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
        background: $background;
    }
    
    #main-container {
        height: 100%;
        dock: top;
    }
    
    #welcome-header {
        dock: top;
        height: auto;
        padding: 1 2;
        background: $background;
    }
    
    #chat-history {
        height: 100%;
        margin: 1 2;
        overflow-y: auto;
        scrollbar-gutter: stable;
        scrollbar-size-vertical: 1;
        scrollbar-background: $background;
        scrollbar-color: $primary;
    }
    
    #model-info {
        dock: bottom;
        height: auto;
        padding: 0 2;
        background: $surface;
        color: $text-muted;
    }
    
    #input-area {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: $background;
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
        background: $background;
        color: $text-muted;
    }
    
    #model-id, #provider, #input-tokens, #output-tokens {
        width: auto;
    }
    
    #model-id {
        color: $accent;
        padding-right: 1;
    }
    
    #provider {
        color: $text-muted;
        padding-right: 1;
    }
    
    #input-tokens {
        color: $success;
        padding-right: 1;
    }
    
    #output-tokens {
        color: $warning;
    }
    
    #spinner {
        width: 20;
        display: none;
    }
    
    #spinner.active {
        display: block;
    }
    
    #exit-hint {
        width: 1fr;
        text-align: right;
    }
    
    #query-input {
        width: 100%;
        min-height: 6;
        max-height: 12;
        background: $surface;
        border-left: thick $success;
        border-top: none;
        border-right: none;
        border-bottom: none;
        color: $text;
        padding: 1 2;
    }
    
    #send-btn {
        min-width: 4;
    }
    
    .pending-query {
        border-left: thick $success;
        border-top: none;
        border-right: none;
        border-bottom: none;
        padding: 1 2 1 2;
    }
    
    .user-msg {
        padding: 0 2;
        border-left: thick $success;
        color: $text-warning;
    }
    
    .agent-msg {
        padding: 0 2;
        border-left: solid $panel;
        color: $text;
    }
    
    .final-answer {
        padding: 0 2;
        border-left: thick $accent;
        color: $text;
    }
    
    .final-answer-label {
        color: $accent;
        text-style: bold;
    }
    
    .system-msg {
        padding: 0 2;
        color: $text-muted;
        text-style: italic;
    }
    
    .thinking-box {
        background: $surface;
        margin: 1 0;
    }
    
    .step-header {
        height: auto;
        padding: 0 1;
    }
    
    .step-title {
        color: $accent;
        text-style: bold;
        width: auto;
    }
    
    .expand-btn {
        min-width: 3;
    }
    
    .step-log-container {
        border: solid $panel;
        margin: 1 0;
    }
    """

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
        # Always create a new session on app startup
        await self.session_manager.create_session()
        self.agent = cora_agent()
        logger.info("Agent initialized successfully")

        session = self.session_manager.get_current_session()
        if session and session.id:
            self._current_session_id = session.id
            saved_steps = await self.session_manager.get_agent_steps(session.id)
            if saved_steps:
                import pickle

                try:
                    self.agent.memory.steps = pickle.loads(saved_steps)
                    logger.info(
                        f"Restored {len(self.agent.memory.steps)} steps from session {session.id}"
                    )
                except Exception as e:
                    logger.warning(f"Could not restore agent steps: {e}")

        self.push_screen(ChatScreen(self.session_manager, self.agent))

    async def on_shutdown(self) -> None:
        logger.info("Saving sessions before shutdown")
        if self.agent and self._current_session_id:
            import pickle

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
            import pickle

            try:
                agent_steps = pickle.dumps(self.agent.memory.steps)
                await self.session_manager.save_agent_steps(
                    self._current_session_id, agent_steps
                )
                logger.info(
                    f"Saved {len(self.agent.memory.steps)} steps when switching from session {self._current_session_id}"
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
                    logger.info(
                        f"Restored {len(self.agent.memory.steps)} steps for session {session_id}"
                    )
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
