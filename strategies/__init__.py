"""Stateless trading strategy abstractions and implementations."""

from strategies.base import Signal, Strategy
from strategies.ema_crossover import (
    EMACrossoverStrategy,
    InvalidStrategyInput,
    StrategyError,
)

__all__ = [
    "EMACrossoverStrategy",
    "InvalidStrategyInput",
    "Signal",
    "Strategy",
    "StrategyError",
]
