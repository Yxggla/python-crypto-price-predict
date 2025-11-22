
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
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
    end: Optional[date | datetime | str] = field(default_factory=date.today)
    interval: str = "1d"

def download_price_history(config: DownloadConfig, force: bool = False) -> Path:
    """Download historical price data for a single symbol via yfinance.

    This always fetches fresh data and overwrites any existing CSV.
    """
    csv_path = _price_output_path(config.symbol, config.interval)

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
