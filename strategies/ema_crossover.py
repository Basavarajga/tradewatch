"""EMA crossover strategy implementation."""

from typing import Literal

import pandas as pd

from indicators import InvalidIndicatorInput
from indicators.ema import calculate_ema
from strategies.base import Signal, Strategy


class StrategyError(Exception):
    """Base exception for strategy evaluation failures."""


class InvalidStrategyInput(StrategyError):  # noqa: N818
    """Raised when strategy configuration or market data is invalid."""


class EMACrossoverStrategy(Strategy):
    """Generate signals when a fast EMA crosses a slow EMA."""

    name = "EMA_CROSSOVER"

    def __init__(self, fast_period: int, slow_period: int) -> None:
        """Initialize the EMA crossover strategy.

        Args:
            fast_period: Positive lookback period for the fast EMA.
            slow_period: Lookback period for the slow EMA; must exceed
                ``fast_period``.

        Raises:
            InvalidStrategyInput: If periods are invalid.
        """
        if not isinstance(fast_period, int) or fast_period <= 0:
            raise InvalidStrategyInput("fast_period must be a positive integer")
        if not isinstance(slow_period, int) or slow_period <= fast_period:
            raise InvalidStrategyInput(
                "slow_period must be an integer greater than fast_period"
            )

        self.fast_period = fast_period
        self.slow_period = slow_period

    def evaluate(self, symbol: str, data: pd.DataFrame) -> Signal | None:
        """Evaluate EMA crossover rules for the latest candle.

        Args:
            symbol: Market symbol to evaluate.
            data: Historical candle data ordered chronologically with
                ``timestamp`` and ``close`` columns.

        Returns:
            A BUY or SELL signal when the latest candle completes a crossover,
            otherwise ``None``.

        Raises:
            InvalidStrategyInput: If symbol or data is invalid, or if there is
                insufficient history to compute both EMAs and compare the last
                two candles.
        """
        self._validate_inputs(symbol, data)

        try:
            fast_ema = calculate_ema(data, self.fast_period)
            slow_ema = calculate_ema(data, self.slow_period)
        except InvalidIndicatorInput as exc:
            raise InvalidStrategyInput(str(exc)) from exc

        previous_fast = float(fast_ema.iloc[-2])
        previous_slow = float(slow_ema.iloc[-2])
        current_fast = float(fast_ema.iloc[-1])
        current_slow = float(slow_ema.iloc[-1])

        if previous_fast <= previous_slow and current_fast > current_slow:
            return self._build_signal(symbol, data, "BUY", "Bullish EMA crossover")
        if previous_fast >= previous_slow and current_fast < current_slow:
            return self._build_signal(symbol, data, "SELL", "Bearish EMA crossover")
        return None

    def _validate_inputs(self, symbol: str, data: pd.DataFrame) -> None:
        """Validate evaluation inputs before indicator calculation."""
        if not symbol.strip():
            raise InvalidStrategyInput("symbol must be a non-empty string")
        if not isinstance(data, pd.DataFrame):
            raise InvalidStrategyInput("data must be a pandas DataFrame")
        if "timestamp" not in data.columns:
            raise InvalidStrategyInput("required column 'timestamp' is missing")
        if "close" not in data.columns:
            raise InvalidStrategyInput("required column 'close' is missing")

        minimum_rows = max(self.slow_period, 2)
        if len(data) < minimum_rows:
            raise InvalidStrategyInput(
                "insufficient history: need at least "
                f"{minimum_rows} rows, got {len(data)}"
            )

    def _build_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        signal_type: Literal["BUY", "SELL"],
        reason: str,
    ) -> Signal:
        """Create a signal from the latest candle."""
        latest = data.iloc[-1]
        return Signal(
            symbol=symbol,
            timestamp=pd.Timestamp(latest["timestamp"]),
            signal_type=signal_type,
            strategy=self.name,
            price=float(latest["close"]),
            reason=reason,
        )
