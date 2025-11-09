"""Entry point for running the cryptocurrency analytics workflow."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd

from src.analysis import pairwise_correlation, summarize_volatility
from src.data_loader import (
    BinanceKlinesConfig,
    CoinMarketCapAssetConfig,
    CoinMarketCapGlobalConfig,
    DownloadConfig,
    MacroSeriesConfig,
    download_binance_klines,
    download_cmc_asset_quotes,
    download_cmc_global_metrics,
    download_macro_series,
    download_price_history,
    load_binance_klines,
    load_cmc_asset_quotes,
    load_cmc_global_metrics,
    load_history,
    load_macro_series,
)
from src.model import predict_linear_regression, train_linear_regression
from src.visualization import plot_actual_vs_predicted, plot_price_history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cryptocurrency Trend Analysis and Prediction")
    parser.add_argument("--symbols", nargs="+", default=["BTC-USD", "ETH-USD"], help="Ticker symbols to download")
    parser.add_argument("--days", type=int, default=365, help="Number of days of history to fetch")
    parser.add_argument("--interval", default="1d", help="Sampling interval for the price series")
    parser.add_argument("--force", action="store_true", help="Redownload existing CSV files")
    parser.add_argument("--save-figures", action="store_true", help="Persist generated charts to the figures/ directory")
    parser.add_argument("--quiet", action="store_true", help="Silence verbose dataframe prints")

    parser.add_argument(
        "--dominance-symbol",
        default="BTCDOMUSDT",
        help="Binance symbol used for BTC dominance klines (set empty string to skip).",
    )
    parser.add_argument(
        "--macro-series",
        nargs="+",
        default=["FEDFUNDS"],
        help="FRED series IDs to download (use --macro-series none to skip).",
    )
    parser.add_argument(
        "--cmc-convert",
        default="USD",
        help="Fiat currency for CoinMarketCap global metrics and quotes.",
    )
    parser.add_argument(
        "--skip-cmc",
        action="store_true",
        help="Skip CoinMarketCap downloads even if API key is available.",
    )
    parser.add_argument(
        "--export-xlsx",
        help="Optional path to write a consolidated Excel workbook for downstream analysis.",
    )
    return parser.parse_args()


def export_workbook(
    export_path: Path,
    price_data: Dict[str, pd.DataFrame],
    dominance_path: Optional[Path],
    dominance_symbol: Optional[str],
    dominance_interval: str,
    macro_series: List[str],
    cmc_global_path: Optional[Path],
    cmc_quotes_path: Optional[Path],
    cmc_convert: str,
    cmc_symbols: List[str],
    quiet: bool,
) -> None:
    """Persist cached datasets to an Excel workbook for downstream analysis."""
    export_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(export_path) as writer:
        price_frames = []
        for symbol, df in price_data.items():
            sheet_df = df.copy()
            sheet_df["symbol"] = symbol
            price_frames.append(sheet_df)
        pd.concat(price_frames, ignore_index=True).to_excel(writer, sheet_name="prices", index=False)

        if dominance_path and dominance_symbol:
            dominance_df = load_binance_klines(symbol=dominance_symbol, interval=dominance_interval)
            dominance_df.to_excel(writer, sheet_name="dominance", index=False)

        for series_id in macro_series:
            macro_df = load_macro_series(series_id)
            macro_df.to_excel(writer, sheet_name=f"macro_{series_id}", index=False)

        if cmc_global_path:
            load_cmc_global_metrics(convert=cmc_convert).to_excel(writer, sheet_name="cmc_global", index=False)
        if cmc_quotes_path and cmc_symbols:
            load_cmc_asset_quotes(cmc_symbols, convert=cmc_convert).to_excel(writer, sheet_name="cmc_quotes", index=False)

    if not quiet:
        print(f"[export] Consolidated workbook written to {export_path}")


def main() -> None:
    args = parse_args()
    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)
    figures_dir = Path("figures") if args.save_figures else None
    if figures_dir:
        figures_dir.mkdir(parents=True, exist_ok=True)

    macro_series = [] if args.macro_series == ["none"] else args.macro_series

    datasets: Dict[str, pd.DataFrame] = {}
    for symbol in args.symbols:
        csv_path = download_price_history(
            DownloadConfig(symbol=symbol, start=start_date.isoformat(), end=end_date.isoformat(), interval=args.interval),
            force=args.force,
        )
        df = load_history(symbol, args.interval)
        datasets[symbol] = df
        if not args.quiet:
            print(f"[data] Cached {symbol} price history at {csv_path}")
        save_path = figures_dir / f"{symbol.lower()}_price.png" if figures_dir else None
        plot_price_history(df, symbol, save_path=save_path)
        vol = summarize_volatility(df)
        if not args.quiet:
            print(f"{symbol} latest volatility snapshot:")
            print(vol[["date", "Close", "rolling_volatility"]].tail())

    if len(datasets) >= 2 and not args.quiet:
        corr = pairwise_correlation(datasets)
        print("Correlation matrix:")
        print(corr)

    asset_symbols = sorted({symbol.split("-")[0].upper() for symbol in args.symbols})

    dominance_path: Optional[Path] = None
    if args.dominance_symbol:
        dominance_path = download_binance_klines(
            BinanceKlinesConfig(
                symbol=args.dominance_symbol,
                interval=args.interval,
                start=start_date,
                end=end_date,
            ),
            force=args.force,
        )
        if not args.quiet:
            print(f"[data] Cached {args.dominance_symbol} dominance klines at {dominance_path}")

    if macro_series:
        for series_id in macro_series:
            macro_path = download_macro_series(
                MacroSeriesConfig(series_id=series_id, start=start_date, end=end_date),
                force=args.force,
            )
            if not args.quiet:
                print(f"[data] Cached macro series {series_id} at {macro_path}")

    cmc_global_path: Optional[Path] = None
    cmc_quotes_path: Optional[Path] = None
    if not args.skip_cmc:
        cmc_global_path = download_cmc_global_metrics(CoinMarketCapGlobalConfig(convert=args.cmc_convert))
        cmc_quotes_path = download_cmc_asset_quotes(
            CoinMarketCapAssetConfig(symbols=asset_symbols, convert=args.cmc_convert)
        )
        if not args.quiet:
            print(f"[data] Cached CoinMarketCap global metrics at {cmc_global_path}")
            print(f"[data] Cached CoinMarketCap quotes for {', '.join(asset_symbols)} at {cmc_quotes_path}")

    # Example model training on the first symbol.
    first_symbol = args.symbols[0]
    model, metrics = train_linear_regression(datasets[first_symbol])
    predictions = predict_linear_regression(model, datasets[first_symbol])
    actual_series = datasets[first_symbol].set_index("date")["Close"]
    summary = pd.DataFrame({"actual": actual_series.loc[predictions.index], "predicted": predictions})
    save_path = figures_dir / f"{first_symbol.lower()}_predictions.png" if figures_dir else None
    plot_actual_vs_predicted(actual_series, predictions, first_symbol, save_path=save_path)
    if not args.quiet:
        print("Linear regression training metrics:", metrics)
        print(summary.tail())

    if args.export_xlsx:
        export_workbook(
            export_path=Path(args.export_xlsx),
            price_data=datasets,
            dominance_path=dominance_path,
            dominance_symbol=args.dominance_symbol,
            dominance_interval=args.interval,
            macro_series=macro_series,
            cmc_global_path=cmc_global_path,
            cmc_quotes_path=cmc_quotes_path,
            cmc_convert=args.cmc_convert,
            cmc_symbols=asset_symbols if not args.skip_cmc else [],
            quiet=args.quiet,
        )

    if not args.save_figures:
        plt.show()


if __name__ == "__main__":
    main()
