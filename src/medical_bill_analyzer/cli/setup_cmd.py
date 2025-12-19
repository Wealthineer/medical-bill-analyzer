"""Setup command - Interactive wizard for first-run configuration."""

import os
from decimal import Decimal
from pathlib import Path

import typer

from medical_bill_analyzer.config.defaults import DEFAULT_CONFIG, get_user_config_dir
from medical_bill_analyzer.config.settings import Settings, get_config_path
from medical_bill_analyzer.database.connection import DatabaseConnection
from medical_bill_analyzer.database.migrations.migration_manager import MigrationManager
from medical_bill_analyzer.llm.factory import create_llm_provider, list_available_providers
from medical_bill_analyzer.utils.logger import get_logger

from .utils import error_message, info_message, success_message, warning_message

logger = get_logger(__name__)


def setup():
    """Interactive setup wizard for first-run configuration."""
    typer.echo("\n" + "=" * 60)
    typer.secho("  Medical Bill Analyzer - Setup Wizard", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 60 + "\n")

    info_message("This wizard will help you configure the application\n")

    # Show privacy notice
    _show_privacy_notice()

    # Check if config already exists
    config_path = get_config_path()
    if config_path.exists():
        warning_message(f"Configuration already exists at: {config_path}")
        if not typer.confirm("\nDo you want to reconfigure?", default=False):
            typer.echo("\nSetup cancelled.")
            raise typer.Exit()
        typer.echo()

    # Step 1: Select LLM provider
    provider_name = _select_llm_provider()

    # Step 2: Get API key (if needed)
    api_key = _setup_api_key(provider_name)

    # Step 3: Test connection
    if not _test_llm_connection(provider_name, api_key):
        error_message("Setup failed: Could not connect to LLM provider")
        raise typer.Exit(code=1)

    # Step 4: Set bonus threshold
    bonus_threshold = _set_bonus_threshold()

    # Step 5: Initialize database
    db_path = _initialize_database()

    # Step 6: Save credential to database
    _save_credential(db_path, provider_name, api_key)

    # Step 7: Save configuration
    _save_configuration(provider_name, bonus_threshold)

    # Success!
    typer.echo("\n" + "=" * 60)
    success_message("Setup completed successfully!")
    typer.echo("=" * 60 + "\n")

    info_message("Next steps:")
    typer.echo("  1. Add bills: medical-bill-analyzer add /path/to/bill.pdf")
    typer.echo("  2. List bills: medical-bill-analyzer list")
    typer.echo("  3. Check bonus: medical-bill-analyzer bonus-check\n")


def _show_privacy_notice():
    """Show privacy and data handling notice."""
    typer.secho("Privacy & Data Handling:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  • All PDFs and data are stored locally on your machine")
    typer.echo("  • Only extracted TEXT is sent to the LLM API (not PDF files)")
    typer.echo("  • For complete privacy, use Ollama (local processing)")
    typer.echo()


def _select_llm_provider() -> str:
    """Prompt user to select LLM provider.

    Returns:
        Provider name (anthropic, openai, or ollama)
    """
    typer.secho("Step 1: Select LLM Provider", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    available = list_available_providers()
    provider_choices = {
        "1": ("anthropic", "Anthropic Claude (Recommended) - Most accurate"),
        "2": ("openai", "OpenAI GPT - Good alternative"),
        "3": ("ollama", "Ollama - Local, completely private"),
    }

    typer.echo("Available providers:")
    for key, (name, description) in provider_choices.items():
        available_mark = "✓" if name in available else "✗"
        typer.echo(f"  {key}. [{available_mark}] {description}")
    typer.echo()

    while True:
        choice = typer.prompt("Select provider", type=str, default="1")
        if choice in provider_choices:
            provider_name, _ = provider_choices[choice]
            if provider_name in available:
                success_message(f"Selected: {provider_name}")
                typer.echo()
                return provider_name
            else:
                error_message(f"{provider_name} is not available. Install required packages.")
        else:
            error_message("Invalid choice. Please enter 1, 2, or 3")


def _setup_api_key(provider_name: str) -> Optional[str]:
    """Setup API key for provider.

    Args:
        provider_name: Name of provider

    Returns:
        API key value (None for ollama which runs locally)
    """
    typer.secho("Step 2: API Key Configuration", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    # Ollama runs locally, no API key needed
    if provider_name == "ollama":
        info_message("Ollama runs locally - no API key needed")
        typer.echo()
        return None

    # Prompt user to enter API key
    typer.echo(f"Enter your {provider_name.title()} API key:")
    if provider_name == "anthropic":
        typer.echo("(Get your key from: https://console.anthropic.com)")
    elif provider_name == "openai":
        typer.echo("(Get your key from: https://platform.openai.com)")
    typer.echo()

    api_key = typer.prompt(
        "API Key",
        hide_input=True,
        confirmation_prompt=False,
    ).strip()

    if not api_key:
        error_message("API key cannot be empty")
        raise typer.Exit(code=1)

    success_message("API key received - will be saved to database")
    typer.echo()
    return api_key


def _test_llm_connection(provider_name: str, api_key: Optional[str]) -> bool:
    """Test LLM provider connection.

    Args:
        provider_name: Name of provider
        api_key: API key (None for ollama)

    Returns:
        True if successful, False otherwise
    """
    typer.secho("Step 3: Testing Connection", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    # Build provider config
    default_llm_config = DEFAULT_CONFIG["llm"]

    if provider_name == "anthropic":
        config = {
            "model": default_llm_config["anthropic"]["model"],
            "api_key": api_key,
            "max_tokens": default_llm_config["anthropic"]["max_tokens"],
            "temperature": default_llm_config["anthropic"]["temperature"],
        }
    elif provider_name == "openai":
        config = {
            "model": default_llm_config["openai"]["model"],
            "api_key": api_key,
            "max_tokens": default_llm_config["openai"]["max_tokens"],
            "temperature": default_llm_config["openai"]["temperature"],
        }
    else:  # ollama
        config = {
            "model": default_llm_config["ollama"]["model"],
            "base_url": default_llm_config["ollama"]["base_url"],
            "timeout": default_llm_config["ollama"]["timeout"],
        }

    with typer.progressbar(length=1, label="Testing LLM connection") as progress:
        try:
            provider = create_llm_provider(provider_name, config)
            result = provider.test_connection()

            if result["success"]:
                progress.update(1)
                typer.echo()
                success_message(f"Connected successfully: {result['message']}")
                typer.echo()
                return True
            else:
                progress.update(1)
                typer.echo()
                error_message(f"Connection failed: {result['message']}")
                typer.echo()
                return False

        except Exception as e:
            progress.update(1)
            typer.echo()
            error_message(f"Connection failed: {e}")
            typer.echo()
            return False


def _set_bonus_threshold() -> Decimal:
    """Prompt for bonus threshold.

    Returns:
        Bonus threshold amount
    """
    typer.secho("Step 4: Bonus Threshold", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    typer.echo("Enter your annual PKV bonus amount (in EUR):")
    typer.echo("  This is the amount you'll lose if you submit claims")
    typer.echo()

    while True:
        threshold_str = typer.prompt("Bonus threshold", default="1000")
        try:
            threshold = Decimal(threshold_str)
            if threshold < 0:
                error_message("Threshold must be positive")
                continue
            success_message(f"Set bonus threshold: €{threshold}")
            typer.echo()
            return threshold
        except Exception:
            error_message("Invalid number format")


def _initialize_database() -> Path:
    """Initialize database with migrations.

    Returns:
        Database path
    """
    typer.secho("Step 5: Initializing Database", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    # Get database path from default config
    db_path = Path(DEFAULT_CONFIG["storage"]["database_path"]).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with typer.progressbar(length=1, label="Creating database") as progress:
        try:
            # Create connection and run migrations (including v2 for credentials)
            db = DatabaseConnection(db_path)
            manager = MigrationManager(db)
            manager.run_migrations()

            progress.update(1)
            typer.echo()
            success_message(f"Database initialized: {db_path}")
            typer.echo()
            return db_path

        except Exception as e:
            progress.update(1)
            typer.echo()
            error_message(f"Database initialization failed: {e}")
            raise typer.Exit(code=1)


def _save_credential(db_path: Path, provider_name: str, api_key: Optional[str]):
    """Save credential to database.

    Args:
        db_path: Path to database
        provider_name: Provider name
        api_key: API key (None for ollama)
    """
    typer.secho("Step 6: Saving Credentials", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    with typer.progressbar(length=1, label="Saving credentials to database") as progress:
        try:
            from medical_bill_analyzer.database.repositories import CredentialRepository

            credential_repo = CredentialRepository(db_path)
            credential_repo.save_credential(provider_name, api_key)

            progress.update(1)
            typer.echo()
            success_message(f"Credentials saved securely to database")
            typer.echo()

        except Exception as e:
            progress.update(1)
            typer.echo()
            error_message(f"Failed to save credentials: {e}")
            raise typer.Exit(code=1)


def _save_configuration(provider_name: str, bonus_threshold: Decimal):
    """Save configuration to file.

    Args:
        provider_name: Provider name
        bonus_threshold: Bonus threshold
    """
    typer.secho("Step 7: Saving Configuration", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Build full config from defaults
    full_config = {
        "llm": {
            "provider": provider_name,
            **DEFAULT_CONFIG["llm"],  # Includes all provider configs
        },
        "storage": DEFAULT_CONFIG["storage"],
        "bonus": {
            "default_threshold": float(bonus_threshold),
        },
    }

    # Save to file
    with typer.progressbar(length=1, label="Saving configuration") as progress:
        settings = Settings(**full_config)
        settings.to_yaml(config_path)
        progress.update(1)
        typer.echo()
        success_message(f"Configuration saved: {config_path}")
        typer.echo()
