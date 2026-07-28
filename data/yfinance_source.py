"""YFinance-backed implementation of the market data source interface."""

import logging
import time
from typing import Final

import pandas as pd
import yfinance as yf  # type: ignore[import-not-found,import-untyped]

from data.source import DataFetchError, DataSource, InvalidSymbolError

_REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)
_OHLC_COLUMNS: Final[tuple[str, ...]] = ("open", "high", "low", "close")


class YFinanceSource(DataSource):
    """Fetch historical OHLCV candles from Yahoo Finance via ``yfinance``."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the data source.

        Args:
            logger: Optional logger. When omitted, a module logger is used.
        """
        self._logger = logger or logging.getLogger(__name__)

    def get_latest_candles(
        self,
        symbol: str,
        interval: str,
        lookback: int,
    ) -> pd.DataFrame:
        """Fetch, normalize, and return the latest candles from yfinance."""
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_interval = self._validate_interval(interval)
        self._validate_lookback(lookback)

        started_at = time.perf_counter()
        raw_frame = self._download_with_retry(
            symbol=normalized_symbol,
            interval=normalized_interval,
            lookback=lookback,
        )
        clean_frame = (
            self._normalize_frame(raw_frame).tail(lookback).reset_index(drop=True)
        )
        duration_seconds = time.perf_counter() - started_at

        self._logger.info(
            "Fetched market candles",
            extra={
                "symbol": normalized_symbol,
                "interval": normalized_interval,
                "lookback": lookback,
                "rows_returned": len(clean_frame),
                "fetch_duration_seconds": duration_seconds,
            },
        )
        return clean_frame

    def _download_with_retry(
        self,
        symbol: str,
        interval: str,
        lookback: int,
    ) -> pd.DataFrame:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                frame = yf.download(
                    tickers=symbol,
                    period=self._period_for_lookback(lookback),
                    interval=interval,
                    progress=False,
                    auto_adjust=False,
                    threads=False,
                )
                if frame.empty:
                    msg = f"no candles returned for symbol: {symbol}"
                    raise DataFetchError(msg)
                return frame
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    self._logger.warning(
                        "Retrying market candle fetch",
                        extra={
                            "symbol": symbol,
                            "interval": interval,
                            "lookback": lookback,
                        },
                    )
        msg = f"failed to fetch candles for symbol: {symbol}"
        raise DataFetchError(msg) from last_error

    def _normalize_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        if isinstance(frame.columns, pd.MultiIndex):
            frame = frame.copy()
            frame.columns = frame.columns.get_level_values(0)

        normalized = frame.reset_index()
        normalized.columns = [str(column).lower() for column in normalized.columns]
        normalized = normalized.rename(
            columns={"date": "timestamp", "datetime": "timestamp"}
        )

        missing_columns = set(_REQUIRED_COLUMNS) - set(normalized.columns)
        if missing_columns:
            msg = (
                "downloaded candles missing required columns: "
                f"{sorted(missing_columns)}"
            )
            raise DataFetchError(msg)

        normalized = normalized.loc[:, list(_REQUIRED_COLUMNS)]
        normalized = normalized.dropna(subset=list(_OHLC_COLUMNS))
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"])
        if normalized["timestamp"].dt.tz is None:
            normalized["timestamp"] = normalized["timestamp"].dt.tz_localize("UTC")
        normalized = normalized.sort_values("timestamp", ascending=True)
        return normalized.reset_index(drop=True)

    def _normalize_symbol(self, symbol: str) -> str:
        stripped_symbol = symbol.strip()
        if not stripped_symbol:
            msg = "symbol must be a non-empty string"
            raise InvalidSymbolError(msg)
        if stripped_symbol.endswith(".NS"):
            return stripped_symbol
        return f"{stripped_symbol}.NS"

    def _validate_interval(self, interval: str) -> str:
        stripped_interval = interval.strip()
        if not stripped_interval:
            msg = "interval must be a non-empty string"
            raise DataFetchError(msg)
        return stripped_interval

    def _validate_lookback(self, lookback: int) -> None:
        if lookback <= 0:
            msg = "lookback must be greater than zero"
            raise DataFetchError(msg)

    def _period_for_lookback(self, lookback: int) -> str:
        return f"{lookback}d"
