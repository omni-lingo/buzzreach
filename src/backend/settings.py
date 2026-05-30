"""Application settings loaded from environment variables via pydantic-settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """BuzzReach application settings.

    All values are read from environment variables (or a .env file).
    Defaults are provided for local development; production must set
    secrets explicitly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Database ---
    database_url: str = Field(
        default="sqlite:///data/buzzreach.db",
        description="SQLAlchemy database URL",
    )
    db_schema: str = Field(
        default="buzzreach",
        description="Database schema name for all models",
    )

    # --- AI / Anthropic ---
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude scoring and drafting",
    )

    # --- Search provider ---
    search_api_key: str = Field(
        default="",
        description="API key for the search provider (Google, Bing, etc.)",
    )
    search_provider: str = Field(
        default="google",
        description="Search provider name (google, bing)",
    )

    # --- Auth / JWT ---
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_expire_minutes: int = Field(
        default=60,
        description="JWT token expiration in minutes",
    )

    # --- Email / SMTP ---
    smtp_host: str = Field(default="", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from_email: str = Field(
        default="noreply@buzzreach.app",
        description="Sender email address for digests",
    )

    # --- Slack ---
    slack_webhook_url: str = Field(
        default="",
        description="Slack incoming webhook URL for digest delivery",
    )

    # --- Rate Limiting ---
    rate_limit_tokens_per_minute: int = Field(
        default=100,
        description="Token bucket refill rate (tokens added per minute)",
    )
    rate_limit_burst_size: int = Field(
        default=100,
        description="Maximum token bucket capacity (burst allowance)",
    )

    # --- Config ---
    config_dir: Path = Field(
        default=Path("config"),
        description="Directory containing per-product JSON config files",
    )

    # --- Server ---
    host: str = Field(default="0.0.0.0", description="Server bind host")
    port: int = Field(default=8000, description="Server bind port")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
