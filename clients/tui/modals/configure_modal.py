import logging

import yaml
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from src.config import CONFIG_DIR, CONFIG_FILE, get_config

logger = logging.getLogger(__name__)


class ConfigureModal(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._config = get_config()

    def compose(self) -> ComposeResult:
        config_path = str(CONFIG_DIR / CONFIG_FILE)

        with Vertical(id="configure-form"):
            yield Static("Configure Settings", id="title")
            yield Static(f"Config file: {config_path}", id="config-path")

            with Horizontal(classes="form-row"):
                yield Static("AWS Profile:", classes="form-label")
                yield Input(
                    self._config.aws_profile or "",
                    id="aws-profile",
                    placeholder="notisphere",
                )

            with Horizontal(classes="form-row"):
                yield Static("LLM Provider:", classes="form-label")
                yield Input(
                    self._config.llm_provider,
                    id="llm-provider",
                    placeholder="openrouter",
                )

            with Horizontal(classes="form-row"):
                yield Static("LLM Model ID:", classes="form-label")
                yield Input(
                    self._config.llm_model_id,
                    id="llm-model-id",
                    placeholder="qwen/qwen3-coder",
                )

            with Horizontal(classes="form-row"):
                yield Static("LLM API Base:", classes="form-label")
                yield Input(
                    self._config.llm_api_base or "",
                    id="llm-api-base",
                    placeholder="https://...",
                )

            with Horizontal(classes="form-row"):
                yield Static("LLM API Key:", classes="form-label")
                yield Input(
                    self._config.llm_api_key or "",
                    id="llm-api-key",
                    placeholder="sk-...",
                )

            with Horizontal(classes="form-row"):
                yield Static("Langfuse Secret:", classes="form-label")
                yield Input(
                    self._config.langfuse_secret_key or "",
                    id="langfuse-secret",
                    placeholder="sk-...",
                )

            with Horizontal(classes="form-row"):
                yield Static("Langfuse Public:", classes="form-label")
                yield Input(
                    self._config.langfuse_public_key or "",
                    id="langfuse-public",
                    placeholder="pk-...",
                )

            with Horizontal(classes="form-row"):
                yield Static("Langfuse URL:", classes="form-label")
                yield Input(
                    self._config.langfuse_base_url or "",
                    id="langfuse-url",
                    placeholder="https://cloud.langfuse.com",
                )

            with Horizontal(id="button-row"):
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn", variant="default")

    def on_mount(self) -> None:
        aws_profile = self.query_one("#aws-profile", Input)
        aws_profile.focus()

    def action_cancel(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#save-btn")
    def _handle_save(self) -> None:
        aws_profile = self.query_one("#aws-profile", Input).value.strip()
        llm_provider = self.query_one("#llm-provider", Input).value.strip()
        llm_model_id = self.query_one("#llm-model-id", Input).value.strip()
        llm_api_base = self.query_one("#llm-api-base", Input).value.strip()
        llm_api_key = self.query_one("#llm-api-key", Input).value.strip()
        langfuse_secret = self.query_one("#langfuse-secret", Input).value.strip()
        langfuse_public = self.query_one("#langfuse-public", Input).value.strip()
        langfuse_url = self.query_one("#langfuse-url", Input).value.strip()

        config_data = {}

        if aws_profile:
            config_data["aws_profile"] = aws_profile

        if llm_provider or llm_model_id or llm_api_base or llm_api_key:
            config_data["llm"] = {}
            if llm_provider:
                config_data["llm"]["provider"] = llm_provider
            if llm_model_id:
                config_data["llm"]["model_id"] = llm_model_id
            if llm_api_base:
                config_data["llm"]["api_base"] = llm_api_base
            if llm_api_key:
                config_data["llm"]["api_key"] = llm_api_key

        if langfuse_secret or langfuse_public or langfuse_url:
            config_data["langfuse"] = {}
            if langfuse_secret:
                config_data["langfuse"]["secret_key"] = langfuse_secret
            if langfuse_public:
                config_data["langfuse"]["public_key"] = langfuse_public
            if langfuse_url:
                config_data["langfuse"]["base_url"] = langfuse_url

        config_path = CONFIG_DIR / CONFIG_FILE
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
            logger.info(f"Config saved to {config_path}")
        except Exception as e:
            logger.exception(f"Failed to save config: {e}")

        self.app.pop_screen()

    @on(Button.Pressed, "#cancel-btn")
    def _handle_cancel(self) -> None:
        self.action_cancel()
