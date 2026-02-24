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
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Input,
    LoadingIndicator,
    Markdown as TextualMarkdown,
    Static,
)

from clients.tui.step_tabs import StepsTabbedContent
from src.agents import cora_agent
from src.config import get_config
from src.session import SessionManager, MessageRole
from src.themes import BUILT_IN_THEMES

CORPUS_ASCII = Text(figlet_format("CORA", font="slant"), style="bold green")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

        # Mount to self (ChatHistoryPanel) first
        self.mount(query_section)

        # Now mount children to the mounted query_section
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

    def add_system_message(self, message: str):
        """Add a system message to the chat history."""
        widget = Static(f"\n[System] {message}", classes="system-msg")
        self.mount(widget)
        return widget

    def clear_pending_border(self):
        """No-op for compatibility."""
        pass


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
        self._current_tab_id: str | None = None
        self._planning_tab_ids: list[str] = []
        self._action_tab_ids: list[str] = []
        self._query_count = 0
        self._current_steps_tabs = None
        self._current_final_container = None

    def _scroll_to_bottom(self, widget) -> None:
        """Scroll a widget to its bottom."""
        try:
            widget.scroll_end()
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Compose the layout."""
        with Vertical(id="main-container"):
            with Container(id="welcome-header"):
                yield Static(Align.center(CORPUS_ASCII), id="ascii-header")
                yield Static(
                    "[dim]Press Enter to send. Ctrl+C to quit.[/dim]", id="help-text"
                )

            with VerticalScroll(id="scrollable-content"):
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

            # Load cumulative token counts from all agent runs for this session
            cumulative = await self.session_manager.get_session_cumulative_tokens(
                session.id
            )

            def update_tokens():
                try:
                    input_widget = self.query_one("#input-tokens", Static)
                    output_widget = self.query_one("#output-tokens", Static)
                    input_widget.update(f"In: {cumulative.get('input_tokens', 0)}")
                    output_widget.update(f"Out: {cumulative.get('output_tokens', 0)}")
                except Exception:
                    pass

            self.call_later(update_tokens)
            logger.info(
                f"Loaded cumulative tokens: in={cumulative.get('input_tokens', 0)}, out={cumulative.get('output_tokens', 0)}"
            )

        # Clear chat history
        chat_history = self.query_one("#chat-history", ChatHistoryPanel)
        chat_history.remove_children()

        # Reconstruct chat history from session messages
        if session and session.messages:
            logger.info(
                f"Reconstructing chat history with {len(session.messages)} messages"
            )
            self._query_count = 0
            self._current_steps_tabs = None
            self._current_final_container = None

            user_messages = [m for m in session.messages if m.role == MessageRole.USER]
            has_user_messages = bool(user_messages)

            if has_user_messages:
                for msg in session.messages:
                    if msg.role == MessageRole.USER:
                        self._query_count += 1
                        query_section, steps_tabs, final_container = (
                            chat_history.add_query_section(
                                msg.content, self._query_count
                            )
                        )
                        self._current_steps_tabs = steps_tabs
                        self._current_final_container = final_container
                    elif msg.role == MessageRole.AGENT:
                        self._process_agent_message_for_reconstruction(
                            msg.content, chat_history
                        )
            else:
                logger.warning(
                    f"No USER messages found in session {session.id}, "
                    "attempting to reconstruct from agent messages only"
                )
                for msg in session.messages:
                    if msg.role == MessageRole.AGENT:
                        content = msg.content
                        if content.startswith("Final Answer:"):
                            self._query_count += 1
                            query_section, steps_tabs, final_container = (
                                chat_history.add_query_section(
                                    f"[Restored Query {self._query_count}]",
                                    self._query_count,
                                )
                            )
                            self._current_steps_tabs = steps_tabs
                            self._current_final_container = final_container
                            self._process_agent_message_for_reconstruction(
                                content, chat_history
                            )

            if session.messages:
                self.show_welcome = False
                header = self.query_one("#welcome-header")
                header.display = False
            logger.info(f"Reconstructed {self._query_count} query sections")
        else:
            # Keep show_welcome = True so welcome is shown on load
            # It will be set to False when first query is sent
            logger.debug("Started fresh session")

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

    def _process_agent_message_for_reconstruction(
        self, content: str, chat_history: ChatHistoryPanel
    ) -> None:
        """Process an agent message for chat history reconstruction."""
        if content.startswith("Final Answer:"):
            answer_text = content.replace("Final Answer:", "", 1).lstrip("\n")
            if self._current_final_container:
                final_answer_md = TextualMarkdown(
                    answer_text,
                    id=f"final-answer-markdown-{self._query_count}",
                )
                self._current_final_container.update("")
                self._current_final_container.mount(final_answer_md)
                self._current_final_container.add_class("visible")
        elif content.startswith("Plan "):
            if self._current_steps_tabs:
                try:
                    lines = content.split("\n", 1)
                    plan_content = lines[1] if len(lines) > 1 else ""
                    self._current_steps_tabs.add_planning_tab(plan_content)
                except Exception as e:
                    logger.warning(f"Could not parse plan step: {e}")
        elif content.startswith("Step "):
            if self._current_steps_tabs:
                try:
                    lines = content.split("\n")
                    step_line = lines[0]
                    step_num = int(step_line.replace("Step ", ""))

                    thought = ""
                    code = ""
                    observations = ""

                    for line in lines[1:]:
                        if line.startswith("Code:"):
                            code = line.replace("Code:", "").strip()
                        elif line.startswith("Result:"):
                            observations = line.replace("Result:", "").strip()
                        elif line and not thought:
                            thought = line

                    tab_id = self._current_steps_tabs.add_action_tab(step_num)
                    self._action_tab_ids.append(tab_id)
                    self._current_steps_tabs.update_action_tab(
                        tab_id,
                        thought=thought,
                        code=code,
                        observations=observations,
                    )
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse agent step: {e}")

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

        # Query will be displayed in query section created by _run_agent

        # Save user message to database
        logger.info(f"_process_query: about to save user message, query='{query}'")
        session = self.session_manager.get_current_session()
        logger.info(
            f"_process_query: session={session}, session.id={session.id if session else None}"
        )
        if session and session.id:
            logger.info(
                f"_process_query: calling asyncio.create_task for _add_user_message"
            )
            import asyncio

            asyncio.create_task(self._add_user_message(session.id, query))

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
            # Send unrecognized commands to agent - will create query section in _run_agent
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
        logger.info(
            f"Saving USER message: session_id={session_id}, content={content[:50]}..."
        )
        try:
            await self.session_manager.add_message(
                MessageRole.USER, content, session_id
            )
            logger.info(f"USER message saved successfully to session {session_id}")
        except Exception as e:
            logger.exception(f"Failed to save USER message: {e}")

    async def _add_agent_message(self, session_id: int, content: str) -> None:
        await self.session_manager.add_message(MessageRole.AGENT, content, session_id)

    async def _save_agent_step(self, session_id: int, content: str) -> None:
        """Save agent step to database - works even if session not active."""
        try:
            await self.app.session_manager.add_message(
                MessageRole.AGENT, content, session_id
            )
            logger.debug(f"Saved agent step to session {session_id}")
        except Exception as e:
            logger.warning(f"Could not save agent step: {e}")

    async def _update_token_counts(self, save_to_db: bool = False) -> None:
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

            if save_to_db:
                session = self.session_manager.get_current_session()
                if session and session.id:
                    asyncio.create_task(
                        self.session_manager.save_agent_run_metrics(
                            session.id,
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

        self._query_count += 1
        current_query_num = self._query_count

        self._planning_tab_ids = []
        self._action_tab_ids = []

        # Create query section using ChatHistoryPanel's method
        query_section, steps_tabs, final_container = chat_history.add_query_section(
            query, current_query_num
        )

        # Store references for use in callbacks
        self._current_steps_tabs = steps_tabs
        self._current_final_container = final_container

        # Scroll to show the new query
        self.call_later(lambda: self._scroll_to_bottom(chat_history))

        logger.info("=== AGENT MEMORY BEFORE RUN ===")
        logger.info(f"Memory steps count: {len(self.agent.memory.steps)}")
        for i, step in enumerate(self.agent.memory.steps):
            logger.info(f"  Step {i}: {type(step).__name__}")
        logger.info("===============================")

        try:
            import time

            logger.info(f"Starting agent run with query: {query}")
            start_time = time.time()

            def stream_agent():
                """Run agent in thread and yield steps."""
                logger.info("stream_agent: starting agent.run()")
                try:
                    result = self.agent.run(query, stream=True, reset=False)
                    logger.info(f"stream_agent: agent.run() returned: {type(result)}")
                    return result
                except Exception as e:
                    logger.exception(f"stream_agent: agent.run() raised: {e}")
                    raise

            loop = asyncio.get_event_loop()
            logger.info(f"self.app.executor: {self.app.executor}")
            stream_gen = await loop.run_in_executor(self.app.executor, stream_agent)
            logger.info("stream_gen created successfully")

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

                    def add_planning():
                        try:
                            logger.debug(
                                f"add_planning called, _current_steps_tabs={self._current_steps_tabs}"
                            )
                            if self._current_steps_tabs:
                                tab_id = self._current_steps_tabs.add_planning_tab(
                                    plan_text
                                )
                                self._planning_tab_ids.append(tab_id)
                                self._current_tab_id = tab_id
                                self.screen.refresh()
                            else:
                                logger.warning(
                                    "add_planning: _current_steps_tabs is None!"
                                )
                        except Exception as e:
                            logger.exception(f"Error in add_planning: {e}")

                    self.call_later(add_planning)

                    # Save planning step to database
                    session = self.session_manager.get_current_session()
                    if session and session.id:
                        content = f"Plan {len(self._planning_tab_ids)}\n{plan_text}"
                        asyncio.create_task(self._save_agent_step(session.id, content))

                    continue

                elif isinstance(step, ActionStep):
                    step_number = step.step_number

                    model_output = None
                    if step.model_output:
                        thought = step.model_output
                        model_output = None
                        if isinstance(thought, list):
                            texts = []
                            for item in thought:
                                if (
                                    isinstance(item, dict)
                                    and item.get("type") == "text"
                                ):
                                    texts.append(item.get("text", ""))
                            model_output = "\n".join(texts) if texts else str(thought)
                        elif isinstance(thought, str):
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
                                pass
                            model_output = thought
                        elif isinstance(thought, dict):
                            model_output = (
                                thought.get("thought")
                                or thought.get("text")
                                or thought.get("reasoning")
                                or str(thought)
                            )
                        else:
                            model_output = str(thought) if thought else None

                    code_action = step.code_action
                    execution_result = step.observations if step.observations else None

                    if model_output or code_action or execution_result:

                        def add_action_step():
                            try:
                                if self._current_steps_tabs:
                                    tab_id = self._current_steps_tabs.add_action_tab(
                                        step_number
                                    )
                                    self._action_tab_ids.append(tab_id)
                                    self._current_tab_id = tab_id
                                    self._current_steps_tabs.update_action_tab(
                                        tab_id,
                                        thought=model_output or "",
                                        code=code_action or "",
                                        observations=execution_result or "",
                                    )
                                    self.screen.refresh()
                                else:
                                    logger.warning(
                                        "add_action_step: _current_steps_tabs is None!"
                                    )
                            except Exception as e:
                                logger.exception(f"Error in add_action_step: {e}")

                        self.call_later(add_action_step)

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
                    answer_text = getattr(step, "action_output", None) or getattr(
                        step, "output", ""
                    )
                    session = self.session_manager.get_current_session()
                    if session and session.id:
                        answer_content = f"Final Answer:\n{answer_text}"
                        asyncio.create_task(
                            self._save_agent_step(session.id, answer_content)
                        )

                    await self._update_token_counts(save_to_db=True)

                    def finish():
                        final_answer_md = TextualMarkdown(
                            answer_text,
                            id=f"final-answer-markdown-{current_query_num}",
                        )
                        self._current_final_container.update("")
                        self._current_final_container.mount(final_answer_md)
                        self._current_final_container.add_class("visible")
                        self.screen.refresh()

                    self.call_later(finish)
                    break

                await self._update_token_counts(save_to_db=False)

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
    
    #scrollable-content {
        height: 100%;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    
    #chat-history {
        height: auto;
        max-height: 100%;
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
    
    .query-section {
        height: auto;
        min-height: 35vh;
        padding: 1;
        background: $surface;
        border: solid $panel;
    }
    
    .query-section .query-text {
        color: $accent;
        text-style: bold;
        padding: 1;
    }
    
    .query-section .final-answer-section {
        padding: 1;
        margin-top: 1;
        border-left: thick $accent;
    }
    
    StepsTabbedContent {
        height: 35vh;
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
