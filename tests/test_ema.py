"""Tests for EMA indicator calculations."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from indicators import InvalidIndicatorInput
from indicators.ema import calculate_ema


def test_valid_calculation() -> None:
    """EMA calculation matches pandas ewm and preserves the original index."""
    data = pd.DataFrame(
        {"close": [10.0, 12.0, 14.0, 13.0]},
        index=pd.Index(["a", "b", "c", "d"], name="bar"),
    )

    ema = calculate_ema(data, 3)

    expected = data["close"].ewm(span=3, adjust=False).mean().rename("EMA_3")
    assert_series_equal(ema, expected)
    assert ema.index.equals(data.index)


@pytest.mark.parametrize("period", [0, -1])
def test_invalid_period(period: int) -> None:
    """Non-positive periods are rejected."""
    data = pd.DataFrame({"close": [10.0, 11.0]})

    with pytest.raises(InvalidIndicatorInput, match="period"):
        calculate_ema(data, period)


def test_missing_column() -> None:
    """A missing source column is rejected."""
    data = pd.DataFrame({"open": [10.0, 11.0]})

    with pytest.raises(InvalidIndicatorInput, match="close"):
        calculate_ema(data, 2)


def test_insufficient_history() -> None:
    """The input must contain at least period rows."""
    data = pd.DataFrame({"close": [10.0, 11.0]})

    with pytest.raises(InvalidIndicatorInput, match="insufficient history"):
        calculate_ema(data, 3)


def test_original_dataframe_unchanged() -> None:
    """EMA calculation does not mutate the input DataFrame."""
    data = pd.DataFrame({"close": [10.0, 12.0, 14.0], "volume": [1, 2, 3]})
    original = data.copy(deep=True)

    calculate_ema(data, 2)

    assert_frame_equal(data, original)
