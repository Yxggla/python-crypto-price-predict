"""Core analytics for cryptocurrency time series."""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd
import numpy as np


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Append logarithmic and simple returns to the dataframe."""
    df = df.copy()
    df["return_simple"] = df["Close"].pct_change()
    df["return_log"] = np.log(df["Close"] / df["Close"].shift(1))
    return df


def summarize_volatility(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Calculate rolling volatility over the provided window length."""
    df = add_returns(df)
    df["rolling_volatility"] = df["return_simple"].rolling(window).std() * (window ** 0.5)
    return df


def pairwise_correlation(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return correlation matrix for closing prices."""
    closes = pd.DataFrame({name: data["Close"] for name, data in datasets.items()})
    return closes.corr()


def period_return(df: pd.DataFrame) -> pd.Series:
    """Return first open, last close, and percentage change over the dataframe."""
    if df.empty:
        raise ValueError("Dataframe is empty; cannot compute period return.")

    start_open = float(df["Open"].iloc[0])
    end_close = float(df["Close"].iloc[-1])
    pct_change = (end_close - start_open) / start_open * 100 if start_open else float("nan")

    return pd.Series(
        {
            "start_date": df["date"].iloc[0],
            "end_date": df["date"].iloc[-1],
            "open_price": start_open,
            "close_price": end_close,
            "pct_change": pct_change,
        }
    )


def rolling_max_drawdown(df: pd.DataFrame, window: int = 90) -> pd.DataFrame:
    """Append rolling drawdown metrics over the specified window."""
    if "Close" not in df.columns:
        raise KeyError("Dataframe must contain 'Close' column for drawdown calculations.")

    result = df.copy()
    rolling_max = result["Close"].rolling(window, min_periods=1).max()
    result["drawdown"] = result["Close"] / rolling_max - 1.0
    result["rolling_max_drawdown"] = result["drawdown"].rolling(window, min_periods=1).min()
    return result


def rolling_sharpe_ratio(df: pd.DataFrame, window: int = 90, periods_per_year: int = 365) -> pd.DataFrame:
    """Append rolling Sharpe ratio based on simple returns."""
    if "return_simple" not in df.columns:
        df = add_returns(df)

    result = df.copy()
    rolling_mean = result["return_simple"].rolling(window, min_periods=1).mean()
    rolling_std = result["return_simple"].rolling(window, min_periods=1).std()
    annualized_factor = np.sqrt(periods_per_year)
    result["rolling_sharpe"] = (rolling_mean / rolling_std) * annualized_factor
    result.loc[rolling_std == 0, "rolling_sharpe"] = np.nan
    return result


def btc_eth_spread_zscore(
    btc_df: pd.DataFrame,
    eth_df: pd.DataFrame,
    window: int = 30,
) -> pd.DataFrame:
    """Compute BTC-ETH close-price spread and z-score over the window."""
    merged = (
        btc_df[["date", "Close"]]
        .rename(columns={"Close": "btc_close"})
        .merge(eth_df[["date", "Close"]].rename(columns={"Close": "eth_close"}), on="date", how="inner")
        .sort_values("date")
        .reset_index(drop=True)
    )
    merged["spread"] = merged["btc_close"] - merged["eth_close"]
    rolling_mean = merged["spread"].rolling(window, min_periods=1).mean()
    rolling_std = merged["spread"].rolling(window, min_periods=1).std()
    merged["spread_zscore"] = (merged["spread"] - rolling_mean) / rolling_std
    merged.loc[rolling_std == 0, "spread_zscore"] = np.nan
    return merged


def volatility_regime(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Classify each row into low/medium/high volatility regimes based on rolling vol quantiles."""
    if "rolling_volatility" not in df.columns:
        vol_df = summarize_volatility(df, window)
    else:
        vol_df = df.copy()

    vol = vol_df["rolling_volatility"].dropna()
    if vol.empty:
        vol_df["vol_regime"] = np.nan
        return vol_df

    q_low = vol.quantile(1 / 3)
    q_high = vol.quantile(2 / 3)

    def regime(value: float) -> str:
        if np.isnan(value):
            return "unknown"
        if value <= q_low:
            return "low"
        if value >= q_high:
            return "high"
        return "medium"

    vol_df["vol_regime"] = vol_df["rolling_volatility"].apply(regime)
    return vol_df


def ma_crossover_signals(
    df: pd.DataFrame,
    fast: int = 7,
    slow: int = 30,
) -> pd.DataFrame:
    """Add moving averages and crossover signal (+1 for bullish, -1 for bearish, 0 otherwise)."""
    result = df.copy()
    result[f"ma_{fast}"] = result["Close"].rolling(fast).mean()
    result[f"ma_{slow}"] = result["Close"].rolling(slow).mean()
    diff = result[f"ma_{fast}"] - result[f"ma_{slow}"]
    signal = np.sign(diff)
    result["ma_signal"] = signal
    result["ma_crossover"] = signal.diff().fillna(0).astype(int)
    return result
