"""Tests for ATR indicator calculations."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from indicators import InvalidIndicatorInput
from indicators.atr import calculate_atr


def test_valid_calculation() -> None:
    """ATR calculation matches true range smoothed by pandas ewm."""
    data = pd.DataFrame(
        {
            "high": [12.0, 15.0, 14.0, 16.0],
            "low": [9.0, 11.0, 10.0, 13.0],
            "close": [10.0, 14.0, 11.0, 15.0],
        },
        index=pd.Index([10, 20, 30, 40], name="bar"),
    )

    atr = calculate_atr(data, 3)

    previous_close = data["close"].shift(1)
    true_range = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - previous_close).abs(),
            (data["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    expected = true_range.ewm(span=3, adjust=False).mean().rename("ATR_3")
    assert_series_equal(atr, expected)
    assert atr.index.equals(data.index)


@pytest.mark.parametrize(
    "columns",
    [
        {"low": [9.0, 10.0], "close": [10.0, 11.0]},
        {"high": [12.0, 13.0], "close": [10.0, 11.0]},
        {"high": [12.0, 13.0], "low": [9.0, 10.0]},
    ],
)
def test_missing_required_columns(columns: dict[str, list[float]]) -> None:
    """Missing OHLC columns are rejected."""
    data = pd.DataFrame(columns)

    with pytest.raises(InvalidIndicatorInput, match="missing"):
        calculate_atr(data, 2)


@pytest.mark.parametrize("period", [0, -1])
def test_invalid_period(period: int) -> None:
    """Non-positive periods are rejected."""
    data = pd.DataFrame(
        {"high": [12.0, 13.0], "low": [9.0, 10.0], "close": [10.0, 11.0]}
    )

    with pytest.raises(InvalidIndicatorInput, match="period"):
        calculate_atr(data, period)


def test_insufficient_history() -> None:
    """The input must contain at least period rows."""
    data = pd.DataFrame(
        {"high": [12.0, 13.0], "low": [9.0, 10.0], "close": [10.0, 11.0]}
    )

    with pytest.raises(InvalidIndicatorInput, match="insufficient history"):
        calculate_atr(data, 3)


def test_original_dataframe_unchanged() -> None:
    """ATR calculation does not mutate the input DataFrame."""
    data = pd.DataFrame(
        {
            "high": [12.0, 15.0, 14.0],
            "low": [9.0, 11.0, 10.0],
            "close": [10.0, 14.0, 11.0],
            "volume": [1, 2, 3],
        }
    )
    original = data.copy(deep=True)

    calculate_atr(data, 2)

    assert_frame_equal(data, original)
