"""Typed configuration loading for TradeWatch.

The module reads a YAML file and validates it into immutable Pydantic models.
Callers may pass any configuration path, which keeps the loader free of
hardcoded project-specific locations.
"""

from pathlib import Path
from typing import Self

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
)


class ConfigurationError(ValueError):
    """Raised when application configuration cannot be loaded or validated."""


class StrictModel(BaseModel):
    """Base model that rejects unknown configuration keys."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ApplicationSettings(StrictModel):
    """Application identity and runtime environment settings."""

    name: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    timezone: str = Field(min_length=1)


class WatchlistSettings(StrictModel):
    """Symbols monitored by the application foundation."""

    symbols: tuple[str, ...] = Field(min_length=1)

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, symbols: tuple[str, ...]) -> tuple[str, ...]:
        """Ensure configured symbols are non-empty strings.

        Args:
            symbols: Symbol values loaded from configuration.

        Returns:
            The validated symbols.

        Raises:
            ValueError: If any symbol is blank.
        """
        if any(not symbol.strip() for symbol in symbols):
            msg = "watchlist symbols must be non-empty strings"
            raise ValueError(msg)
        return symbols


class StrategySettings(StrictModel):
    """Strategy parameter configuration without strategy implementation logic."""

    timeframe: str = Field(min_length=1)
    ema_fast: int = Field(gt=0)
    ema_slow: int = Field(gt=0)
    atr_period: int = Field(gt=0)

    @field_validator("ema_slow")
    @classmethod
    def validate_ema_order(cls, ema_slow: int, info: ValidationInfo) -> int:
        """Validate that the slow EMA period is greater than the fast period.

        Args:
            ema_slow: Slow EMA period.
            info: Pydantic validation context containing prior field values.

        Returns:
            The validated slow EMA period.

        Raises:
            ValueError: If the slow EMA period is not greater than the fast one.
        """
        ema_fast = info.data.get("ema_fast")
        if isinstance(ema_fast, int) and ema_slow <= ema_fast:
            msg = "strategy.ema_slow must be greater than strategy.ema_fast"
            raise ValueError(msg)
        return ema_slow


class PollingSettings(StrictModel):
    """Polling cadence settings."""

    interval_seconds: int = Field(gt=0)


class TelegramSettings(StrictModel):
    """Telegram notification connection settings."""

    enabled: bool
    bot_token: str = Field(min_length=1)
    chat_id: str = Field(min_length=1)


class LoggingSettings(StrictModel):
    """Logging destination and rotation settings."""

    level: str = Field(min_length=1)
    directory: Path
    filename: str = Field(min_length=1)
    max_file_size_mb: int = Field(gt=0)
    backup_count: int = Field(ge=0)

    @field_validator("level")
    @classmethod
    def normalize_level(cls, level: str) -> str:
        """Normalize and validate a Python logging level name.

        Args:
            level: Configured logging level.

        Returns:
            Uppercase logging level name.

        Raises:
            ValueError: If the level is unsupported.
        """
        normalized = level.upper()
        valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        if normalized not in valid_levels:
            msg = f"unsupported logging level: {level}"
            raise ValueError(msg)
        return normalized


class DatabaseSettings(StrictModel):
    """Database connection settings."""

    url: str = Field(min_length=1)


class TradeWatchSettings(StrictModel):
    """Root configuration object for TradeWatch."""

    application: ApplicationSettings
    watchlist: WatchlistSettings
    strategy: StrategySettings
    polling: PollingSettings
    telegram: TelegramSettings
    logging: LoggingSettings
    database: DatabaseSettings

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> Self:
        """Load and validate settings from a YAML file.

        Args:
            config_path: Filesystem path to the YAML configuration file.

        Returns:
            A validated settings object.

        Raises:
            ConfigurationError: If the file is missing, malformed, empty, or
                fails validation.
        """
        path = Path(config_path).expanduser()
        if not path.is_file():
            msg = f"configuration file not found: {path}"
            raise ConfigurationError(msg)

        try:
            with path.open("r", encoding="utf-8") as file_handle:
                raw_config = yaml.safe_load(file_handle)
        except yaml.YAMLError as exc:
            msg = f"configuration file contains invalid YAML: {path}"
            raise ConfigurationError(msg) from exc
        except OSError as exc:
            msg = f"configuration file could not be read: {path}"
            raise ConfigurationError(msg) from exc

        if not isinstance(raw_config, dict):
            msg = f"configuration file must contain a YAML mapping: {path}"
            raise ConfigurationError(msg)

        try:
            return cls.model_validate(raw_config)
        except ValidationError as exc:
            msg = f"configuration validation failed for {path}: {exc}"
            raise ConfigurationError(msg) from exc


def load_config(config_path: str | Path) -> TradeWatchSettings:
    """Load TradeWatch settings from a YAML configuration file.

    Args:
        config_path: Filesystem path to the YAML configuration file.

    Returns:
        Validated TradeWatch settings.
    """
    return TradeWatchSettings.from_yaml(config_path)
