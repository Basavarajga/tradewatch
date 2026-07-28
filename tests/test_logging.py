"""Tests for centralized logging initialization."""

from pathlib import Path

from config import LoggingSettings
from logging_setup import setup_logging


def _logging_settings(log_directory: Path) -> LoggingSettings:
    """Create logging settings for tests."""
    return LoggingSettings(
        level="INFO",
        directory=log_directory,
        filename="tradewatch.log",
        max_file_size_mb=1,
        backup_count=1,
    )


def test_logger_initializes_successfully(tmp_path: Path) -> None:
    """setup_logging returns a configured logger."""
    logger = setup_logging(_logging_settings(tmp_path / "logs"), "tests.logging.init")

    assert logger.name == "tests.logging.init"
    assert logger.getEffectiveLevel() == 20
    assert len(logger.handlers) == 2


def test_log_directory_is_created(tmp_path: Path) -> None:
    """setup_logging creates the configured log directory."""
    log_directory = tmp_path / "logs"

    setup_logging(_logging_settings(log_directory), "tests.logging.directory")

    assert log_directory.is_dir()


def test_duplicate_setup_calls_do_not_create_duplicate_handlers(tmp_path: Path) -> None:
    """Repeated setup_logging calls do not add duplicate managed handlers."""
    logger_name = "tests.logging.duplicates"
    settings = _logging_settings(tmp_path / "logs")

    first_logger = setup_logging(settings, logger_name)
    first_handler_ids = {id(handler) for handler in first_logger.handlers}
    second_logger = setup_logging(settings, logger_name)
    second_handler_ids = {id(handler) for handler in second_logger.handlers}

    assert second_logger is first_logger
    assert len(second_logger.handlers) == 2
    assert second_handler_ids == first_handler_ids
