"""Tests for the yfinance market data source."""

from collections.abc import Iterator
from unittest.mock import Mock

import pandas as pd
import pytest

from data.source import DataFetchError, InvalidSymbolError
from data.yfinance_source import YFinanceSource

_EXPECTED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


@pytest.fixture
def downloaded_frame() -> pd.DataFrame:
    """Return deterministic yfinance-like OHLCV data."""
    return pd.DataFrame(
        {
            "Open": [101.0, 102.0, None],
            "High": [106.0, 107.0, 108.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [104.0, 105.0, 106.0],
            "Volume": [1_000, 1_100, 1_200],
        },
        index=pd.DatetimeIndex(
            [
                "2026-01-03 09:15:00+05:30",
                "2026-01-01 09:15:00+05:30",
                "2026-01-02 09:15:00+05:30",
            ],
            name="Datetime",
        ),
    )


@pytest.fixture
def yfinance_download(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Patch yfinance download with a mock."""
    download = Mock()
    monkeypatch.setattr("data.yfinance_source.yf.download", download)
    return download


def test_valid_fetch_returns_clean_chronological_dataframe(
    yfinance_download: Mock,
    downloaded_frame: pd.DataFrame,
) -> None:
    """A valid fetch returns cleaned candles in canonical order."""
    yfinance_download.return_value = downloaded_frame

    candles = YFinanceSource().get_latest_candles("RELIANCE", "1d", 10)

    assert list(candles.columns) == _EXPECTED_COLUMNS
    assert len(candles) == 2
    assert candles["timestamp"].dt.tz is not None
    assert candles["timestamp"].is_monotonic_increasing
    assert candles.iloc[0]["open"] == 102.0
    assert candles.iloc[1]["open"] == 101.0


def test_automatic_ns_suffix(
    yfinance_download: Mock,
    downloaded_frame: pd.DataFrame,
) -> None:
    """NSE symbols without a suffix are sent to yfinance with .NS appended."""
    yfinance_download.return_value = downloaded_frame

    YFinanceSource().get_latest_candles("TCS", "1d", 5)

    assert yfinance_download.call_args.kwargs["tickers"] == "TCS.NS"


def test_existing_ns_suffix_preserved(
    yfinance_download: Mock,
    downloaded_frame: pd.DataFrame,
) -> None:
    """Symbols already ending in .NS are not modified."""
    yfinance_download.return_value = downloaded_frame

    YFinanceSource().get_latest_candles("INFY.NS", "1d", 5)

    assert yfinance_download.call_args.kwargs["tickers"] == "INFY.NS"


def test_invalid_lookback_raises_data_fetch_error() -> None:
    """Non-positive lookback values are rejected."""
    with pytest.raises(DataFetchError, match="lookback"):
        YFinanceSource().get_latest_candles("RELIANCE", "1d", 0)


def test_empty_symbol_raises_invalid_symbol_error() -> None:
    """Blank symbols are rejected."""
    with pytest.raises(InvalidSymbolError, match="symbol"):
        YFinanceSource().get_latest_candles("  ", "1d", 5)


def test_empty_interval_raises_data_fetch_error() -> None:
    """Blank intervals are rejected."""
    with pytest.raises(DataFetchError, match="interval"):
        YFinanceSource().get_latest_candles("RELIANCE", " ", 5)


def test_retry_succeeds(
    yfinance_download: Mock,
    downloaded_frame: pd.DataFrame,
) -> None:
    """A transient first failure is retried once."""
    yfinance_download.side_effect = [RuntimeError("temporary"), downloaded_frame]

    candles = YFinanceSource().get_latest_candles("RELIANCE", "1d", 5)

    assert len(candles) == 2
    assert yfinance_download.call_count == 2


def test_retry_fails(yfinance_download: Mock) -> None:
    """Two failed attempts raise the shared fetch exception."""
    yfinance_download.side_effect = _errors()

    with pytest.raises(DataFetchError, match="failed to fetch"):
        YFinanceSource().get_latest_candles("RELIANCE", "1d", 5)

    assert yfinance_download.call_count == 2


def test_dataframe_columns_exactly_match_specification(
    yfinance_download: Mock,
    downloaded_frame: pd.DataFrame,
) -> None:
    """Returned candle columns exactly match the DataSource contract."""
    yfinance_download.return_value = downloaded_frame

    candles = YFinanceSource().get_latest_candles("RELIANCE", "1d", 5)

    assert candles.columns.tolist() == _EXPECTED_COLUMNS


def _errors() -> Iterator[RuntimeError]:
    """Yield repeated transient errors for retry tests."""
    yield RuntimeError("first")
    yield RuntimeError("second")
