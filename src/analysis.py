"""Core analytics for cryptocurrency time series."""

from __future__ import annotations

from typing import Dict

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
