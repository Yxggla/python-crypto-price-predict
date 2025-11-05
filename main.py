"""Entry point for running the cryptocurrency analytics workflow."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.analysis import pairwise_correlation, summarize_volatility
from src.data_loader import DownloadConfig, download_price_history, load_history
from src.model import predict_linear_regression, train_linear_regression
from src.visualization import plot_actual_vs_predicted, plot_price_history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cryptocurrency Trend Analysis and Prediction")
    parser.add_argument("--symbols", nargs="+", default=["BTC-USD", "ETH-USD"], help="Ticker symbols to download")
    parser.add_argument("--days", type=int, default=365, help="Number of days of history to fetch")
    parser.add_argument("--interval", default="1d", help="Sampling interval for the price series")
    parser.add_argument("--force", action="store_true", help="Redownload existing CSV files")
    parser.add_argument("--save-figures", action="store_true", help="Persist generated charts to the figures/ directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)
    figures_dir = Path("figures") if args.save_figures else None
    if figures_dir:
        figures_dir.mkdir(parents=True, exist_ok=True)

    datasets = {}
    for symbol in args.symbols:
        csv_path = download_price_history(
            DownloadConfig(symbol=symbol, start=start_date.isoformat(), end=end_date.isoformat(), interval=args.interval),
            force=args.force,
        )
        df = load_history(symbol, args.interval)
        datasets[symbol] = df
        print(f"Loaded {len(df)} rows for {symbol} from {csv_path}")
        save_path = figures_dir / f"{symbol.lower()}_price.png" if figures_dir else None
        plot_price_history(df, symbol, save_path=save_path)
        vol = summarize_volatility(df)
        print(f"{symbol} latest volatility snapshot:")
        print(vol[["date", "Close", "rolling_volatility"]].tail())

    if len(datasets) >= 2:
        corr = pairwise_correlation(datasets)
        print("Correlation matrix:")
        print(corr)

    # Example model training on the first symbol.
    first_symbol = args.symbols[0]
    model, metrics = train_linear_regression(datasets[first_symbol])
    predictions = predict_linear_regression(model, datasets[first_symbol])
    actual_series = datasets[first_symbol].set_index("date")["Close"]
    summary = pd.DataFrame({"actual": actual_series.loc[predictions.index], "predicted": predictions})
    save_path = figures_dir / f"{first_symbol.lower()}_predictions.png" if figures_dir else None
    plot_actual_vs_predicted(actual_series, predictions, first_symbol, save_path=save_path)
    print("Linear regression training metrics:", metrics)
    print(summary.tail())
    plt.show()


if __name__ == "__main__":
    main()
