"""Base abstractions for stateless trading strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass(frozen=True, slots=True)
class Signal:
    """Trading signal produced by a strategy evaluation.

    Attributes:
        symbol: Market symbol associated with the signal.
        timestamp: Timestamp for the candle that generated the signal.
        signal_type: Direction of the signal, either ``BUY`` or ``SELL``.
        strategy: Stable strategy identifier.
        price: Latest close price used for the signal.
        reason: Human-readable explanation for why the signal was emitted.
    """

    symbol: str
    timestamp: pd.Timestamp
    signal_type: Literal["BUY", "SELL"]
    strategy: str
    price: float
    reason: str


class Strategy(ABC):
    """Abstract interface for stateless market-data strategy evaluation."""

    @abstractmethod
    def evaluate(self, symbol: str, data: pd.DataFrame) -> Signal | None:
        """Evaluate market data and optionally return a trading signal.

        Args:
            symbol: Market symbol to evaluate.
            data: Historical candle data ordered chronologically.

        Returns:
            A trading ``Signal`` when strategy rules trigger, otherwise ``None``.
        """
        raise NotImplementedError
