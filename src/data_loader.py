"""Utilities for fetching and caching cryptocurrency price data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class DownloadConfig:
    symbol: str
    start: str
    end: Optional[str] = None
    interval: str = "1d"


def ensure_data_dir() -> Path:
    """Create the data directory if needed and return its path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _output_path(symbol: str, interval: str) -> Path:
    return ensure_data_dir() / f"{symbol.lower()}_{interval}.csv"


def download_price_history(config: DownloadConfig, force: bool = False) -> Path:
    """Download historical price data and persist it to CSV.

    Returns the path to the cached CSV.
    """
    output_path = _output_path(config.symbol, config.interval)
    if output_path.exists() and not force:
        return output_path

    ticker = yf.Ticker(config.symbol)
    data = ticker.history(start=config.start, end=config.end, interval=config.interval)
    if data.empty:
        raise ValueError(f"No data returned for {config.symbol}")

    data.index.name = "date"
    data.reset_index().to_csv(output_path, index=False)
    return output_path


def load_history(symbol: str, interval: str = "1d") -> pd.DataFrame:
    """Load a cached CSV into a DataFrame."""
    csv_path = _output_path(symbol, interval)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Fetch data with download_price_history first."
        )
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
