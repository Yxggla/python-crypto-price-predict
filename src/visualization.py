"""Visualization helpers for cryptocurrency analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
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

    hover_text = [
        (
            f"<b>{pd.to_datetime(date):%Y-%m-%d}</b><br>"
            f"Open: {open_:.2f}<br>High: {high:.2f}<br>Low: {low:.2f}<br>Close: {close:.2f}"
        )
        for date, open_, high, low, close in zip(df["date"], df["Open"], df["High"], df["Low"], df["Close"])
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
