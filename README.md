# Cryptocurrency Trend Analysis and Prediction

This project provides a reproducible workflow for downloading, analysing, visualising, and modelling cryptocurrency time series. It targets the COMM7330 course requirements and supports a six-person collaboration workflow covering data acquisition, exploratory analysis, modelling, visual reporting, and presentation deliverables.

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
3. Run the CLI to fetch data, compute metrics, fit a baseline model, and preview outputs:
   ```bash
   python main.py --symbols BTC-USD ETH-USD --days 730 --interval 1d
   ```
   Use `--force` to refresh cached CSV files in `data/`.
   Add `--save-figures` to persist Matplotlib charts (price trends, actual-vs-predicted) to the `figures/` directory for later use in reports or slides.

## Module overview

- `src/data_loader.py` — Handles data downloads via `yfinance`, caching, and CSV loading.
- `src/analysis.py` — Computes daily returns, rolling volatility, and cross-asset correlations.
- `src/visualization.py` — Provides Matplotlib and Plotly helpers (price trends with volume overlays, candlestick charts, actual-vs-predicted plots).
- `src/model.py` — Implements a linear-regression baseline plus an ARIMA helper for time-series forecasting.

## Planned extensions (for a 10‑minute presentation)

| Track | Why it matters | Concrete deliverables |
| --- | --- | --- |
| **User story & objective** | Anchor the work around “helping novice crypto investors judge entry/exit within 10 minutes.” | One slide/README paragraph that states the problem, target users, and success metrics. |
| **Richer data coverage** | Link price action with macro/chain signals to explain moves. | Extend `data_loader.py` to fetch SOL-USD, BTC.D dominance, FRED rates, ETH active addresses, and exchange net inflow CSVs. |
| **Deeper indicators** | Give the audience insight beyond OHLC. | Add features such as rolling max drawdown, Sharpe ratio, BTC–ETH spread z-score, and volatility regimes in `src/analysis.py` + Notebook 02 outputs. |
| **Story-driven visuals** | Slides/screenshots need to “show” the findings. | Plotly dashboard with linked charts, regime shading, and model error bands saved via `--save-figures`. |
| **Models & strategies** | Baseline LR/ARIMA is good; comparison makes it compelling. | Add Prophet or LSTM, plus a simple MA crossover / model-signal backtest with equity curve + confusion chart. |
| **Narrated notebooks** | Instructor can trace the analysis logic. | Fill `notebooks/01-03` with markdown rationale, code, and saved outputs ready for report/presentation reuse. |

## Suggested team workflow

1. **Project Lead & Reporter (Person A)** – Owns the README narrative above, drafts the 10‑minute script, curates screenshots from notebooks, and ensures findings map to the user story/objective.
2. **Data Acquisition & Feature Engineering (Person B)** – Extends `src/data_loader.py` plus `notebooks/01_data_cleaning.ipynb` to pull multi-asset, macro, and on-chain metrics; documents a data dictionary and quality checks.
3. **Exploratory Analysis & Indicator Design (Person C)** – Enhances `src/analysis.py`, computes return/volatility regimes, z-scores, drawdowns, and summarizes insights with markdown commentary in Notebook 02.
4. **Visualization & Dashboarding (Person D)** – Expands `src/visualization.py` with Plotly dashboards, regime shading, and error-band plots; exports publication-ready figures via CLI `--save-figures`.
5. **Modeling & Backtesting (Person E)** – Builds Prophet/LSTM variants in `src/model.py` or dedicated notebook sections, compares against LR/ARIMA baselines, and codes a simple trading/backtest routine with performance stats.
6. **Integration & Demo (Person F)** – Keeps `main.py` runnable end-to-end, wires CLI flags for new data/features, prepares a short live demo or recorded run showing how the system guides entry/exit decisions.

## Next steps

- Populate notebooks with detailed workflows and narrative commentary.
- Add automated tests (e.g., with `pytest`) to cover data transforms if required.
- Integrate advanced models (Prophet, LSTM) or alternative data sources (CoinGecko, on-chain metrics) as stretch goals.

Feel free to adapt or extend the structure to meet team preferences or instructor guidelines.
