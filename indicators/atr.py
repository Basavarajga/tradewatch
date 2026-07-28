"""Average true range indicator."""

import pandas as pd

from indicators import InvalidIndicatorInput

_REQUIRED_COLUMNS = frozenset({"high", "low", "close"})


def calculate_atr(data: pd.DataFrame, period: int) -> pd.Series:
    """Calculate the average true range for OHLC data.

    Args:
        data: Input DataFrame containing ``high``, ``low``, and ``close``
            columns.
        period: Positive ATR lookback period.

    Returns:
        A new pandas Series containing the ATR values, preserving the input
        DataFrame index and named ``ATR_<period>``.

    Raises:
        InvalidIndicatorInput: If ``data`` is not a DataFrame, required OHLC
            columns are missing, ``period`` is not positive, or there are fewer
            rows than ``period``.
    """
    if not isinstance(data, pd.DataFrame):
        raise InvalidIndicatorInput("data must be a pandas DataFrame")
    if not isinstance(period, int) or period <= 0:
        raise InvalidIndicatorInput("period must be a positive integer")

    missing_columns = sorted(_REQUIRED_COLUMNS.difference(data.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise InvalidIndicatorInput(f"required columns are missing: {missing}")
    if len(data) < period:
        raise InvalidIndicatorInput(
            f"insufficient history: need at least {period} rows, got {len(data)}"
        )

    previous_close = data["close"].shift(1)
    true_range_components = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - previous_close).abs(),
            (data["low"] - previous_close).abs(),
        ],
        axis=1,
    )
    true_range = true_range_components.max(axis=1)
    atr = true_range.ewm(span=period, adjust=False).mean()
    return atr.rename(f"ATR_{period}")
