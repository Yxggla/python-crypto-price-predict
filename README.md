# Cryptocurrency Trend Analysis and Prediction

This project is a CLI-first workflow for downloading, analysing, visualising, and forecasting cryptocurrency time series. Running `python main.py` grabs yfinance OHLCV + OKX dominance data, computes interpretable signals, renders export-ready figures, and prints actionable “lean long / lean short / wait” recommendations—everything an investor needs for a 10-minute trend briefing.

## Problem statement & objective

Retail crypto investors often jump between apps to answer three questions before taking action: *Is the market trending? Is volatility acceptable? Do complementary signals confirm my intuition?*  
Our goal is to deliver a **10-minute trend briefing** that stitches together: (1) full-history daily K-lines from yfinance, (2) a zoomed 90-day Price/MA + volume panel showing bull/bear regimes, (3) an indicator panel that explains rolling drawdowns, Sharpe, volatility regimes, MA crossovers, BTC–ETH spread z-scores, and explicit buy/hold/sell suggestions, plus (4) a “last 30 days + next 7 days” forecast chart so investors immediately know what to do. Every deliverable below links back to that north star.

## Project layout

```
data/             # Cached CSV downloads from yfinance + OKX helpers
src/              # Reusable Python modules for data loading, analytics, viz, and modelling
main.py           # CLI entry point that runs the entire workflow
requirements.txt  # Python dependencies
figures/          # CLI-generated PNG/HTML artefacts (ignored by git)
exports/          # Optional Excel exports (ignored by git)
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
3. Run the CLI to fetch yfinance OHLCV, OKX dominance candles, indicator panels, 90-day Price/MA charts, short-term forecasts, and models in one go. Set `--days` to **2000 or more** so each symbol has at least ~2000 rows of history:
    ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 2000 --interval 1d \
     --dominance-inst-id BTC-USDT \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
   The CLI always emits Matplotlib PNGs (90-day Price/MA, indicator panel, 30d+7d forecast), Plotly HTML K-lines, interactive charts, and Excel exports. Add `--force` to refresh cached CSVs, and use `--dominance-inst-id` to switch OKX sources.

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
3. *(reserved for future sources)* The CLI currently relies on yfinance + OKX; extend here if additional sources are needed.

## Outputs at a glance

- **Excel price sheet** — `exports/...xlsx` → `prices` sheet includes raw OHLCV plus `change_abs`, `change_pct`, rolling volatility/drawdown/Sharpe, MA signals, etc., so you can filter inside Excel.
- **Interactive K-line** — Plotly candlesticks display O/H/L/C and daily change/percentage on hover, and HTML copies live under `figures/`.
- **Price vs MA chart (90 days)** — `figures/<symbol>_price.png` zooms into the latest 90 sessions, color-codes bull/bear regimes (Close vs MA30), draws dashed MA7/MA30, shades top-volume days, and renders teal/red volume bars with human-friendly million-unit ticks.
- **Indicator panel** — `figures/<symbol>_indicator_panel.png` shows (1) price + volatility regime shading, (2) rolling max drawdown, (3) rolling Sharpe, plus a caption such as “lean long / wait / lean short” with bullet-point reasons.
- **Short-term forecast view** — `figures/<symbol>_forecast_next7.png` overlays the last 30 days of actual closes with the next 7 days of linear-regression forecasts so potential pivots are obvious.
- **Signal snapshot** — CLI stdout summarises the latest regime, drawdown, Sharpe, MA state, BTC–ETH spread z-score, and prints the plain-English recommendation, so no extra post-processing is needed.

## Planned extensions (aligned to the objective)

| Track | Why it matters | Concrete deliverables |
| --- | --- | --- |
| **Narrative & objectives** | Keep everyone aligned to the “10-minute trend briefing.” | README + persona summary, success metrics, CLI outputs that clearly tell users “buy / sell / wait.” |
| **Data spine** | Market-share context makes signals credible. | Harden CLI/export for BTC-USD/ETH-USD/SOL-USD (yfinance) plus OKX BTC-USDT dominance candles, document schema + validation scripts. |
| **Indicators & insight** | Users need interpretable triggers. | Maintain rolling drawdown, Sharpe, BTC–ETH z-score, volatility regimes, MA crossovers, and textual recommendations inside CLI + indicator panels. |
| **Visualization & dashboard** | Stakeholders digest insights visually. | Keep Price/MA, indicator panels, dominance charts, and forecast plots export-ready for PPT/briefings. |
| **Modeling & strategy** | Quantifies “what happens next.” | Iterate LR/ARIMA/Prophet/LSTM, implement MA crossover / predicted-return strategies, share equity curves + confusion matrices. |

## Suggested team workflow

1. **Person A – Project structure & data ingestion**
   - Owns repo layout, dependencies, and `src/data_loader.py`. Keeps yfinance/OKX pulls and Excel exports healthy.
2. **Person B – Data processing & indicators**
   - Extends `src/analysis.py`, maintains derived columns, validates rolling metrics, and keeps CLI signal prints accurate.
3. **Person C – Matplotlib visualizations**
   - Enhances Price/MA charts, indicator panels, forecast plots, and ensures PNG assets drop directly into decks.
4. **Person D – Plotly & HTML visualizations**
   - Owns interactive K-line + dominance HTML exports and any web-friendly dashboards.
5. **Person E – Modeling & forecasting**
   - Develops/maintains models in `src/model.py` (LR/ARIMA/Prophet/LSTM), tunes hyperparameters, manages checkpoints.
6. **Person F – Strategy & integration**
   - Wires predictions into MA crossover / predicted-return strategies, extends `main.py` + Excel exports, and verifies end-to-end CLI demos.
