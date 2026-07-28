"""Tests for EMA crossover strategy evaluation."""

from dataclasses import FrozenInstanceError

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from strategies import EMACrossoverStrategy, InvalidStrategyInput, Signal


def _candles(closes: list[float]) -> pd.DataFrame:
    """Build deterministic candle data for strategy tests."""
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2026-01-01 09:30", periods=len(closes), freq="1min", tz="UTC"
            ),
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [100] * len(closes),
        }
    )


def test_buy_signal() -> None:
    """A fast EMA crossing above a slow EMA emits a BUY signal."""
    data = _candles([10.0, 10.0, 10.0, 20.0])
    strategy = EMACrossoverStrategy(fast_period=2, slow_period=3)

    signal = strategy.evaluate("AAPL", data)

    assert signal == Signal(
        symbol="AAPL",
        timestamp=pd.Timestamp("2026-01-01 09:33", tz="UTC"),
        signal_type="BUY",
        strategy="EMA_CROSSOVER",
        price=20.0,
        reason="Bullish EMA crossover",
    )


def test_sell_signal() -> None:
    """A fast EMA crossing below a slow EMA emits a SELL signal."""
    data = _candles([20.0, 20.0, 20.0, 10.0])
    strategy = EMACrossoverStrategy(fast_period=2, slow_period=3)

    signal = strategy.evaluate("AAPL", data)

    assert signal == Signal(
        symbol="AAPL",
        timestamp=pd.Timestamp("2026-01-01 09:33", tz="UTC"),
        signal_type="SELL",
        strategy="EMA_CROSSOVER",
        price=10.0,
        reason="Bearish EMA crossover",
    )


def test_no_signal() -> None:
    """No signal is emitted when the latest candle does not complete a crossover."""
    data = _candles([10.0, 20.0, 30.0, 40.0])
    strategy = EMACrossoverStrategy(fast_period=2, slow_period=3)

    assert strategy.evaluate("AAPL", data) is None


@pytest.mark.parametrize(
    ("fast_period", "slow_period"),
    [
        (0, 3),
        (-1, 3),
        (3, 3),
        (4, 3),
    ],
)
def test_invalid_periods(fast_period: int, slow_period: int) -> None:
    """Invalid EMA periods are rejected during strategy construction."""
    with pytest.raises(InvalidStrategyInput, match="period"):
        EMACrossoverStrategy(fast_period=fast_period, slow_period=slow_period)


def test_insufficient_history() -> None:
    """Enough candles for the slow EMA and crossover comparison are required."""
    data = _candles([10.0, 11.0])
    strategy = EMACrossoverStrategy(fast_period=2, slow_period=3)

    with pytest.raises(InvalidStrategyInput, match="insufficient history"):
        strategy.evaluate("AAPL", data)


def test_dataframe_unchanged() -> None:
    """Evaluating the strategy does not mutate the input DataFrame."""
    data = _candles([10.0, 10.0, 10.0, 20.0])
    original = data.copy(deep=True)
    strategy = EMACrossoverStrategy(fast_period=2, slow_period=3)

    strategy.evaluate("AAPL", data)

    assert_frame_equal(data, original)


def test_signal_is_immutable() -> None:
    """Generated signals are immutable dataclass instances."""
    signal = Signal(
        symbol="AAPL",
        timestamp=pd.Timestamp("2026-01-01 09:33", tz="UTC"),
        signal_type="BUY",
        strategy="EMA_CROSSOVER",
        price=20.0,
        reason="Bullish EMA crossover",
    )

    with pytest.raises(FrozenInstanceError):
        signal.price = 21.0  # type: ignore[misc]
