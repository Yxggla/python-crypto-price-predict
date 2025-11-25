from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from .analysis import ma_crossover_signals


def ma_crossover_backtest(
    df: pd.DataFrame,
    fast: int = 7,
    slow: int = 30,
    stake: float = 10.0,
    leverage: float = 2.0,
    compound: bool = False,
    fee_rate: float = 0.001,
) -> pd.DataFrame:
    """
    Vectorless backtest for a simple MA crossover strategy.

    Rules:
    - When MA_fast > MA_slow -> long with `stake` capital at `leverage`.
    - When MA_fast < MA_slow -> short with `stake` capital at `leverage`.
    - Position flips on the bar where the signal flips; entry/exit uses the same bar's close.
    """
    price_df = df.copy()
    if f"ma_{fast}" not in price_df.columns or f"ma_{slow}" not in price_df.columns or "ma_signal" not in price_df.columns:
        price_df = ma_crossover_signals(price_df, fast=fast, slow=slow)

    price_df = price_df.dropna(subset=[f"ma_{fast}", f"ma_{slow}"]).reset_index(drop=True)

    trades = []
    current_dir: int | None = None
    entry_price: float | None = None
    entry_date: pd.Timestamp | None = None
    entry_ma_fast: float | None = None
    entry_ma_slow: float | None = None
    capital = stake  # 初始本金

    def close_trade(exit_row: pd.Series) -> None:
        nonlocal current_dir, entry_price, entry_date, entry_ma_fast, entry_ma_slow, capital
        if current_dir is None or entry_price is None or entry_date is None:
            return
        exit_date = pd.to_datetime(exit_row["date"])
        exit_price = float(exit_row["Close"])
        exit_ma_f = float(exit_row.get(f"ma_{fast}", np.nan))
        exit_ma_s = float(exit_row.get(f"ma_{slow}", np.nan))

        entry_capital = capital if compound else min(capital, stake)
        if entry_capital <= 0:
            return
        entry_notional = entry_capital * leverage
        quantity = entry_notional / entry_price

        price_return = (exit_price - entry_price) / entry_price
        signed_return = current_dir * price_return
        leveraged_return = signed_return * leverage

        # 毛收益与手续费（进出各收 fee_rate * 名义）
        pnl_gross = entry_capital * leveraged_return
        exit_notional = quantity * exit_price
        fee_entry = fee_rate * entry_notional
        fee_exit = fee_rate * exit_notional
        fee_total = fee_entry + fee_exit
        pnl_net = pnl_gross - fee_total

        capital_after = capital + pnl_net
        capital = capital_after

        trades.append(
            {
                "entry_date": pd.to_datetime(entry_date),
                "exit_date": exit_date,
                "direction": "long" if current_dir > 0 else "short",
                "stake": stake,
                "leverage": leverage,
                "capital_before": entry_capital,
                "capital_after": capital_after if compound else np.nan,
                "fee_entry": fee_entry,
                "fee_exit": fee_exit,
                "fee_total": fee_total,
                "entry_price": entry_price,
                "entry_ma_fast": entry_ma_fast,
                "entry_ma_slow": entry_ma_slow,
                "exit_price": exit_price,
                "exit_ma_fast": exit_ma_f,
                "exit_ma_slow": exit_ma_s,
                "price_return_pct": price_return * 100,
                "directional_return_pct": signed_return * 100,
                "leveraged_return_pct": leveraged_return * 100,
                "pnl_gross": pnl_gross,
                "pnl": pnl_net,
                "entry_notional": entry_notional,
                "exit_notional": exit_notional,
                "holding_days": max((exit_date - entry_date).days, 0),
            }
        )

    for _, row in price_df.iterrows():
        signal = row["ma_signal"]
        if pd.isna(signal) or signal == 0:
            continue

        if current_dir is None:
            current_dir = int(np.sign(signal))
            entry_price = float(row["Close"])
            entry_date = pd.to_datetime(row["date"])
            entry_ma_fast = float(row.get(f"ma_{fast}", np.nan))
            entry_ma_slow = float(row.get(f"ma_{slow}", np.nan))
            continue

        if int(np.sign(signal)) == current_dir:
            continue

        close_trade(row)
        current_dir = int(np.sign(signal))
        entry_price = float(row["Close"])
        entry_date = pd.to_datetime(row["date"])
        entry_ma_fast = float(row.get(f"ma_{fast}", np.nan))
        entry_ma_slow = float(row.get(f"ma_{slow}", np.nan))

    # Close any open trade on the final bar.
    if current_dir is not None and entry_price is not None and entry_date is not None:
        close_trade(price_df.iloc[-1])

    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        trades_df.sort_values("entry_date", inplace=True)
        trades_df.reset_index(drop=True, inplace=True)

    return trades_df


def summarize_trades(trades_df: pd.DataFrame) -> pd.Series:
    """Compute win-rate and PnL aggregates for the trade list."""
    if trades_df.empty:
        return pd.Series(dtype=float)

    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] <= 0]
    long_count = (trades_df["direction"] == "long").sum()
    short_count = (trades_df["direction"] == "short").sum()

    principal = float(trades_df["stake"].iloc[0]) if "stake" in trades_df.columns else np.nan
    total_pnl = trades_df["pnl"].sum()
    total_pnl_gross = trades_df["pnl_gross"].sum() if "pnl_gross" in trades_df.columns else np.nan
    total_fees = trades_df["fee_total"].sum() if "fee_total" in trades_df.columns else np.nan
    total_return = total_pnl / principal if principal else np.nan

    start_date = pd.to_datetime(trades_df["entry_date"]).min()
    end_date = pd.to_datetime(trades_df["exit_date"]).max()
    days_span = max((end_date - start_date).days, 1)
    annualized_return = (1 + total_return) ** (365 / days_span) - 1 if not np.isnan(total_return) else np.nan

    summary = {
        "trades": len(trades_df),
        "win_rate": len(wins) / len(trades_df) if len(trades_df) else np.nan,
        "long_trades": long_count,
        "short_trades": short_count,
        "avg_pnl": trades_df["pnl"].mean(),
        "median_pnl": trades_df["pnl"].median(),
        "avg_win": wins["pnl"].mean() if not wins.empty else np.nan,
        "avg_loss": losses["pnl"].mean() if not losses.empty else np.nan,
        "best_trade_pnl": trades_df["pnl"].max(),
        "worst_trade_pnl": trades_df["pnl"].min(),
        "total_pnl": total_pnl,
        "total_pnl_gross": total_pnl_gross,
        "total_fees": total_fees,
        "total_return_pct": total_return * 100 if not np.isnan(total_return) else np.nan,
        "annualized_return_pct": annualized_return * 100 if not np.isnan(annualized_return) else np.nan,
        "avg_holding_days": trades_df["holding_days"].mean(),
    }
    return pd.Series(summary)


def export_backtest_excel(trades_df: pd.DataFrame, summary: pd.Series, export_path: Path) -> Path:
    """Persist backtest trades and summary to an Excel workbook（中文表头）."""
    export_path = Path(export_path)
    export_path.parent.mkdir(parents=True, exist_ok=True)

    summary_mapping = {
        "trades": "交易总数",
        "win_rate": "胜率",
        "long_trades": "多头笔数",
        "short_trades": "空头笔数",
        "avg_pnl": "平均盈亏(u)",
        "median_pnl": "盈亏中位数(u)",
        "avg_win": "平均盈利(u)",
        "avg_loss": "平均亏损(u)",
        "best_trade_pnl": "最大单笔盈利(u)",
        "worst_trade_pnl": "最大单笔亏损(u)",
        "total_pnl": "总盈亏(含手续费,u)",
        "total_pnl_gross": "总盈亏(未扣手续费,u)",
        "total_fees": "手续费总额(u)",
        "total_return_pct": "总收益率(基于本金)",
        "annualized_return_pct": "年化收益率(基于持仓区间)",
        "avg_holding_days": "平均持仓天数",
    }
    summary_rows = []
    for key, label in summary_mapping.items():
        val = summary.get(key, np.nan)
        summary_rows.append({"指标": label, "数值": val})
    summary_df = pd.DataFrame(summary_rows)

    trades_to_save = trades_df.copy()
    if not trades_to_save.empty:
        trades_to_save["entry_date"] = pd.to_datetime(trades_to_save["entry_date"]).dt.strftime("%Y-%m-%d")
        trades_to_save["exit_date"] = pd.to_datetime(trades_to_save["exit_date"]).dt.strftime("%Y-%m-%d")

        # 额外衍生字段，中文表头
        trades_to_save["price_return_pct"] = trades_to_save["price_return_pct"].round(4)
        trades_to_save["directional_return_pct"] = trades_to_save["directional_return_pct"].round(4)
        trades_to_save["leveraged_return_pct"] = trades_to_save["leveraged_return_pct"].round(4)
        if "pnl_gross" in trades_to_save:
            trades_to_save["pnl_gross"] = trades_to_save["pnl_gross"].round(4)
        trades_to_save["pnl"] = trades_to_save["pnl"].round(4)
        trades_to_save["entry_notional"] = trades_to_save["entry_notional"].round(4)
        trades_to_save["exit_notional"] = trades_to_save["exit_notional"].round(4)
        trades_to_save["stake"] = trades_to_save["stake"].round(4)
        trades_to_save["leverage"] = trades_to_save["leverage"].round(4)
        if "fee_entry" in trades_to_save:
            trades_to_save["fee_entry"] = trades_to_save["fee_entry"].round(4)
        if "fee_exit" in trades_to_save:
            trades_to_save["fee_exit"] = trades_to_save["fee_exit"].round(4)
        if "fee_total" in trades_to_save:
            trades_to_save["fee_total"] = trades_to_save["fee_total"].round(4)
        if "capital_before" in trades_to_save:
            trades_to_save["principal_return_pct"] = (trades_to_save["pnl"] / trades_to_save["capital_before"] * 100).round(4)
        else:
            trades_to_save["principal_return_pct"] = (trades_to_save["pnl"] / trades_to_save["stake"] * 100).round(4)
        if "capital_before" in trades_to_save:
            trades_to_save["capital_before"] = trades_to_save["capital_before"].round(4)
        if "capital_after" in trades_to_save:
            trades_to_save["capital_after"] = trades_to_save["capital_after"].round(4)

        column_mapping = {
            "entry_date": "开仓日期",
            "exit_date": "平仓日期",
            "direction": "方向",
            "stake": "本金(u)",
            "leverage": "杠杆",
            "capital_before": "开仓前本金(u)",
            "capital_after": "平仓后本金(u)",
            "fee_entry": "开仓手续费(u)",
            "fee_exit": "平仓手续费(u)",
            "fee_total": "手续费合计(u)",
            "entry_price": "开仓价",
            "entry_ma_fast": "开仓MA快线",
            "entry_ma_slow": "开仓MA慢线",
            "exit_price": "平仓价",
            "exit_ma_fast": "平仓MA快线",
            "exit_ma_slow": "平仓MA慢线",
            "entry_notional": "名义敞口(u)",
            "exit_notional": "平仓名义价值(u)",
            "pnl_gross": "盈亏(毛,u)",
            "pnl": "盈亏(净,u)",
            "principal_return_pct": "本金收益率(%)",
            "price_return_pct": "价格涨跌(%)",
            "directional_return_pct": "方向收益(%)",
            "leveraged_return_pct": "杠杆收益(%)",
            "holding_days": "持仓天数",
        }

        # 设定导出列顺序
        ordered_cols = list(column_mapping.keys())
        trades_to_save = trades_to_save[ordered_cols].rename(columns=column_mapping)

    with pd.ExcelWriter(export_path) as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        trades_to_save.to_excel(writer, sheet_name="trades", index=False)

    return export_path
