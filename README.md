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
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 730 --interval 1d \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
   Use `--force` to refresh cached CSV files in `data/`.
   Add `--save-figures` to persist Matplotlib charts (price trends, actual-vs-predicted) to the `figures/` directory for later use in reports or slides.
   Add `--plotly-kline --show-kline` to render the polished Plotly candlestick chart in a browser (pair it with `--save-figures` to keep HTML exports such as `figures/btc-usd_kline.html`).
   Add `--quiet` if you only want cached files + charts without console tables.
   Use `--macro-series DGS10` (or `--macro-series none`) to control FRED pulls, `--dominance-inst-id BTC-USDT` to switch OKX dominance proxies, and `--skip-cmc` if you do not want CoinMarketCap metrics.

### Quick candlestick preview

Once you've run the CLI and cached price data, you can regenerate the interactive K-line without writing a notebook:

```bash
python main.py --symbols BTC-USD --days 365 --interval 1d \
  --plotly-kline --show-kline --save-figures
```

This command both opens the chart in a browser window and writes an HTML copy to `figures/btc-usd_kline.html` (thanks to `--save-figures`).

## Module overview

- `src/data_loader.py` — Handles crypto price downloads (yfinance), OKX dominance candles, FRED macro series, and CoinMarketCap global/asset metrics with CSV caching.
- `src/analysis.py` — Computes daily returns, rolling volatility, cross-asset correlations, and open-to-close period performance.
- `src/visualization.py` — Provides Matplotlib and Plotly helpers (price trends with volume overlays, candlestick charts, actual-vs-predicted plots).
- `src/model.py` — Implements a linear-regression baseline plus an ARIMA helper for time-series forecasting.

## Data acquisition cookbook

> **Environment prerequisites**
> - `pip install -r requirements.txt` now includes `pandas-datareader` for FRED downloads.
> - Set `export COINMARKETCAP_API_KEY=<your-key>` (or load it from `.env`) before requesting CoinMarketCap data.
>
> The CLI automatically runs the same helpers (OKX BTC-USDT dominance proxy, FRED series, CoinMarketCap metrics) and can bundle everything into Excel via `--export-xlsx`. The snippets below are for ad-hoc or notebook use.

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
2. **BTC dominance proxy (OKX BTC-USDT candles)**  
   ```python
   from src.data_loader import OkxCandlesConfig, download_okx_candles
   download_okx_candles(OkxCandlesConfig(inst_id="BTC-USDT", bar="1D"))
   ```
   Output CSV columns: `date, open, high, low, close, volume_base`.
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
| **Narrative & objectives** | Keeps everyone driving toward “10-minute entry/exit guidance.” | README + persona brief with success metrics, plus notebook callouts that tie outputs back to the story. |
| **Multisource data spine** | Market-share + macro context makes signals credible. | Harden CLI/export for BTC/ETH/SOL, OKX BTC-USDT dominance candles, FRED FEDFUNDS + DGS10, CoinMarketCap global + quotes, and document a data dictionary with validation checks. |
| **Indicators & macro insight** | Users need interpretable triggers. | Add rolling max drawdown, Sharpe, BTC–ETH spread z-score, volatility regimes, MA crossovers; include trigger explanations in Notebook 02. |
| **Visualization & dashboard** | Stakeholders digest insights visually. | Plotly dashboard with price/dominance/macro/model overlays, regime shading, annotations, and exported PNG/GIF assets ready for PPT. |
| **Modeling & strategy** | Quantifies “what happens next” and actionability. | Compare LR/ARIMA vs Prophet/LSTM, implement MA crossover + predicted-return strategies, and output equity curves + confusion matrices. |
| **Notebook-first storytelling** | Slides/report should flow from notebooks. | Populate `notebooks/01-03` with markdown narration, saved charts/tables, and references indicating which slide/report section each asset supports. |

## Suggested team workflow

1. **Person A – Data ingestion lead**
   - Owns `src/data_loader.py` / CLI integrations to keep BTC/ETH/SOL, OKX dominance candles, FRED, and CoinMarketCap downloads healthy and timezone-clean.
   - Maintains Notebook 01’s ETL section (data dictionary, validation snippets) and ensures Excel export schemas stay stable.
2. **Person B – Feature engineering & cleaning**
   - Implements derived columns (returns, spreads, macro joins) inside Notebook 01 and supporting helpers in `src/analysis.py`.
   - Writes quick unit/notebook tests validating sample rows before data moves downstream.
3. **Person C – Indicator & macro analytics**
   - Extends `src/analysis.py` with rolling drawdown, Sharpe, volatility regimes, BTC–ETH z-scores, MA triggers, and documents each signal in Notebook 02 with code + commentary.
   - Hands off summarized tables/figures that cite the exact code cell for reuse.
4. **Person D – Visualization engineering**
   - Develops Plotly dashboards and Matplotlib figures inside `src/visualization.py`, wiring price/dominance/macro/model overlays plus annotations.
   - Automates figure export via CLI `--save-figures` or notebook cells, providing instructions/code for reproducing PNG/GIF assets.
5. **Person E – Modeling algorithms**
   - Focuses on model architectures inside Notebook 03 / `src/model.py` (LR/ARIMA baseline vs Prophet/LSTM), tuning hyperparameters and saving reusable checkpoints or inference helpers.
   - Documents training/evaluation code so others can reproduce metrics and swap models in or out.
6. **Person F – Strategy & pipeline integration**
   - Takes Person E’s predictions and owns the backtesting/export layer: wiring predictions into MA crossover / predicted-return strategies, extending `main.py` + Excel exports so new metrics land in the workbook.
   - Adds CLI/demo scripts that showcase the full pipeline (data → indicators → models → strategy outputs) and verifies each run emits the expected CSV/Excel/figure set.
