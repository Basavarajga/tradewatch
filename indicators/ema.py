"""Exponential moving average indicator."""

import pandas as pd

from indicators import InvalidIndicatorInput


def calculate_ema(
    data: pd.DataFrame,
    period: int,
    column: str = "close",
) -> pd.Series:
    """Calculate an exponential moving average for a DataFrame column.

    Args:
        data: Input DataFrame containing the source price column.
        period: Positive EMA lookback period.
        column: Name of the column to calculate the EMA from.

    Returns:
        A new pandas Series containing the EMA values, preserving the input
        DataFrame index and named ``EMA_<period>``.

    Raises:
        InvalidIndicatorInput: If ``data`` is not a DataFrame, ``column`` is
            missing or blank, ``period`` is not positive, or there are fewer
            rows than ``period``.
    """
    if not isinstance(data, pd.DataFrame):
        raise InvalidIndicatorInput("data must be a pandas DataFrame")
    if not isinstance(period, int) or period <= 0:
        raise InvalidIndicatorInput("period must be a positive integer")
    if not column:
        raise InvalidIndicatorInput("column must be a non-empty string")
    if column not in data.columns:
        raise InvalidIndicatorInput(f"required column '{column}' is missing")
    if len(data) < period:
        raise InvalidIndicatorInput(
            f"insufficient history: need at least {period} rows, got {len(data)}"
        )

    ema = data[column].ewm(span=period, adjust=False).mean()
    return ema.rename(f"EMA_{period}")
