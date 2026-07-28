"""Tests for TradeWatch configuration loading."""

from pathlib import Path

import pytest
import yaml

from config import ConfigurationError, load_config


def _valid_config() -> dict[str, object]:
    """Return a valid baseline configuration mapping."""
    return {
        "application": {
            "name": "TradeWatch",
            "environment": "test",
            "timezone": "Asia/Kolkata",
        },
        "watchlist": {"symbols": ["RELIANCE.NS", "TCS.NS"]},
        "strategy": {
            "timeframe": "15m",
            "ema_fast": 9,
            "ema_slow": 21,
            "atr_period": 14,
        },
        "polling": {"interval_seconds": 60},
        "telegram": {
            "enabled": False,
            "bot_token": "replace-with-telegram-bot-token",
            "chat_id": "replace-with-telegram-chat-id",
        },
        "logging": {
            "level": "INFO",
            "directory": "logs",
            "filename": "tradewatch.log",
            "max_file_size_mb": 10,
            "backup_count": 5,
        },
        "database": {"url": "sqlite:///tradewatch.db"},
    }


def _write_config(config_path: Path, config: dict[str, object]) -> None:
    """Write a YAML configuration file for tests."""
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")


def test_valid_config_loads_correctly(tmp_path: Path) -> None:
    """Valid YAML configuration loads into typed settings."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, _valid_config())

    settings = load_config(config_path)

    assert settings.application.name == "TradeWatch"
    assert settings.watchlist.symbols == ("RELIANCE.NS", "TCS.NS")
    assert settings.strategy.ema_fast == 9
    assert settings.strategy.ema_slow == 21
    assert settings.logging.level == "INFO"


def test_invalid_ema_values_raise_configuration_error(tmp_path: Path) -> None:
    """Invalid EMA ordering raises the public configuration exception."""
    config = _valid_config()
    strategy = config["strategy"]
    assert isinstance(strategy, dict)
    strategy["ema_fast"] = 21
    strategy["ema_slow"] = 9
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, config)

    with pytest.raises(ConfigurationError, match="ema_slow"):
        load_config(config_path)


def test_missing_configuration_file_raises_configuration_error(tmp_path: Path) -> None:
    """Missing configuration files raise the public configuration exception."""
    missing_path = tmp_path / "missing-config.yaml"

    with pytest.raises(ConfigurationError, match="configuration file not found"):
        load_config(missing_path)
