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
    api_key_env = _setup_api_key(provider_name)

    # Step 3: Test connection
    config = _create_test_config(provider_name, api_key_env)
    if not _test_llm_connection(provider_name, config):
        error_message("Setup failed: Could not connect to LLM provider")
        raise typer.Exit(code=1)

    # Step 4: Set bonus threshold
    bonus_threshold = _set_bonus_threshold()

    # Step 5: Initialize database
    db_path = _initialize_database(config)

    # Step 6: Create config file
    _save_configuration(config, provider_name, api_key_env, bonus_threshold)

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


def _save_api_key_to_env(env_file: Path, key_name: str, key_value: str):
    """Save or update API key in .env file.

    Args:
        env_file: Path to .env file
        key_name: Environment variable name (e.g., "ANTHROPIC_API_KEY")
        key_value: API key value
    """
    # Read existing .env file if it exists
    existing_lines = []
    key_exists = False

    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                # Update existing key or keep other lines
                if line.strip().startswith(f"{key_name}="):
                    existing_lines.append(f'{key_name}="{key_value}"\n')
                    key_exists = True
                else:
                    existing_lines.append(line)

    # If key doesn't exist, add it
    if not key_exists:
        existing_lines.append(f'{key_name}="{key_value}"\n')

    # Write back to .env file
    with open(env_file, "w") as f:
        f.writelines(existing_lines)


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


def _setup_api_key(provider_name: str) -> str:
    """Setup API key for provider.

    Args:
        provider_name: Name of provider

    Returns:
        Environment variable name for API key
    """
    typer.secho("Step 2: API Key Configuration", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    env_var_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "ollama": None,
    }

    api_key_env = env_var_map.get(provider_name)

    if api_key_env is None:
        info_message("Ollama runs locally - no API key needed")
        typer.echo()
        return ""

    # Check if already set
    existing_key = os.getenv(api_key_env)
    if existing_key:
        success_message(f"API key found in environment: {api_key_env}")
        typer.echo()
        return api_key_env

    # Prompt user to enter API key
    typer.echo(f"Enter your {provider_name.title()} API key:")
    typer.echo(f"(Get your key from: https://console.{provider_name}.com)")
    typer.echo()

    api_key = typer.prompt(
        f"{api_key_env}",
        hide_input=True,
        confirmation_prompt=False,
    ).strip()

    if not api_key:
        error_message("API key cannot be empty")
        raise typer.Exit(code=1)

    # Save to .env file
    env_file = Path.cwd() / ".env"
    _save_api_key_to_env(env_file, api_key_env, api_key)

    # Set in current environment for this session
    os.environ[api_key_env] = api_key

    success_message(f"API key saved to {env_file}")
    typer.echo()
    return api_key_env


def _create_test_config(provider_name: str, api_key_env: str) -> dict:
    """Create test configuration for provider.

    Args:
        provider_name: Name of provider
        api_key_env: Environment variable name

    Returns:
        Config dict for provider
    """
    default_llm_config = DEFAULT_CONFIG["llm"]

    if provider_name == "anthropic":
        return {
            "provider": "anthropic",
            "anthropic": {
                "model": default_llm_config["anthropic"]["model"],
                "api_key_env": api_key_env,
                "max_tokens": default_llm_config["anthropic"]["max_tokens"],
                "temperature": default_llm_config["anthropic"]["temperature"],
            },
        }
    elif provider_name == "openai":
        return {
            "provider": "openai",
            "openai": {
                "model": default_llm_config["openai"]["model"],
                "api_key_env": api_key_env,
                "max_tokens": default_llm_config["openai"]["max_tokens"],
                "temperature": default_llm_config["openai"]["temperature"],
            },
        }
    else:  # ollama
        return {
            "provider": "ollama",
            "ollama": {
                "model": default_llm_config["ollama"]["model"],
                "base_url": default_llm_config["ollama"]["base_url"],
                "timeout": default_llm_config["ollama"]["timeout"],
            },
        }


def _test_llm_connection(provider_name: str, config: dict) -> bool:
    """Test LLM provider connection.

    Args:
        provider_name: Name of provider
        config: Provider config

    Returns:
        True if successful, False otherwise
    """
    typer.secho("Step 3: Testing Connection", fg=typer.colors.CYAN, bold=True)
    typer.echo()

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


def _initialize_database(config: dict) -> Path:
    """Initialize database with migrations.

    Args:
        config: Application config

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
            # Create connection and run migrations
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


def _save_configuration(
    config: dict,
    provider_name: str,
    api_key_env: str,
    bonus_threshold: Decimal,
):
    """Save configuration to file.

    Args:
        config: LLM config
        provider_name: Provider name
        api_key_env: API key environment variable
        bonus_threshold: Bonus threshold
    """
    typer.secho("Step 6: Saving Configuration", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Build full config
    full_config = {
        "llm": config,
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
