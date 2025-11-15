"""CLI helper to mirror yfinance caches with OKX spot candles."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import pandas as pd

# Allow running as `python scripts/cache_okx_prices.py` without PYTHONPATH tweaks.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PROJECT_ROOT))

from src.data_loader import OkxCandlesConfig, download_okx_candles, ensure_data_dir


def parse_overrides(overrides: list[str]) -> Dict[str, str]:
    """Parse symbol=inst_id mappings from CLI."""
    mapping: Dict[str, str] = {}
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid override '{item}'. Use SYMBOL=OKX_INST format, e.g., BTC-USD=BTC-USDT.")
        symbol, inst_id = item.split("=", 1)
        mapping[symbol.strip()] = inst_id.strip()
    return mapping


def default_inst_id(symbol: str) -> str:
    """Convert yfinance symbols (BTC-USD) to OKX inst IDs (BTC-USDT)."""
    if symbol.upper().endswith("-USD"):
        return symbol[:-3] + "USDT"
    return symbol


def normalize_okx_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Rename OKX columns to yfinance-style OHLCV."""
    renamed = df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume_base": "Volume",
        }
    )
    renamed["Adj Close"] = renamed["Close"]
    renamed["Dividends"] = 0.0
    renamed["Stock Splits"] = 0.0
    ordered_cols = [
        "date",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
        "Dividends",
        "Stock Splits",
    ]
    return renamed[ordered_cols]


def cache_from_okx(symbols: list[str], interval: str, bar: str, limit: int, force: bool, overrides: Dict[str, str]) -> None:
    data_dir = ensure_data_dir()
    for symbol in symbols:
        inst_id = overrides.get(symbol, default_inst_id(symbol))
        config = OkxCandlesConfig(inst_id=inst_id, bar=bar, limit=limit)
        okx_path = download_okx_candles(config, force=force)
        df = pd.read_csv(okx_path)
        normalized = normalize_okx_frame(df)
        normalized["symbol"] = symbol

        cache_path = data_dir / f"{symbol.lower()}_{interval}.csv"
        normalized.to_csv(cache_path, index=False)
        print(f"[okx-cache] {symbol} <= {inst_id} candles saved to {cache_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate data/*.csv using OKX instead of yfinance.")
    parser.add_argument("--symbols", nargs="+", required=True, help="yfinance symbols (e.g., BTC-USD ETH-USD)")
    parser.add_argument("--interval", default="1d", help="Interval suffix for cache filename (default: 1d)")
    parser.add_argument("--bar", default="1D", help="OKX bar size, e.g., 1D/1H/4H")
    parser.add_argument("--limit", type=int, default=1000, help="Number of bars to request from OKX")
    parser.add_argument("--force", action="store_true", help="Force refresh OKX download instead of reusing cache")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Symbol-to-OKX mapping, e.g., --override BTC-USD=BTC-USDT (repeatable).",
    )
    args = parser.parse_args()

    overrides = parse_overrides(args.override) if args.override else {}
    cache_from_okx(args.symbols, args.interval, args.bar.upper(), args.limit, args.force, overrides)


if __name__ == "__main__":
    main()
