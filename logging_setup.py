"""Centralized logging configuration for TradeWatch."""

import logging
from logging import Handler, Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import LoggingSettings

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(module)s %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
_BYTES_PER_MEGABYTE = 1024 * 1024
_FILE_HANDLER_NAME = "tradewatch.rotating_file"
_CONSOLE_HANDLER_NAME = "tradewatch.console"


def setup_logging(settings: LoggingSettings, logger_name: str | None = None) -> Logger:
    """Configure console and rotating file logging once.

    Args:
        settings: Validated logging configuration.
        logger_name: Optional logger name. When omitted, the root logger is
            configured and returned.

    Returns:
        The configured logger instance.
    """
    log_directory = Path(settings.directory)
    log_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(settings.level)
    logger.propagate = False

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)
    log_file = log_directory / settings.filename
    max_bytes = settings.max_file_size_mb * _BYTES_PER_MEGABYTE

    file_handler = _get_named_handler(logger, _FILE_HANDLER_NAME)
    if file_handler is None:
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=settings.backup_count,
            encoding="utf-8",
        )
        file_handler.set_name(_FILE_HANDLER_NAME)
        logger.addHandler(file_handler)

    console_handler = _get_named_handler(logger, _CONSOLE_HANDLER_NAME)
    if console_handler is None:
        console_handler = logging.StreamHandler()
        console_handler.set_name(_CONSOLE_HANDLER_NAME)
        logger.addHandler(console_handler)

    for handler in (file_handler, console_handler):
        handler.setLevel(settings.level)
        handler.setFormatter(formatter)

    return logger


def _get_named_handler(logger: Logger, handler_name: str) -> Handler | None:
    """Return an existing handler by name without mutating logger handlers.

    Args:
        logger: Logger to inspect.
        handler_name: Handler name to find.

    Returns:
        Matching handler when present; otherwise, ``None``.
    """
    for handler in logger.handlers:
        if handler.get_name() == handler_name:
            return handler
    return None
