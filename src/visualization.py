"""Visualization helpers for cryptocurrency analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go


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
) -> plt.Axes:
    """Plot closing price with moving averages and optional volume bars."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 5))
    else:
        fig = ax.figure

    ax.plot(df["date"], df["Close"], label=f"{symbol} Close")
    for window in (7, 30):
        ma = df["Close"].rolling(window).mean()
        ax.plot(df["date"], ma, label=f"MA{window}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    ax.set_title(f"{symbol} price history")

    if show_volume and "Volume" in df.columns:
        ax2 = ax.twinx()
        ax2.bar(df["date"], df["Volume"], alpha=0.2, color="tab:gray", label="Volume")
        ax2.set_ylabel("Volume")
        ax2.grid(False)
        ax2.margins(x=0)
        # Ensure line chart stays on top.
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)

    ax.grid(alpha=0.2)
    fig.autofmt_xdate()
    _maybe_save(fig, save_path)
    return ax


def kline_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Create an interactive Japanese candlestick chart."""
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=symbol,
            )
        ]
    )
    fig.update_layout(title=f"{symbol} candlestick chart", xaxis_title="Date", yaxis_title="Price (USD)")
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
