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

## Suggested team workflow

1. **Project Lead** – Manages roadmap, coordinates notebooks, curates final report.
2. **Data Acquisition** *shanshan* – Extends `data_loader.py` or builds custom notebook to fetch additional assets or features.
3. **Data Analysis** *li*  – Uses `notebooks/01_data_cleaning.ipynb` to clean and compute descriptive statistics using `src.analysis`.
4. **Visualisation** *nn* – Leverages `src.visualization` within `notebooks/02_analysis.ipynb` to produce course-ready figures (e.g., Plotly dashboards or Matplotlib charts).
5. **Modelling**  *csn* *hy* – Experiments with `src.model` and develops advanced predictors (ARIMA variants, LSTM prototypes) in `notebooks/03_prediction.ipynb`.
6. **Reporting** – Consolidates findings into `report.pdf` and `presentation.pptx`, sourcing visuals and summary tables from notebooks.

## Next steps

- Populate notebooks with detailed workflows and narrative commentary.
- Add automated tests (e.g., with `pytest`) to cover data transforms if required.
- Integrate advanced models (Prophet, LSTM) or alternative data sources (CoinGecko, on-chain metrics) as stretch goals.

Feel free to adapt or extend the structure to meet team preferences or instructor guidelines.
