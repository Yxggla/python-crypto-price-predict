"""Entry point for running the cryptocurrency analytics workflow."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd

from src.analysis import (
    pairwise_correlation,
    summarize_volatility,
    period_return,
    rolling_max_drawdown,
    rolling_sharpe_ratio,
    btc_eth_spread_zscore,
    volatility_regime,
    ma_crossover_signals,
)
from src.data_loader import (
    DownloadConfig,
    OkxCandlesConfig,
    download_okx_candles,
    download_price_history,
    load_history,
    load_okx_candles,
)
from src.model import predict_linear_regression, train_linear_regression, forecast_linear_regression
from src.visualization import plot_actual_vs_predicted, plot_price_history, plot_indicator_panel, plot_recent_forecast, kline_chart


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

    print(f"[export] Consolidated workbook written to {export_path}")


def main() -> None:
    args = parse_args()
    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)
    figures_dir = Path("figures")
    figures_dir.mkdir(parents=True, exist_ok=True)

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

        df = summarize_volatility(df)
        df = rolling_max_drawdown(df, window=180)
        df = rolling_sharpe_ratio(df, window=180)
        df = ma_crossover_signals(df, fast=7, slow=30)
        df = volatility_regime(df, window=30)

        df.to_csv(csv_path, index=False)
        datasets[symbol] = df
        print(f"[data] Cached {symbol} price history at {csv_path}")

        save_path = figures_dir / f"{symbol.lower()}_price.png"
        plot_price_history(df, symbol, save_path=save_path, window=90)

        print(f"{symbol} latest volatility snapshot:")
        print(df[["date", "Close", "rolling_volatility"]].tail())

        latest = df.iloc[-1]
        dd_val = latest.get("rolling_max_drawdown")
        sharpe_val = latest.get("rolling_sharpe")
        regime = latest.get("vol_regime", "unknown")
        dd_pct = f"{dd_val * 100:.2f}%" if pd.notna(dd_val) else "n/a"
        sharpe_fmt = f"{sharpe_val:.2f}" if pd.notna(sharpe_val) else "n/a"
        print(f"[signal] {symbol}: regime={regime}, rolling_max_drawdown={dd_pct}, rolling_sharpe={sharpe_fmt}")

        ma_state = latest.get("ma_signal", 0)
        ma_label = "bullish" if ma_state > 0 else "bearish" if ma_state < 0 else "neutral"
        last_cross = df.loc[df["ma_crossover"] != 0].tail(1)
        cross_msg = "none"
        if not last_cross.empty:
            cross_row = last_cross.iloc[-1]
            direction = "bullish" if cross_row["ma_crossover"] > 0 else "bearish"
            cross_msg = f"{direction} on {cross_row['date'].date()}"
        print(f"[ma] {symbol}: current state {ma_label}, last crossover {cross_msg}")

        # Simple textual recommendation
        dd_numeric = dd_val if pd.notna(dd_val) else 0.0
        sharpe_numeric = sharpe_val if pd.notna(sharpe_val) else 0.0
        action = "wait"
        reasons = []
        if ma_state > 0:
            reasons.append("MA7 above MA30")
        elif ma_state < 0:
            reasons.append("MA7 below MA30")
        if sharpe_numeric > 0:
            reasons.append("positive rolling Sharpe")
        elif sharpe_numeric < 0:
            reasons.append("negative rolling Sharpe")
        if regime == "high":
            reasons.append("volatility high")
        elif regime == "low":
            reasons.append("volatility calm")
        if dd_numeric < -0.1:
            reasons.append("deep recent drawdown")

        if ma_state > 0 and sharpe_numeric > 0 and regime != "high":
            action = "lean long"
        elif ma_state < 0 and sharpe_numeric < 0:
            action = "lean short"
        elif regime == "high" and abs(dd_numeric) > 0.08:
            action = "stand aside"

        reason_text = "; ".join(reasons) if reasons else "insufficient data"
        summary_text = f"Recommendation: {action} | Reasons: {reason_text}"
        print(f"[summary] {symbol}: {summary_text}")

        indicator_path = figures_dir / f"{symbol.lower()}_indicator_panel.png"
        try:
            panel_caption = f"{symbol} -> {action.upper()}\n" + "\n".join(f"• {r}" for r in (reasons or ["insufficient data"]))
            plot_indicator_panel(df, symbol, save_path=indicator_path, window=120, summary_text=panel_caption)
            print(f"[fig] Saved indicator panel to {indicator_path}")
        except KeyError as exc:
            print(f"[warn] Indicator panel skipped for {symbol}: {exc}")

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

    if {"BTC-USD", "ETH-USD"}.issubset(datasets.keys()):
        spread_df = btc_eth_spread_zscore(datasets["BTC-USD"], datasets["ETH-USD"], window=30)
        latest_spread = spread_df.iloc[-1]
        print(
            f"[spread] BTC-ETH spread {latest_spread['spread']:.2f} USD | z-score {latest_spread['spread_zscore']:.2f}"
            f" on {latest_spread['date'].date()}"
        )

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

    for symbol, data in datasets.items():
        model, metrics = train_linear_regression(data)
        predictions = predict_linear_regression(model, data)
        actual_series = data.set_index("date")["Close"]
        summary = pd.DataFrame({"actual": actual_series.loc[predictions.index], "predicted": predictions})
        save_path = figures_dir / f"{symbol.lower()}_predictions.png"
        plot_actual_vs_predicted(actual_series, predictions, symbol, save_path=save_path)
        print(f"Linear regression training metrics for {symbol}:", metrics)
        print(summary.tail())

        try:
            future_series = forecast_linear_regression(model, data, steps=7)
            forecast_path = figures_dir / f"{symbol.lower()}_forecast_next7.png"
            plot_recent_forecast(data, future_series, symbol, save_path=forecast_path, window=30)
            print(f"[fig] Saved 30d + 7d forecast view to {forecast_path}")
        except ValueError as exc:
            print(f"[warn] Forecast skipped for {symbol}: {exc}")

    if args.export_xlsx:
        export_workbook(
            export_path=Path(args.export_xlsx),
            price_data=datasets,
            dominance_path=dominance_path,
            dominance_inst_id=args.dominance_inst_id,
            dominance_bar="1D",
        )

    plt.show()


if __name__ == "__main__":
    main()
