"""Abstract market data source interface for historical OHLCV candles.

All application components that need historical market candles must depend on
``DataSource`` instead of directly importing a vendor SDK. Concrete data source
implementations are responsible for vendor-specific symbol formatting, network
calls, retries, validation, and normalization into the canonical candle schema.
"""

from abc import ABC, abstractmethod

import pandas as pd


class DataSourceError(Exception):
    """Base exception for all market data source failures."""


class DataFetchError(DataSourceError):
    """Raised when a data source cannot fetch or normalize requested candles."""


class InvalidSymbolError(DataSourceError):
    """Raised when a requested market symbol is empty or otherwise invalid."""


class DataSource(ABC):
    """Interface for retrieving historical OHLCV candles.

    Implementations must return a clean ``pandas.DataFrame`` containing exactly
    these columns, in this order:

    - ``timestamp``
    - ``open``
    - ``high``
    - ``low``
    - ``close``
    - ``volume``

    The ``timestamp`` column must contain timezone-aware values. OHLC values
    must be numeric, rows with missing open/high/low/close values must be
    removed, and rows must be sorted chronologically before being returned.

    Implementations should raise ``InvalidSymbolError`` for invalid symbols and
    ``DataFetchError`` for retrieval or normalization failures. Callers should
    only rely on this interface and these shared exceptions, not vendor-specific
    SDK behavior.
    """

    @abstractmethod
    def get_latest_candles(
        self,
        symbol: str,
        interval: str,
        lookback: int,
    ) -> pd.DataFrame:
        """Return the latest historical candles for a symbol.

        Args:
            symbol: Market symbol requested by the caller. Implementations may
                normalize it for the backing provider while preserving this
                public API.
            interval: Candle interval supported by the backing data provider.
            lookback: Positive number of most-recent candles to return.

        Returns:
            A ``pandas.DataFrame`` with exactly ``timestamp``, ``open``,
            ``high``, ``low``, ``close``, and ``volume`` columns. The
            ``timestamp`` column is timezone-aware.

        Raises:
            InvalidSymbolError: If ``symbol`` is blank or invalid.
            DataFetchError: If ``interval`` or ``lookback`` is invalid, the
                provider request fails, or returned data cannot be normalized.
        """
        raise NotImplementedError
