"""Reusable technical indicator library."""


class IndicatorError(Exception):
    """Base exception for technical indicator failures."""


class InvalidIndicatorInput(IndicatorError):  # noqa: N818
    """Raised when indicator inputs are invalid or insufficient."""
