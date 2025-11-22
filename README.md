# Cryptocurrency Trend Analysis / 加密货币趋势分析

CLI workflow that downloads yfinance OHLCV (open/high/low/close/volume lines), computes interpretable indicators (drawdown, Sharpe, volatility regimes, MA crossovers, BTC–ETH spread z-score, etc.), renders export-ready visualisations, runs short-term forecasts, and prints “lean long / lean short / wait” suggestions for a 10-minute investment briefing.  
本项目是一套基于 yfinance 的 CLI 工作流，可自动抓取“开盘价/最高价/最低价/收盘价/成交量”这些核心行情数据，先计算滚动回撤/夏普/波动率 Regime/MA 交叉/BTC‑ETH 价差 z-score 等指标，再结合 7 天预测生成图表，最终输出“偏多/偏空/观望”建议，满足 10 分钟趋势汇报的需求。

**Purpose / 目的** – Give retail investors：统一数据来源、指标解释、预测结果和可视化风格，让任何人无需翻阅多份报告就能迅速判断 BTC/ETH/SOL 应该偏多、偏空还是观望。

**Quick Signal Logic / 简易判定逻辑**
- MA7 在线上、滚动夏普为正、波动率不是 high → `LEAN LONG`（偏多）
- MA7 在下、滚动夏普为负 → `LEAN SHORT`（偏空）
- 波动率 high 且近期回撤 >8% → `STAND ASIDE / WAIT`（观望）
- 不满足以上条件则保持 `WAIT`

## Repository Layout 项目结构

```
data/             Fresh CSV generated every CLI run / 每次 CLI 运行生成的最新 CSV
src/              Data loading, analytics, viz, modelling modules / 数据加载、分析、可视化、建模模块
main.py           CLI entry point / CLI 入口
figures/, exports/  Generated PNG/HTML/XLSX / 生成物
requirements.txt  Python 依赖
```

## Quick Start 快速开始

1. **Create a virtual environment 创建虚拟环境**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```
   Windows PowerShell:
   ```powershell
   py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
   ```

2. **Install dependencies 安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the CLI 运行 CLI**（每次都会重新下载 yfinance 数据并覆盖 `data/*.csv`）
   ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 2000 --interval 1d \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
   - `--days ≥ 2000` so each asset has足够历史。  
   - CLI 会在 `figures/` 生成 Matplotlib PNG + Plotly HTML，在 `exports/` 输出 Excel，总结信号到终端。

## Outputs at a Glance 输出一览

- **Excel price sheet Excel 价格表**：`exports/...xlsx` 包含 OHLCV、`change_abs/pct`、滚动波动率/回撤/Sharpe、MA 信号，便于课堂或 PPT 二次分析。
- **Interactive K-line 交互 K 线**：Plotly HTML 展示 O/H/L/C + 当日涨跌额/幅，可直接嵌入网页或附录。
- **90-day Price vs MA 价格+均线图**：`figures/<symbol>_price.png` 标注多空区间、MA7/MA30、成交量，直接贴入报告。
- **Indicator panel 指标面板**：`figures/<symbol>_indicator_panel.png` 显示波动率 Regime、滚动回撤、滚动 Sharpe，并给出“lean long / wait / lean short”文案。
- **Short-term forecast 短期预测图**：`figures/<symbol>_forecast_next7.png` 对比最近 30 天实值与未来 7 天预测，突出潜在拐点。
- **CLI signal snapshot CLI 信号快照**：终端输出最新 regime、drawdown、Sharpe、MA 状态、BTC-ETH z-score 及操作建议。

## Team Roles 团队分工

- 组长｜仓库结构与数据获取（董一孝）：统筹项目整体结构，负责仓库布局、依赖管理和 `src/data_loader.py`，确保 yfinance 下载与 Excel 导出稳定。
- 数据处理与指标分析（李笙筠）：负责 `src/analysis.py`，数据处理与指标分析工作。
- 模型与预测（陈锶妮）：负责模型与预测工作。
- Matplotlib 可视化（韩晔）：生成价格/均线图及指标面板。
- Plotly 与 HTML 可视化（薛姗姗）：负责 Plotly K 线及其他交互式输出。
- Matplotlib 可视化（宁衍程）：生成预测相关 PNG（如 `forecast_next7`）。
