# Cryptocurrency Trend Analysis and Prediction

This project provides a reproducible workflow for downloading, analysing, visualising, and modelling cryptocurrency time series. It targets the COMM7330 course requirements and supports a six-person collaboration workflow covering data acquisition, exploratory analysis, modelling, visual reporting, and presentation deliverables.

## Problem statement & objective

Retail crypto investors often jump between apps to answer three questions before taking action: *Is the market trending? Is volatility acceptable? Do complementary signals confirm my intuition?*  
Our refreshed goal is to hand an investor a **10-minute trend briefing** that stitches together: (1) full-history daily K-lines from yfinance, (2) a zoomed 90-day Price/MA+volume panel that highlights bull/bear regimes, (3) notebook-ready indicators such as rolling max drawdown, Sharpe, BTC–ETH spread z-scores, volatility regimes, MA crossover triggers, and (4) short-horizon forecasts that answer “what’s next and how should I act?”. Every deliverable below links back to that north star.

## Project layout

```
data/             # Cached CSV downloads from yfinance + OKX helpers
src/              # Reusable Python modules for data loading, analytics, viz, and modelling
main.py           # CLI entry point that runs the end-to-end workflow
requirements.txt  # Python dependencies
```

## Getting started

1. Create and activate a virtual environment (example for `venv`):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the CLI to fetch yfinance OHLCV, OKX dominance candles, figures, indicator panels, and models in one go. Set `--days` to **2000 or more** so each symbol has at least ~2000 rows of history:
    ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 2000 --interval 1d \
     --dominance-inst-id BTC-USDT \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
   The CLI always emits Matplotlib PNGs (both the 90-day Price/MA view and the indicator panel), Plotly HTML files, and interactive charts. Add `--force` to refresh cached CSVs, and use `--dominance-inst-id` to switch OKX sources.

## Module overview

- `src/data_loader.py` — Handles yfinance price pulls plus OKX dominance candles with CSV caching.
- `src/analysis.py` — Computes daily returns, rolling volatility, cross-asset correlations, and open-to-close period performance.
- `src/visualization.py` — Provides Matplotlib and Plotly helpers (price trends with volume overlays, candlestick charts, actual-vs-predicted plots).
- `src/model.py` — Implements a linear-regression baseline plus an ARIMA helper for time-series forecasting.

## Data acquisition cookbook

> **Environment prerequisites**
> - `pip install -r requirements.txt` already covers yfinance/OKX helpers.
>
> The CLI automatically runs the same helpers (yfinance OHLCV downloads + OKX BTC-USDT dominance proxy) and can bundle everything into Excel via `--export-xlsx`. The snippets below are for ad-hoc script use.

### Data origin cheat sheet

- **yfinance** — Supplies OHLCV price history for every symbol passed via `--symbols` (e.g., `BTC-USD`, `ETH-USD`, `SOL-USD`). These rows populate the price charts, period stats, correlations, and model training data.
- **OKX public API** — Supplies the BTC-USDT dominance proxy (`open/high/low/close/volume_base`) via `download_okx_candles`. This dataset feeds the dominance exports/plots.

### Cookbook

1. **Price history via yfinance (BTC / ETH / SOL)**  
   ```python
   from datetime import date, timedelta
   from src.data_loader import DownloadConfig, download_price_histories

   today = date.today()
   start = today - timedelta(days=2000)
   configs = [
       DownloadConfig("BTC-USD", start, today),
       DownloadConfig("ETH-USD", start, today),
       DownloadConfig("SOL-USD", start, today),
   ]
   download_price_histories(configs)
   ```
2. **BTC dominance proxy (OKX BTC-USDT candles)**  
   ```python
   from src.data_loader import OkxCandlesConfig, download_okx_candles
   download_okx_candles(OkxCandlesConfig(inst_id="BTC-USDT", bar="1D"))
   ```
   Output CSV columns: `date, open, high, low, close, volume_base`.
3. *(reserved for future sources)* 当前 CLI 仅依赖 yfinance + OKX，如需补充其它指标，可在此扩展。

## Outputs at a glance

- **Excel price sheet** — Every symbol’s yfinance OHLCV history now includes two extra columns: `change_abs` (Close − Open) and `change_pct` (percentage change from the day’s open). These appear in the `prices` worksheet next to the raw K-line data.
- **Interactive K-line** — Hovering a candlestick shows Open/High/Low/Close plus the exact daily change and percentage change, making it easy to read the move without manual math.
- **Price vs MA chart (90 days)** — The Matplotlib chart in `figures/<symbol>_price.png` zooms into the latest 90 sessions, color-codes bull/bear regimes (Close vs MA30), draws both MA7 / MA30 as dashed overlays, shades the top-volume days, and shows teal/red volume bars (with a legend) depending on whether the session closed up or down; the volume axis now uses human-friendly million units instead of `1e11`-style ticks.
- **Indicator panel** — Each run also saves `figures/<symbol>_indicator_panel.png`, a three-pack showing (1) price + volatility regime shading, (2) rolling max drawdown, (3) rolling Sharpe, plus a caption that spells out the current “lean long / lean short / wait” action with bullet-point reasons.
- **Signal snapshot** — CLI output now prints the volatility regime, rolling max drawdown, rolling Sharpe, MA7/MA30 state, BTC–ETH spread z-score, **and** a plain-English recommendation (lean long / lean short / wait) with the key reasons so you can act without opening a notebook.

## Planned extensions (aligned to the objective)

| Track | Why it matters | Concrete deliverables |
| --- | --- | --- |
| **Narrative & objectives** | Keeps everyone driving toward “10-minute entry/exit guidance.” | README + persona brief with success metrics, plus notebook callouts that tie outputs back to the story. |
| **Multisource data spine** | Market-share context makes signals credible. | Harden CLI/export for BTC-USD/ETH-USD/SOL-USD (yfinance) plus OKX BTC-USDT dominance candles, and document a data dictionary with validation checks. |
| **Indicators & insight** | Users need interpretable triggers. | Keep CLI + indicator panel updated with rolling max drawdown, Sharpe, BTC–ETH spread z-score, volatility regimes, MA crossovers, and plain-English recommendations. |
| **Visualization & dashboard** | Stakeholders digest insights visually. | Expand Plotly/Matplotlib outputs (Price/MA, indicator panel, dominance chart) and ensure every graphic is export-ready for PPT/briefings. |
| **Modeling & strategy** | Quantifies “what happens next” and actionability. | Compare LR/ARIMA vs Prophet/LSTM, implement MA crossover + predicted-return strategies, and output equity curves + confusion matrices. |

## Suggested team workflow

1. **Person A – Data ingestion lead**
   - Owns `src/data_loader.py` / CLI integrations to keep yfinance BTC/ETH/SOL pulls and OKX dominance candles healthy and timezone-clean.
   - Maintains the CLI + Excel export schema and verifies cached datasets stay consistent.
2. **Person B – Feature engineering & cleaning**
   - Implements derived columns (returns, spreads, etc.) directly in `src/analysis.py` helpers and adds lightweight tests.
3. **Person C – Indicator & insight engineering**
   - Extends `src/analysis.py` with new signals (drawdown, Sharpe, volatility regimes, z-scores, MA triggers) and ensures CLI prints/plots remain readable.
4. **Person D – Visualization engineering**
   - Builds/updates Plotly + Matplotlib figures (Price/MA, indicator panel, dominance charts) so assets drop straight into PPT/briefings.
5. **Person E – Modeling algorithms**
   - Focuses on model architectures inside `src/model.py` (LR/ARIMA baseline vs Prophet/LSTM), tuning hyperparameters and saving reusable checkpoints or inference helpers.
6. **Person F – Strategy & pipeline integration**
   - Takes Person E’s predictions and owns the backtesting/export layer: wiring predictions into MA crossover / predicted-return strategies, extending `main.py` + Excel exports so new metrics land in the workbook.
   - Adds CLI/demo scripts that showcase the full pipeline (data → indicators → models → strategy outputs) and verifies each run emits the expected CSV/Excel/figure set.
