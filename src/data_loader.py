"""Utilities for fetching and caching cryptocurrency datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests
import yfinance as yf
from pandas.api.types import is_datetime64tz_dtype


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


def _price_output_path(symbol: str, interval: str) -> Path:
    slug = symbol.lower().replace("/", "-")
    return ensure_data_dir() / f"{slug}_{interval}.csv"


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
class OkxCandlesConfig:
    """Configuration for fetching OKX candlestick data."""

    inst_id: str
    bar: str = "1D"
    limit: int = 200


def download_price_history(config: DownloadConfig, force: bool = False) -> Path:
    """Download historical price data for a single symbol via yfinance."""
    csv_path = _price_output_path(config.symbol, config.interval)
    if csv_path.exists() and not force:
        return csv_path

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
    data.reset_index().to_csv(csv_path, index=False)
    return csv_path


def download_price_histories(configs: list[DownloadConfig], force: bool = False) -> Dict[str, Path]:
    """Batch download helper returning symbol -> cached CSV path."""
    return {cfg.symbol: download_price_history(cfg, force=force) for cfg in configs}


def load_history(symbol: str, interval: str = "1d") -> pd.DataFrame:
    csv_path = _price_output_path(symbol, interval)
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found. Fetch data with download_price_history first.")
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in df.columns:
        df["date"] = _strip_timezone(df["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def download_okx_candles(config: OkxCandlesConfig, force: bool = False) -> Path:
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
    csv_path = ensure_data_dir() / f"{inst_id.lower()}_{bar.lower()}_okx.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Fetch data with download_okx_candles first."
        )
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in df.columns:
        df["date"] = _strip_timezone(df["date"])
    return df
