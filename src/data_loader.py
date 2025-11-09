"""Utilities for fetching and caching cryptocurrency, macro, and market metrics."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import pandas as pd
import requests
import yfinance as yf
from pandas.api.types import is_datetime64tz_dtype

try:  # Optional import so unit tests can mock it easily.
    from pandas_datareader import data as data_reader
except ImportError:  # pragma: no cover - documented dependency.
    data_reader = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def ensure_data_dir() -> Path:
    """Create the data directory if needed and return its path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _format_date(value: date | datetime | str | None) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _to_unix_timestamp(value: date | datetime | str | int | float | None) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return int(pd.Timestamp(value).timestamp())


def _price_output_path(symbol: str, interval: str) -> Path:
    return ensure_data_dir() / f"{symbol.lower()}_{interval}.csv"


def _macro_output_path(series_id: str) -> Path:
    return ensure_data_dir() / f"macro_{series_id.lower()}.csv"


def _cmc_global_output_path(convert: str) -> Path:
    return ensure_data_dir() / f"cmc_global_{convert.lower()}.csv"


def _cmc_asset_output_path(symbols: Sequence[str], convert: str) -> Path:
    slug = "_".join(sorted(symbols)).lower()
    return ensure_data_dir() / f"cmc_quotes_{slug}_{convert.lower()}.csv"


def _strip_timezone(series: pd.Series) -> pd.Series:
    if is_datetime64tz_dtype(series):
        return series.dt.tz_localize(None)
    return series


@dataclass
class DownloadConfig:
    symbol: str
    start: date | datetime | str
    end: Optional[date | datetime | str] = None
    interval: str = "1d"


@dataclass
class MacroSeriesConfig:
    """Configuration for fetching macroeconomic series (e.g., FRED)."""

    series_id: str
    start: date | datetime | str
    end: Optional[date | datetime | str] = None
    source: str = "fred"
    api_key: Optional[str] = None


@dataclass
class CoinMarketCapGlobalConfig:
    """Configuration for CoinMarketCap global metrics."""

    convert: str = "USD"
    api_key: Optional[str] = None


@dataclass
class CoinMarketCapAssetConfig:
    """Configuration for CoinMarketCap cryptocurrency quotes."""

    symbols: Sequence[str]
    convert: str = "USD"
    api_key: Optional[str] = None


@dataclass
class OkxCandlesConfig:
    """Configuration for fetching OKX candlestick data."""

    inst_id: str
    bar: str = "1D"
    after: Optional[date | datetime | str | int] = None
    before: Optional[date | datetime | str | int] = None
    limit: int = 200


def download_price_history(config: DownloadConfig, force: bool = False) -> Path:
    """Download historical price data for a single symbol and cache it as CSV."""
    output_path = _price_output_path(config.symbol, config.interval)
    if output_path.exists() and not force:
        return output_path

    ticker = yf.Ticker(config.symbol)
    data = ticker.history(
        start=_format_date(config.start),
        end=_format_date(config.end),
        interval=config.interval,
    )
    if data.empty:
        raise ValueError(f"No data returned for {config.symbol}")

    if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
        data.index = data.index.tz_localize(None)
    data.index.name = "date"
    data.reset_index().to_csv(output_path, index=False)
    return output_path


def download_price_histories(configs: Sequence[DownloadConfig], force: bool = False) -> Dict[str, Path]:
    """Batch download helper that returns a map of symbol -> cached CSV path."""
    return {cfg.symbol: download_price_history(cfg, force=force) for cfg in configs}


def load_history(symbol: str, interval: str = "1d") -> pd.DataFrame:
    """Load a cached price CSV into a DataFrame."""
    csv_path = _price_output_path(symbol, interval)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Fetch data with download_price_history first."
        )
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in df.columns:
        df["date"] = _strip_timezone(df["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def download_macro_series(config: MacroSeriesConfig, force: bool = False) -> Path:
    """Download a macro series (default FRED) and cache it."""
    csv_path = _macro_output_path(config.series_id)
    if csv_path.exists() and not force:
        return csv_path

    if data_reader is None:
        raise ImportError("pandas-datareader is required for macro downloads. Install via `pip install pandas-datareader`.")

    if config.api_key:
        os.environ.setdefault("FRED_API_KEY", config.api_key)

    start = pd.to_datetime(config.start)
    end = pd.to_datetime(config.end) if config.end else None
    series = data_reader.DataReader(config.series_id, config.source, start, end)
    if isinstance(series, pd.Series):
        df = series.to_frame(name="value")
    else:
        df = series.copy()
        if len(df.columns) == 1:
            df.columns = ["value"]
        else:
            df.columns = [str(col) for col in df.columns]
    df.index.name = "date"
    df.reset_index().to_csv(csv_path, index=False)
    return csv_path


def load_macro_series(series_id: str) -> pd.DataFrame:
    """Load a cached macro CSV."""
    csv_path = _macro_output_path(series_id)
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found. Fetch data with download_macro_series first.")
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in df.columns:
        df["date"] = _strip_timezone(df["date"])
    return df


def _coinmarketcap_headers(api_key: Optional[str]) -> Dict[str, str]:
    key = api_key or os.getenv("COINMARKETCAP_API_KEY")
    if not key:
        raise EnvironmentError(
            "COINMARKETCAP_API_KEY is required. Export it or pass api_key to the config."
        )
    return {"X-CMC_PRO_API_KEY": key}


def download_cmc_global_metrics(config: CoinMarketCapGlobalConfig, force: bool = False) -> Path:
    """Download CoinMarketCap global metrics (dominance, total cap, volume)."""
    csv_path = _cmc_global_output_path(config.convert)
    if csv_path.exists() and not force:
        return csv_path

    headers = _coinmarketcap_headers(config.api_key)
    params = {"convert": config.convert}
    response = requests.get(
        "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest",
        headers=headers,
        params=params,
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"CoinMarketCap global metrics request failed ({response.status_code}): {response.text}"
        )

    payload = response.json()
    status = payload.get("status", {})
    data = payload.get("data")
    if not data:
        raise ValueError("No global metrics returned from CoinMarketCap.")

    quote = data.get("quote", {}).get(config.convert, {})
    flat_data = {k: v for k, v in data.items() if k != "quote"}
    flat_quote = {f"quote_{k}": v for k, v in quote.items()}
    record = {
        **flat_data,
        **flat_quote,
        "timestamp": status.get("timestamp"),
    }
    df = pd.DataFrame([record])
    df["date"] = pd.to_datetime(df["timestamp"])
    df.to_csv(csv_path, index=False)
    return csv_path


def load_cmc_global_metrics(convert: str = "USD") -> pd.DataFrame:
    csv_path = _cmc_global_output_path(convert)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Fetch data with download_cmc_global_metrics first."
        )
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in df.columns:
        df["date"] = _strip_timezone(df["date"])
    return df


def download_cmc_asset_quotes(config: CoinMarketCapAssetConfig, force: bool = False) -> Path:
    """Download latest CoinMarketCap quotes for selected symbols."""
    csv_path = _cmc_asset_output_path(config.symbols, config.convert)
    if csv_path.exists() and not force:
        return csv_path

    headers = _coinmarketcap_headers(config.api_key)
    params = {
        "symbol": ",".join(config.symbols),
        "convert": config.convert,
    }
    response = requests.get(
        "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
        headers=headers,
        params=params,
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"CoinMarketCap quotes request failed ({response.status_code}): {response.text}"
        )

    payload = response.json()
    status = payload.get("status", {})
    data = payload.get("data", {})
    if not data:
        raise ValueError("No quotes returned from CoinMarketCap.")

    rows = []
    fallback_ts = status.get("timestamp")
    for symbol, entry in data.items():
        quote = entry.get("quote", {}).get(config.convert, {})
        row = {
            "symbol": symbol,
            "name": entry.get("name"),
            "slug": entry.get("slug"),
            "last_updated": entry.get("last_updated") or quote.get("last_updated") or fallback_ts,
            "circulating_supply": entry.get("circulating_supply"),
            "total_supply": entry.get("total_supply"),
            "max_supply": entry.get("max_supply"),
            "cmc_rank": entry.get("cmc_rank"),
        }
        row.update({f"quote_{k}": v for k, v in quote.items()})
        rows.append(row)

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["last_updated"])
    df.sort_values("date", inplace=True)
    df.to_csv(csv_path, index=False)
    return csv_path


def load_cmc_asset_quotes(symbols: Sequence[str], convert: str = "USD") -> pd.DataFrame:
    csv_path = _cmc_asset_output_path(symbols, convert)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Fetch data with download_cmc_asset_quotes first."
        )
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in df.columns:
        df["date"] = _strip_timezone(df["date"])
    return df


def download_okx_candles(config: OkxCandlesConfig, force: bool = False) -> Path:
    """Download candlestick data from OKX (used as BTC dominance proxy)."""
    csv_path = ensure_data_dir() / f"{config.inst_id.lower()}_{config.bar.lower()}_okx.csv"
    if csv_path.exists() and not force:
        return csv_path

    params: Dict[str, Any] = {
        "instId": config.inst_id.upper(),
        "bar": config.bar,
        "limit": config.limit,
    }

    response = requests.get("https://www.okx.com/api/v5/market/candles", params=params, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"OKX request failed ({response.status_code}): {response.text}"
        )

    payload = response.json()
    data = payload.get("data", [])
    if not data:
        raise ValueError(f"No candle data returned for {config.inst_id}")

    df = pd.DataFrame(
        data,
        columns=[
            "ts",
            "open",
            "high",
            "low",
            "close",
            "volume_base",
            "volume_quote",
            "volume_quote_currency",
            "confirm",
        ],
    )
    df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
    df.dropna(subset=["ts"], inplace=True)
    df["date"] = pd.to_datetime(df["ts"], unit="ms")
    numeric_cols = ["open", "high", "low", "close", "volume_base"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df[["date"] + numeric_cols]
    df.sort_values("date", inplace=True)
    df.to_csv(csv_path, index=False)
    return csv_path


def load_okx_candles(inst_id: str, bar: str = "1D") -> pd.DataFrame:
    """Load cached OKX candlestick data."""
    csv_path = ensure_data_dir() / f"{inst_id.lower()}_{bar.lower()}_okx.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Fetch data with download_okx_candles first."
        )
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in df.columns:
        df["date"] = _strip_timezone(df["date"])
    return df
