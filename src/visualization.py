"""Visualization helpers for cryptocurrency analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
from plotly.subplots import make_subplots


def _maybe_save(fig: plt.Figure, save_path: Optional[Path]) -> None:
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")


def plot_price_history(
    df: pd.DataFrame,
    symbol: str,
    ax: Optional[plt.Axes] = None,
    show_volume: bool = True,
    save_path: Optional[Path] = None,
    window: Optional[int] = 90,
) -> plt.Axes:
    """Plot closing price with moving averages and optional volume bars."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 5))
    else:
        fig = ax.figure

    plot_df = df.tail(window).copy() if window else df.copy()

    plot_df["ma7"] = plot_df["Close"].rolling(7).mean()
    plot_df["ma30"] = plot_df["Close"].rolling(30).mean()

    base_line, = ax.plot(plot_df["date"], plot_df["Close"], color="gray", alpha=0.35, linewidth=1)

    trend_mask = (plot_df["Close"] >= plot_df["ma30"]).fillna(False)
    close_up = plot_df["Close"].where(trend_mask)
    close_down = plot_df["Close"].where(~trend_mask)
    ax.plot(plot_df["date"], close_up, color="#2e7d32", linewidth=2, label=f"{symbol} Close (bull)")
    ax.plot(plot_df["date"], close_down, color="#c62828", linewidth=2, label=f"{symbol} Close (bear)")

    ax.plot(plot_df["date"], plot_df["ma7"], label="MA7", color="#1976d2", linestyle="--")
    ax.plot(plot_df["date"], plot_df["ma30"], label="MA30", color="#ffa000", linestyle="--")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.set_title(f"{symbol} price history")

    volume_handles: list[Patch] = []
    if show_volume and "Volume" in plot_df.columns:
        ax2 = ax.twinx()
        up_mask = (plot_df["Close"] >= plot_df["Open"]).fillna(False)
        colors = np.where(up_mask, "#26a69a", "#d32f2f")
        ax2.bar(plot_df["date"], plot_df["Volume"], alpha=0.28, color=colors, label="Volume")
        ax2.set_ylabel("Volume (M)")
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{val/1e6:.0f}M"))
        volume_handles = [
            Patch(facecolor="#26a69a", alpha=0.4, label="Volume↑ (Close ≥ Open)"),
            Patch(facecolor="#d32f2f", alpha=0.4, label="Volume↓ (Close < Open)"),
        ]
        ax2.grid(False)
        ax2.margins(x=0)
        # Ensure line chart stays on top.
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)

    ax.grid(alpha=0.2)

    # Highlight top volume days
    if show_volume and "Volume" in plot_df.columns and not plot_df["Volume"].isna().all():
        top_volume = plot_df.nlargest(3, "Volume")
        for _, row in top_volume.iterrows():
            ax.axvspan(
                row["date"] - pd.Timedelta(days=0.4),
                row["date"] + pd.Timedelta(days=0.4),
                color="#ff7043",
                alpha=0.12,
            )

    # Remove MA crossover arrows per latest request

    handles, labels = ax.get_legend_handles_labels()
    if volume_handles:
        handles.extend(volume_handles)
        labels.extend([h.get_label() for h in volume_handles])
    ax.legend(handles, labels)

    fig.autofmt_xdate()
    _maybe_save(fig, save_path)
    return ax


def plot_indicator_panel(
    df: pd.DataFrame,
    symbol: str,
    save_path: Optional[Path] = None,
    window: int = 120,
    summary_text: Optional[str] = None,
) -> None:
    """Create a multi-panel chart that explains each derived signal."""

    required_cols = {"Close", "ma_7", "ma_30", "rolling_max_drawdown", "rolling_sharpe", "vol_regime"}
    missing = required_cols - set(df.columns)
    if missing:
        raise KeyError(f"plot_indicator_panel requires missing columns: {', '.join(sorted(missing))}")

    panel_df = df.tail(window).copy() if window else df.copy()

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"{symbol} – Trend & Risk Signals", fontsize=14)

    # ----- Panel 1: Price with volatility regime shading -----
    ax_price = axes[0]
    regime_colors = {"low": "#e0f7fa", "medium": "#fff9c4", "high": "#ffebee"}
    for regime, color in regime_colors.items():
        mask = panel_df["vol_regime"] == regime
        if mask.any():
            ax_price.fill_between(
                panel_df.loc[mask, "date"],
                panel_df.loc[mask, "Close"].min(),
                panel_df.loc[mask, "Close"].max(),
                color=color,
                alpha=0.2,
                label=f"{regime.title()} volatility",
            )

    ax_price.plot(panel_df["date"], panel_df["Close"], color="#424242", label="Close")
    ax_price.plot(panel_df["date"], panel_df["ma_7"], linestyle="--", color="#1976d2", label="MA7")
    ax_price.plot(panel_df["date"], panel_df["ma_30"], linestyle="--", color="#ffa000", label="MA30")
    ax_price.set_ylabel("Price (USD)")
    ax_price.set_title("Price + Volatility regime (shaded background)")
    ax_price.legend(loc="upper left", ncol=2, fontsize=9)

    # ----- Panel 2: Rolling max drawdown -----
    ax_dd = axes[1]
    dd_pct = panel_df["rolling_max_drawdown"] * 100
    ax_dd.fill_between(panel_df["date"], dd_pct, 0, color="#ef5350", alpha=0.3)
    ax_dd.plot(panel_df["date"], dd_pct, color="#b71c1c", linewidth=1.5)
    ax_dd.set_ylabel("Drawdown (%)")
    ax_dd.set_title("Rolling max drawdown – how deep the recent sell-off reached")
    ax_dd.set_ylim(min(dd_pct.min() * 1.2, -5), 2)
    ax_dd.grid(alpha=0.3)

    # ----- Panel 3: Rolling Sharpe ratio -----
    ax_sharpe = axes[2]
    ax_sharpe.plot(panel_df["date"], panel_df["rolling_sharpe"], color="#2e7d32", linewidth=1.5)
    ax_sharpe.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax_sharpe.set_ylabel("Sharpe (annualized)")
    ax_sharpe.set_title("Rolling Sharpe – risk-adjusted momentum")
    ax_sharpe.set_xlabel("Date")
    ax_sharpe.grid(alpha=0.3)

    fig.autofmt_xdate()
    if summary_text:
        fig.text(0.02, 0.01, summary_text, fontsize=9, ha="left", va="bottom", family="monospace")
        fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    else:
        fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)


def kline_chart(df: pd.DataFrame, symbol: str, show_volume: bool = True) -> go.Figure:
    """Create a polished candlestick chart with optional volume bars."""

    include_volume = show_volume and "Volume" in df.columns
    rows = 2 if include_volume else 1
    row_heights = [0.74, 0.26] if include_volume else [1]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        specs=[[{"secondary_y": False}] for _ in range(rows)],
    )

    change = df["Close"] - df["Open"]
    change_pct = (change / df["Open"]) * 100
    hover_text = [
        (
            f"<b>{pd.to_datetime(date):%Y-%m-%d}</b><br>"
            f"Open: {open_:.2f}<br>High: {high:.2f}<br>Low: {low:.2f}<br>Close: {close:.2f}<br>"
            f"Change: {chg:+.2f} ({pct:+.2f}%)"
        )
        for date, open_, high, low, close, chg, pct in zip(
            df["date"], df["Open"], df["High"], df["Low"], df["Close"], change, change_pct
        )
    ]

    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=symbol,
            increasing_line_color="#26a69a",
            increasing_fillcolor="rgba(38, 166, 154, 0.4)",
            decreasing_line_color="#ef5350",
            decreasing_fillcolor="rgba(239, 83, 80, 0.4)",
            line_width=1.2,
            hovertext=hover_text,
            hoverinfo="text",
        ),
        row=1,
        col=1,
    )

    if include_volume:
        colors = ["#26a69a" if close >= open_ else "#ef5350" for open_, close in zip(df["Open"], df["Close"])]
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["Volume"],
                marker_color=colors,
                name="Volume",
                opacity=0.55,
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        title=f"{symbol} candlestick chart",
        margin=dict(l=40, r=20, t=60, b=40),
        showlegend=False,
    )

    for row in range(1, rows + 1):
        axis_kwargs = dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.08)",
            showspikes=True,
            spikemode="across",
            spikedash="solid",
            spikesnap="cursor",
            spikecolor="rgba(0,0,0,0.4)",
            spikethickness=1,
        )
        if row == rows:
            axis_kwargs["rangeslider"] = dict(visible=False)
        fig.update_xaxes(row=row, col=1, **axis_kwargs)

    fig.update_yaxes(
        title_text="Price (USD)",
        showline=True,
        linecolor="rgba(0,0,0,0.3)",
        mirror=True,
        row=1,
        col=1,
    )

    if include_volume:
        fig.update_yaxes(
            title_text="Volume",
            showgrid=False,
            rangemode="tozero",
            row=2,
            col=1,
        )

    return fig


def plot_actual_vs_predicted(
    actual: pd.Series,
    predicted: pd.Series,
    symbol: str,
    ax: Optional[plt.Axes] = None,
    save_path: Optional[Path] = None,
) -> plt.Axes:
    """Plot actual vs predicted closing prices on the same axes."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 4))
    else:
        fig = ax.figure

    aligned_actual = actual.loc[predicted.index]
    ax.plot(aligned_actual.index, aligned_actual.values, label="Actual", color="tab:blue")
    ax.plot(predicted.index, predicted.values, label="Predicted", color="tab:orange", linestyle="--")
    ax.fill_between(
        predicted.index,
        aligned_actual.values,
        predicted.values,
        color="tab:orange",
        alpha=0.15,
        label="Error band",
    )
    ax.set_title(f"{symbol} actual vs predicted closing price")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.autofmt_xdate()
    _maybe_save(fig, save_path)
    return ax
