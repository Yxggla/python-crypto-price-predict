from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtest import export_backtest_excel, ma_crossover_backtest, summarize_trades
from src.data_loader import load_history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MA7/MA30 crossover backtest CLI")
    parser.add_argument("--symbols", nargs="+", help="多个符号，空格分隔，例如 BTC-USD ETH-USD")
    parser.add_argument("--symbol", nargs="+", help="单个或多个符号（兼容旧参数）")
    parser.add_argument("--interval", default="1d", help="Sampling interval for the cached CSV")
    parser.add_argument("--fast", type=int, default=7, help="Fast MA length")
    parser.add_argument("--slow", type=int, default=30, help="Slow MA length")
    parser.add_argument("--stake", type=float, default=10.0, help="Capital per position")
    parser.add_argument("--leverage", type=float, default=2.0, help="Leverage multiplier")
    parser.add_argument("--fee-rate", type=float, default=0.001, help="单边手续费率（默认千分之一）")
    parser.add_argument("--days", type=int, default=2000, help="Number of most recent rows to backtest")
    parser.add_argument("--export", type=Path, help="Optional Excel export path")
    parser.add_argument("--csv", type=Path, help="Use a CSV path instead of cached symbol history")
    parser.add_argument("--compound", action="store_true", help="开启复利（默认关闭，固定单笔上限为 stake，若本金不足则用剩余本金）")
    parser.set_defaults(compound=False)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    symbols: list[str] = []
    if args.symbols:
        symbols = args.symbols
    elif args.symbol:
        symbols = args.symbol
    else:
        symbols = ["BTC-USD"]

    # 展平可能的嵌套列表（兼容 --symbol 传多值）
    flat_symbols = []
    for s in symbols:
        if isinstance(s, (list, tuple)):
            flat_symbols.extend(list(s))
        else:
            flat_symbols.append(s)
    symbols = flat_symbols

    export_paths = []

    for sym in symbols:
        if args.csv:
            df = pd.read_csv(args.csv, parse_dates=["date"])
        else:
            df = load_history(sym, args.interval)

        if args.days:
            df = df.tail(args.days)

        trades = ma_crossover_backtest(
            df=df,
            fast=args.fast,
            slow=args.slow,
            stake=args.stake,
            leverage=args.leverage,
            compound=args.compound,
            fee_rate=args.fee_rate,
        )
        summary = summarize_trades(trades)

        if trades.empty:
            continue

        export_path = args.export
        if not export_path or (len(symbols) > 1 and args.export is None):
            export_dir = Path("exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            symbol_slug = sym.lower().replace("/", "-")
            export_path = export_dir / f"{symbol_slug}_ma{args.fast}_{args.slow}_backtest.xlsx"

        export_backtest_excel(trades, summary, export_path)
        export_paths.append(export_path)

    return export_paths


if __name__ == "__main__":
    main()
