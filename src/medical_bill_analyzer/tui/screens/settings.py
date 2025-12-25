"""Settings screen for Medical Bill Analyzer TUI."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static

from medical_bill_analyzer.cli.utils import get_credential_repository, load_config
from medical_bill_analyzer.config.settings import save_settings
from medical_bill_analyzer.llm.factory import create_llm_provider


class SettingsScreen(Screen):
    """Settings screen for configuring LLM providers and app settings.

    Allows users to:
    - Switch between LLM providers (Anthropic, OpenAI, Ollama, LM Studio)
    - Configure API keys (for cloud providers)
    - Configure endpoints (for local providers)
    - Set model parameters
    - Set bonus threshold
    - Test connection
    - Save settings
    """

    CSS = """
    SettingsScreen {
        background: $surface;
    }

    #settings-container {
        height: 100%;
        padding: 1 2;
        overflow-y: auto;
    }

    .settings-section {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    Label {
        padding: 1 0 0 0;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    Select {
        width: 100%;
        margin-bottom: 1;
    }

    Vertical {
        height: auto;
        margin-bottom: 1;
    }

    #button-container {
        height: auto;
        padding: 1 0;
    }

    Button {
        margin: 0 1;
    }

    #status {
        padding: 1 0;
        min-height: 3;
    }

    #help-text {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    .help-note {
        color: $text-muted;
        padding: 0 0 1 0;
        text-style: italic;
    }

    .hidden {
        display: none;
    }
    """

    def __init__(self):
        """Initialize settings screen."""
        super().__init__()
        self.current_settings = None
        self.current_provider = "anthropic"

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            # Provider Selection
            Container(
                Static("LLM Provider", classes="section-title"),
                Label("Provider:"),
                Select(
                    [
                        ("Anthropic Claude", "anthropic"),
                        ("OpenAI GPT", "openai"),
                        ("LM Studio (local)", "lmstudio"),
                        ("Ollama (local)", "ollama"),
                    ],
                    id="provider-select",
                    value="anthropic",
                ),
                classes="settings-section",
            ),
            # Provider-specific Configuration
            Container(
                Static("Provider Configuration", classes="section-title"),
                # API Key field (for cloud providers only)
                Vertical(
                    Label("API Key:"),
                    Input(
                        placeholder="Enter your API key",
                        password=True,
                        id="api-key-input",
                    ),
                    id="api-key-row",
                ),
                # Base URL field (for local providers only)
                Vertical(
                    Label("Base URL:"),
                    Input(
                        placeholder="http://localhost:1234",
                        id="base-url-input",
                    ),
                    Static(
                        "Just paste the URL shown in LM Studio",
                        classes="help-note",
                        id="base-url-help",
                    ),
                    id="base-url-row",
                    classes="hidden",
                ),
                # Model name (all providers)
                Label("Model:"),
                Input(
                    placeholder="Model name",
                    id="model-input",
                ),
                classes="settings-section",
            ),
            # Bonus Settings
            Container(
                Static("App Settings", classes="section-title"),
                Label("Bonus Threshold (EUR):"),
                Input(
                    placeholder="1000",
                    id="bonus-input",
                ),
                classes="settings-section",
            ),
            # Buttons
            Horizontal(
                Button("Test Connection", id="test-btn", variant="primary"),
                Button("Save Settings", id="save-btn", variant="success"),
                Button("Cancel", id="cancel-btn", variant="default"),
                id="button-container",
            ),
            Static(id="status"),
            Static(
                "Press Esc to go back without saving",
                id="help-text",
            ),
            id="settings-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load current settings when screen is displayed."""
        self._load_current_settings()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle provider selection changes."""
        if event.select.id == "provider-select":
            self.current_provider = str(event.value)
            self._update_form_for_provider()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "cancel-btn":
            self.app.pop_screen()
        elif event.button.id == "save-btn":
            self._save_settings()
        elif event.button.id == "test-btn":
            self._test_connection()

    def _load_current_settings(self) -> None:
        """Load current settings from config and database."""
        try:
            settings = load_config()
            self.current_settings = settings

            # Set provider select
            provider_select = self.query_one("#provider-select", Select)
            if settings.llm.provider == "openai" and settings.llm.openai.base_url:
                provider_select.value = "lmstudio"
                self.current_provider = "lmstudio"
            else:
                provider_select.value = settings.llm.provider
                self.current_provider = settings.llm.provider

            # Load provider-specific settings
            self._update_form_for_provider()

            # Load bonus threshold (format as integer if whole number)
            bonus_input = self.query_one("#bonus-input", Input)
            threshold = settings.bonus.default_threshold
            # Display as integer if it's a whole number
            if threshold == int(threshold):
                bonus_input.value = str(int(threshold))
            else:
                bonus_input.value = str(threshold)

            # Load API key from database (if applicable)
            if self.current_provider in ["anthropic", "openai", "lmstudio"]:
                credential_repo = get_credential_repository(settings)
                key_provider = "openai" if self.current_provider == "lmstudio" else self.current_provider
                api_key = credential_repo.get_credential(key_provider)
                if api_key:
                    api_key_input = self.query_one("#api-key-input", Input)
                    api_key_input.value = api_key

        except Exception as e:
            status = self.query_one("#status", Static)
            status.update(f"Error loading settings: {e}")

    def _update_form_for_provider(self) -> None:
        """Update form fields based on selected provider."""
        model_input = self.query_one("#model-input", Input)
        base_url_input = self.query_one("#base-url-input", Input)
        api_key_input = self.query_one("#api-key-input", Input)

        # Get container rows
        api_key_row = self.query_one("#api-key-row")
        base_url_row = self.query_one("#base-url-row")

        if self.current_provider == "anthropic":
            # Show: API Key, Model
            api_key_row.remove_class("hidden")
            base_url_row.add_class("hidden")

            model_input.placeholder = "e.g., claude-sonnet-4-20250514"
            if self.current_settings:
                model_input.value = self.current_settings.llm.anthropic.model
            api_key_input.placeholder = "Enter Anthropic API key"

        elif self.current_provider == "openai":
            # Show: API Key, Model
            api_key_row.remove_class("hidden")
            base_url_row.add_class("hidden")

            model_input.placeholder = "e.g., gpt-4o-mini"
            if self.current_settings:
                model_input.value = self.current_settings.llm.openai.model
            api_key_input.placeholder = "Enter OpenAI API key"

        elif self.current_provider == "lmstudio":
            # Show: Base URL, Model (API key hidden)
            api_key_row.add_class("hidden")
            base_url_row.remove_class("hidden")

            # Update help text for LM Studio
            base_url_help = base_url_row.query_one(".help-note", Static)
            base_url_help.update("Just paste the URL shown in LM Studio (e.g., http://127.0.0.1:1234)")

            model_input.placeholder = "e.g., openai/gpt-oss-20b"
            if self.current_settings:
                model_input.value = self.current_settings.llm.openai.model
                if self.current_settings.llm.openai.base_url:
                    # Remove /v1 suffix when displaying (user sees what they entered)
                    display_url = self.current_settings.llm.openai.base_url.rstrip("/v1")
                    base_url_input.value = display_url
                else:
                    base_url_input.value = "http://localhost:1234"
            else:
                base_url_input.value = "http://localhost:1234"

        elif self.current_provider == "ollama":
            # Show: Base URL, Model (no API key)
            api_key_row.add_class("hidden")
            base_url_row.remove_class("hidden")

            # Update help text for Ollama
            base_url_help = base_url_row.query_one(".help-note", Static)
            base_url_help.update("Ollama default: http://localhost:11434")

            model_input.placeholder = "e.g., llama3.1:8b"
            if self.current_settings:
                model_input.value = self.current_settings.llm.ollama.model
                base_url_input.value = self.current_settings.llm.ollama.base_url
            else:
                base_url_input.value = "http://localhost:11434"

    def _save_settings(self) -> None:
        """Save settings to config file and database."""
        try:
            # Get form values
            model = self.query_one("#model-input", Input).value
            api_key = self.query_one("#api-key-input", Input).value
            base_url = self.query_one("#base-url-input", Input).value
            bonus_threshold = self.query_one("#bonus-input", Input).value

            # Validate
            if not model:
                self.app.notify("Model name is required", severity="error", timeout=3)
                return

            if self.current_provider in ["anthropic", "openai"] and not api_key:
                self.app.notify("API key is required for cloud providers", severity="error", timeout=3)
                return

            if self.current_provider in ["lmstudio", "ollama"] and not base_url:
                self.app.notify("Base URL is required for local providers", severity="error", timeout=3)
                return

            # Load current config
            settings = load_config()

            # Update provider settings
            if self.current_provider == "lmstudio":
                settings.llm.provider = "openai"
                settings.llm.openai.model = model
                # Automatically append /v1 for LM Studio if not present
                if not base_url.endswith("/v1"):
                    base_url = base_url.rstrip("/") + "/v1"
                settings.llm.openai.base_url = base_url
            elif self.current_provider == "anthropic":
                settings.llm.provider = "anthropic"
                settings.llm.anthropic.model = model
            elif self.current_provider == "openai":
                settings.llm.provider = "openai"
                settings.llm.openai.model = model
                settings.llm.openai.base_url = None
            elif self.current_provider == "ollama":
                settings.llm.provider = "ollama"
                settings.llm.ollama.model = model
                settings.llm.ollama.base_url = base_url

            # Update bonus threshold
            if bonus_threshold:
                settings.bonus.default_threshold = int(bonus_threshold)

            # Save config to database
            save_settings(settings)

            # Save API key to database (for cloud providers)
            if self.current_provider in ["anthropic", "openai"]:
                if api_key:
                    credential_repo = get_credential_repository(settings)
                    credential_repo.save_credential(self.current_provider, api_key)
            elif self.current_provider == "lmstudio":
                # LM Studio needs a dummy API key
                credential_repo = get_credential_repository(settings)
                credential_repo.save_credential("openai", "lm-studio")

            self.app.notify("Settings saved successfully!", severity="information", timeout=3)

            status = self.query_one("#status", Static)
            status.update("✓ Settings saved! Changes will take effect for new operations.")

        except Exception as e:
            self.app.notify(f"Failed to save settings: {e}", severity="error", timeout=5)
            status = self.query_one("#status", Static)
            status.update(f"Error: {e}")

    def _test_connection(self) -> None:
        """Test connection to LLM provider."""
        try:
            # Get form values
            model = self.query_one("#model-input", Input).value
            api_key = self.query_one("#api-key-input", Input).value
            base_url = self.query_one("#base-url-input", Input).value

            if not model:
                self.app.notify("Please enter a model name", severity="warning", timeout=3)
                return

            if self.current_provider in ["anthropic", "openai"] and not api_key:
                self.app.notify("Please enter an API key", severity="warning", timeout=3)
                return

            if self.current_provider in ["lmstudio", "ollama"] and not base_url:
                self.app.notify("Please enter a base URL", severity="warning", timeout=3)
                return

            status = self.query_one("#status", Static)
            status.update("Testing connection...")

            # Build config for provider
            if self.current_provider == "anthropic":
                config = {
                    "model": model,
                    "api_key": api_key,
                    "max_tokens": 100,
                    "temperature": 0,
                }
                provider_name = "anthropic"
            elif self.current_provider == "openai":
                config = {
                    "model": model,
                    "api_key": api_key,
                    "max_tokens": 100,
                    "temperature": 0,
                }
                provider_name = "openai"
            elif self.current_provider == "lmstudio":
                # Automatically append /v1 for LM Studio if not present
                test_url = base_url
                if not test_url.endswith("/v1"):
                    test_url = test_url.rstrip("/") + "/v1"

                config = {
                    "model": model,
                    "api_key": "lm-studio",  # Dummy key for local endpoint
                    "base_url": test_url,
                    "max_tokens": 100,
                    "temperature": 0,
                }
                provider_name = "openai"
            elif self.current_provider == "ollama":
                config = {
                    "model": model,
                    "base_url": base_url,
                    "timeout": 60,
                }
                provider_name = "ollama"

            # Create provider and test
            provider = create_llm_provider(provider_name, config)
            result = provider.test_connection()

            if result:
                status.update("✓ Connection successful!")
                self.app.notify("Connection test passed!", severity="information", timeout=3)
            else:
                status.update("✗ Connection failed - check your settings")
                self.app.notify("Connection test failed", severity="error", timeout=3)

        except Exception as e:
            status = self.query_one("#status", Static)
            status.update(f"✗ Connection failed: {e}")
            self.app.notify(f"Connection error: {e}", severity="error", timeout=5)
