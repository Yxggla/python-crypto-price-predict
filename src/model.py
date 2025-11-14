"""Baseline forecasting models for cryptocurrency prices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA


@dataclass
class LinearRegressionModel:
    regressor: LinearRegression
    feature_columns: Tuple[str, ...]
    horizon: int
    windows: Tuple[int, ...]


def _feature_engineering(df: pd.DataFrame, windows: Iterable[int]) -> pd.DataFrame:
    """Generate lagged price, return, and moving-average features."""
    features = pd.DataFrame(index=df.index)
    returns = df["Close"].pct_change()

    lag_windows = sorted(set(windows) | {1, 2, 3})
    for lag in lag_windows:
        features[f"close_lag_{lag}"] = df["Close"].shift(lag)
        features[f"return_lag_{lag}"] = returns.shift(lag)

    for window in windows:
        ma = df["Close"].rolling(window).mean()
        features[f"ma_ratio_{window}"] = ma / df["Close"] - 1
        vol = returns.rolling(window, min_periods=window).std(ddof=0)
        features[f"vol_window_{window}"] = vol.fillna(0.0)

    if "Volume" in df.columns:
        features["volume_change"] = df["Volume"].pct_change()

    return features


def prepare_supervised(
    df: pd.DataFrame, horizon: int = 1, windows: Iterable[int] = (1, 7, 30)
) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare supervised learning dataset for the close price."""
    engineered = _feature_engineering(df, windows)
    target = df["Close"].shift(-horizon)
    dataset = pd.concat([engineered, target.rename("target")], axis=1)
    dataset = dataset.dropna()
    X = dataset.drop(columns="target")
    y = dataset["target"]
    return X, y


def train_linear_regression(
    df: pd.DataFrame, horizon: int = 1, windows: Iterable[int] = (1, 7, 30)
) -> Tuple[LinearRegressionModel, dict]:
    """Fit a linear regression baseline and return metrics on the training data."""
    X, y = prepare_supervised(df, horizon, windows)
    regressor = LinearRegression()
    regressor.fit(X, y)
    predictions = regressor.predict(X)
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y, predictions))),
        "mae": float(mean_absolute_error(y, predictions)),
    }
    return LinearRegressionModel(regressor, tuple(X.columns), horizon, tuple(windows)), metrics


def predict_linear_regression(model: LinearRegressionModel, df: pd.DataFrame) -> pd.Series:
    """Generate predictions for the provided dataframe."""
    X, _ = prepare_supervised(df, model.horizon, model.windows)
    X = X.reindex(columns=model.feature_columns).dropna()
    raw_pred = pd.Series(model.regressor.predict(X), index=X.index, name="prediction")
    if "date" in df.columns:
        date_index = pd.DatetimeIndex(df.loc[raw_pred.index, "date"])
        raw_pred.index = date_index
    return raw_pred


def fit_arima(df: pd.DataFrame, order: Tuple[int, int, int] = (5, 1, 0)):
    """Train a simple ARIMA model on the closing price."""
    model = ARIMA(df["Close"], order=order)
    return model.fit()


def forecast_linear_regression(
    model: LinearRegressionModel,
    df: pd.DataFrame,
    steps: int = 7,
) -> pd.Series:
    """Iteratively forecast future closing prices using the trained linear model."""

    if "date" not in df.columns:
        raise KeyError("Dataframe must contain 'date' column for forecasting.")

    working = df.copy().reset_index(drop=True)
    forecasts = []

    for _ in range(steps):
        base_row = working.iloc[[-1]].copy()
        next_date = base_row["date"].iloc[0] + pd.Timedelta(days=1)
        base_row["date"] = next_date
        for col in ("Open", "High", "Low", "Close"):
            if col in base_row.columns:
                base_row[col] = working["Close"].iloc[-1]
        if "Volume" in base_row.columns:
            base_row["Volume"] = working.get("Volume", pd.Series([0])).iloc[-1]

        working = pd.concat([working, base_row], ignore_index=True)

        features = _feature_engineering(working, model.windows)
        row = features.iloc[[-1]].reindex(columns=model.feature_columns)
        if row.isna().any().any():
            raise ValueError("Insufficient history to compute forecast features.")

        pred = float(model.regressor.predict(row)[0])
        idx = len(working) - 1
        for col in ("Open", "High", "Low", "Close"):
            if col in working.columns:
                working.at[idx, col] = pred

        forecasts.append((next_date, pred))

    return pd.Series({date: value for date, value in forecasts})
