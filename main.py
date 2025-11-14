"""Entry point for running the cryptocurrency analytics workflow."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd

from src.analysis import pairwise_correlation, summarize_volatility, period_return
from src.data_loader import (
    DownloadConfig,
    MacroSeriesConfig,
    OkxCandlesConfig,
    download_macro_series,
    download_okx_candles,
    download_price_history,
    load_history,
    load_macro_series,
    load_okx_candles,
)
from src.model import predict_linear_regression, train_linear_regression
from src.visualization import plot_actual_vs_predicted, plot_price_history, kline_chart


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cryptocurrency Trend Analysis and Prediction")
    parser.add_argument("--symbols", nargs="+", default=["BTC-USD", "ETH-USD"], help="yfinance ticker symbols to download")
    parser.add_argument("--days", type=int, default=365, help="Number of days of history to fetch")
    parser.add_argument("--interval", default="1d", help="Sampling interval for the price series")
    parser.add_argument("--force", action="store_true", help="Redownload existing CSV files")

    parser.add_argument(
        "--dominance-inst-id",
        default="BTC-USDT",
        help="OKX instrument ID used for dominance proxy candles (set empty string to skip).",
    )
    parser.add_argument(
        "--macro-series",
        nargs="+",
        default=["FEDFUNDS"],
        help="FRED series IDs to download.",
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
    dominance_inst_id: Optional[str],
    dominance_bar: str,
    macro_series: List[str],
) -> None:
    """Persist cached datasets to an Excel workbook for downstream analysis."""
    export_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(export_path) as writer:
        price_frames = []
        for symbol, df in price_data.items():
            sheet_df = df.copy()
            sheet_df["symbol"] = symbol
            sheet_df["change_abs"] = sheet_df["Close"] - sheet_df["Open"]
            sheet_df["change_pct"] = (sheet_df["change_abs"] / sheet_df["Open"]) * 100
            sheet_df.loc[sheet_df["Open"] == 0, "change_pct"] = pd.NA
            price_frames.append(sheet_df)
        pd.concat(price_frames, ignore_index=True).to_excel(writer, sheet_name="prices", index=False)

        if dominance_path and dominance_inst_id:
            dominance_df = load_okx_candles(inst_id=dominance_inst_id, bar=dominance_bar)
            dominance_df.to_excel(writer, sheet_name="dominance", index=False)

        for series_id in macro_series:
            macro_df = load_macro_series(series_id)
            macro_df.to_excel(writer, sheet_name=f"macro_{series_id}", index=False)

    print(f"[export] Consolidated workbook written to {export_path}")


def main() -> None:
    args = parse_args()
    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)
    figures_dir = Path("figures")
    figures_dir.mkdir(parents=True, exist_ok=True)

    macro_series = args.macro_series

    datasets: Dict[str, pd.DataFrame] = {}
    performance_rows = []

    for symbol in args.symbols:
        csv_path = download_price_history(
            DownloadConfig(symbol=symbol, start=start_date, end=end_date, interval=args.interval),
            force=args.force,
        )
        df = load_history(symbol, args.interval).copy()
        df["symbol"] = symbol
        df["change_abs"] = df["Close"] - df["Open"]
        df["change_pct"] = (df["change_abs"] / df["Open"]) * 100
        df.loc[df["Open"] == 0, "change_pct"] = pd.NA
        df.to_csv(csv_path, index=False)
        datasets[symbol] = df
        print(f"[data] Cached {symbol} price history at {csv_path}")

        save_path = figures_dir / f"{symbol.lower()}_price.png"
        plot_price_history(df, symbol, save_path=save_path, window=180)

        vol = summarize_volatility(df)
        print(f"{symbol} latest volatility snapshot:")
        print(vol[["date", "Close", "rolling_volatility"]].tail())

        period_stats = period_return(df)
        stats_row = {"symbol": symbol, **period_stats.to_dict()}
        performance_rows.append(stats_row)
        pct = stats_row["pct_change"]
        print(
            f"[performance] {symbol}: {stats_row['start_date']} open {stats_row['open_price']:.2f} -> "
            f"{stats_row['end_date']} close {stats_row['close_price']:.2f} ({pct:+.2f}%)"
        )

        kline_fig = kline_chart(df, symbol)
        html_path = figures_dir / f"{symbol.lower()}_kline.html"
        kline_fig.write_html(html_path)
        print(f"[fig] Saved Plotly k-line to {html_path}")
        kline_fig.show()

    if len(datasets) >= 2:
        corr = pairwise_correlation(datasets)
        print("Correlation matrix:")
        print(corr)

    if performance_rows:
        performance_df = pd.DataFrame(performance_rows)
        print("\nPeriod performance (% change from first open to last close):")
        print(performance_df[["symbol", "open_price", "close_price", "pct_change"]])

    dominance_path: Optional[Path] = None
    if args.dominance_inst_id:
        try:
            dominance_path = download_okx_candles(
                OkxCandlesConfig(
                    inst_id=args.dominance_inst_id,
                    bar="1D",
                    limit=min(max(args.days, 200), 1000),
                ),
                force=args.force,
            )
            print(f"[data] Cached {args.dominance_inst_id} OKX candles at {dominance_path}")
        except RuntimeError as exc:
            dominance_path = None
            print(f"[warn] OKX dominance download skipped: {exc}")

    if macro_series:
        for series_id in macro_series:
            macro_path = download_macro_series(
                MacroSeriesConfig(series_id=series_id, start=start_date, end=end_date),
                force=args.force,
            )
            print(f"[data] Cached macro series {series_id} at {macro_path}")

    # Example model training on the first symbol.
    first_symbol = args.symbols[0]
    model, metrics = train_linear_regression(datasets[first_symbol])
    predictions = predict_linear_regression(model, datasets[first_symbol])
    actual_series = datasets[first_symbol].set_index("date")["Close"]
    summary = pd.DataFrame({"actual": actual_series.loc[predictions.index], "predicted": predictions})
    save_path = figures_dir / f"{first_symbol.lower()}_predictions.png"
    plot_actual_vs_predicted(actual_series, predictions, first_symbol, save_path=save_path)
    print("Linear regression training metrics:", metrics)
    print(summary.tail())

    if args.export_xlsx:
        export_workbook(
            export_path=Path(args.export_xlsx),
            price_data=datasets,
            dominance_path=dominance_path,
            dominance_inst_id=args.dominance_inst_id,
            dominance_bar="1D",
            macro_series=macro_series,
        )

    plt.show()


if __name__ == "__main__":
    main()
