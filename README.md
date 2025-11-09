# Cryptocurrency Trend Analysis and Prediction

This project provides a reproducible workflow for downloading, analysing, visualising, and modelling cryptocurrency time series. It targets the COMM7330 course requirements and supports a six-person collaboration workflow covering data acquisition, exploratory analysis, modelling, visual reporting, and presentation deliverables.

## Problem statement & objective

Retail crypto investors often jump between apps to answer three questions before taking action: *Is the market trending? Is volatility acceptable? Do complementary signals confirm my intuition?*  
Our 10‑minute presentation (and the supporting system) must therefore help a novice investor decide whether to **enter, hold, or exit** BTC/ETH positions within a single dashboard + report bundle. Every deliverable below links back to that north star.

## Project layout

```
data/             # Cached CSV downloads from Yahoo Finance
notebooks/        # Jupyter notebooks for each analysis stage (to be authored by the team)
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
3. Provide required API credentials (CoinMarketCap in this phase). You can either export it in your shell or store it in a local `.env` file (ignored by git) and `source` it before running commands:
   ```bash
   # option A: export
   export COINMARKETCAP_API_KEY="<your-coinmarketcap-key>"

   # option B: create .env (same folder) and load it into the shell
   echo 'COINMARKETCAP_API_KEY="<your-coinmarketcap-key>"' >> .env
   set -a; source .env; set +a
   ```
4. Run the CLI to fetch data, compute metrics, fit a baseline model, and preview outputs:
   ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 730 --interval 1d
   ```
   Use `--force` to refresh cached CSV files in `data/`.
   Add `--save-figures` to persist Matplotlib charts (price trends, actual-vs-predicted) to the `figures/` directory for later use in reports or slides.

## Module overview

- `src/data_loader.py` — Handles crypto price downloads (yfinance), Binance dominance klines, FRED macro series, and CoinMarketCap global/asset metrics with CSV caching.
- `src/analysis.py` — Computes daily returns, rolling volatility, and cross-asset correlations.
- `src/visualization.py` — Provides Matplotlib and Plotly helpers (price trends with volume overlays, candlestick charts, actual-vs-predicted plots).
- `src/model.py` — Implements a linear-regression baseline plus an ARIMA helper for time-series forecasting.

## Data acquisition cookbook

> **Environment prerequisites**
> - `pip install -r requirements.txt` now includes `pandas-datareader` for FRED downloads.
> - Set `export COINMARKETCAP_API_KEY=<your-key>` (or load it from `.env`) before requesting CoinMarketCap data.

1. **Price history (BTC / ETH / SOL)**  
   ```python
   from datetime import date, timedelta
   from src.data_loader import DownloadConfig, download_price_histories

   today = date.today()
   start = today - timedelta(days=730)
   configs = [
       DownloadConfig("BTC-USD", start, today),
       DownloadConfig("ETH-USD", start, today),
       DownloadConfig("SOL-USD", start, today),
   ]
   download_price_histories(configs)
   ```
2. **BTC dominance (Binance BTCDOMUSDT klines)**  
   ```python
   from src.data_loader import BinanceKlinesConfig, download_binance_klines
   download_binance_klines(BinanceKlinesConfig(symbol="BTCDOMUSDT", interval="1d"))
   ```
   Output CSV columns: `date, open, high, low, close, volume`.
3. **Macro series (e.g., Fed Funds Rate from FRED)**  
   ```python
   from src.data_loader import MacroSeriesConfig, download_macro_series
   download_macro_series(MacroSeriesConfig(series_id="FEDFUNDS", start="2010-01-01"))
   ```
   Provide `api_key` or set `FRED_API_KEY` if your FRED account requires it.
4. **CoinMarketCap metrics (global dominance + latest quotes)**  
   ```python
   from src.data_loader import (
       CoinMarketCapGlobalConfig,
       CoinMarketCapAssetConfig,
       download_cmc_global_metrics,
       download_cmc_asset_quotes,
   )

   download_cmc_global_metrics(CoinMarketCapGlobalConfig(convert="USD"))
   download_cmc_asset_quotes(
       CoinMarketCapAssetConfig(symbols=["BTC", "ETH", "SOL"], convert="USD")
   )
   ```
   Requires `COINMARKETCAP_API_KEY`. Global CSV provides dominance/total cap/volume; quotes CSV stores price, market cap, and percent changes per symbol.

## Planned extensions (aligned to the objective)

| Track | Why it matters | Concrete deliverables |
| --- | --- | --- |
| **User story & objective** | Keep the “entry/exit decision within 10 minutes” story explicit. | README + slide describing persona, decision workflow, and how each module supports it. |
| **Richer data coverage** | Entry/exit decisions need macro + market-share confirmation. | Extend `data_loader.py` to fetch SOL-USD, BTC.D dominance, FRED rates, and CoinMarketCap global metrics (dominance, total cap, volume) with caching. |
| **Deeper indicators** | Users need interpretable signals, not just price charts. | Implement rolling max drawdown, Sharpe ratio, BTC–ETH spread z-score, volatility regimes, and annotate when signals trigger. |
| **Story-driven visuals** | Decision makers grasp insights visually. | Plotly dashboard with linked charts, regime shading, signal annotations, and exportable PNG/GIF via `--save-figures`. |
| **Models & strategies** | Quantify “what happens next” and tie it to actions. | Add Prophet or LSTM, compare with LR/ARIMA, and run MA crossover or model-signal backtests with equity curve + confusion chart. |
| **Narrated notebooks** | Documentation must prove the workflow is reproducible. | Fill `notebooks/01-03` with markdown rationale, saved outputs, and callouts that map to the 10‑minute story. |

## Suggested team workflow

1. **Person A – Project Lead, Storytelling & Reporting**
   - Maintain the “entry/exit in 10 minutes” narrative inside README + slides, update success metrics, and ensure every module explicitly links back to the objective.
   - Curate screenshots/figures exported by teammates, assemble the report outline, and script the 10‑minute presentation (including speaker notes).
   - Facilitate weekly sync/checklist so each deliverable meets the persona’s needs; log blockers and decisions in `README.md`.
2. **Person B – Data Acquisition & Feature Engineering**
   - Extend `src/data_loader.py` to ingest additional markets (BTC-USD, ETH-USD, SOL-USD), dominance indices, FRED macro series, and on-chain metrics; document ETL steps in `notebooks/01_data_cleaning.ipynb`.
   - Produce a data dictionary covering column definitions, refresh cadence, and how each feature supports entry/exit decisions.
   - Implement validation scripts (missing data checks, alignment across frequencies) and share sample CSVs in `data/`.
3. **Person C – Exploratory Analysis & Indicator Design**
   - Enhance `src/analysis.py` with max drawdown, Sharpe, z-score spreads, volatility regimes, and turn them into “signals” with clear thresholds.
   - Own `notebooks/02_analysis.ipynb`: narrate insights (markdown + figures) that explain how indicators anticipate good/bad entry points.
   - Hand over concise insight summaries to Person A for inclusion in report/presentation.
4. **Person D – Visualization & Dashboarding**
   - Upgrade `src/visualization.py` to deliver Plotly dashboards combining price, volume, indicators, and model signals; include regime shading + tooltips explaining what to do.
   - Build a one-pager dashboard (HTML/GIF/png) via CLI `--save-figures` so the persona can “see everything” quickly.
   - Coordinate with Person F to ensure the dashboard animates or updates correctly during live demo.
5. **Person E – Modeling & Backtesting**
   - Implement Prophet or LSTM in `src/model.py` (or a dedicated module), compare against the linear regression/ARIMA baselines, and document metrics (MAE/MAPE) in `notebooks/03_prediction.ipynb`.
   - Translate model outputs into a simple decision rule (e.g., MA crossover, predicted return > threshold) and backtest it; export equity curve, hit-rate table, and confusion chart.
   - Summarize when the model recommends entries/exits and how confident it is, so Person A can articulate the recommendation quality.
6. **Person F – Integration, CLI & Demo Experience**
   - Keep `main.py` orchestrating the full workflow (fetch → features → indicators → models → charts) with flags for new data sources, signal thresholds, and export paths.
   - Produce a scripted CLI run (recorded GIF or terminal log) that demonstrates how the persona would interact with the tool in under 10 minutes.
   - Manage packaging (requirements, README instructions, optional Docker) so instructors can reproduce the demo.

## Next steps

- Populate notebooks with detailed workflows and narrative commentary.
- Add automated tests (e.g., with `pytest`) to cover data transforms if required.
- Integrate advanced models (Prophet, LSTM) or alternative data sources (CoinGecko, on-chain metrics) as stretch goals.

Feel free to adapt or extend the structure to meet team preferences or instructor guidelines.
