# Cryptocurrency Trend Analysis / 加密货币趋势分析

CLI workflow that downloads yfinance OHLCV (open/high/low/close/volume lines), computes interpretable indicators (drawdown, Sharpe, volatility regimes, MA crossovers, BTC–ETH spread z-score, etc.), renders export-ready visualisations, runs short-term forecasts, and prints “lean long / lean short / wait” suggestions for a 10-minute investment briefing.  
本项目是一套基于 yfinance 的 CLI 工作流，可自动抓取“开盘价/最高价/最低价/收盘价/成交量”这些核心行情数据，先计算滚动回撤/夏普/波动率 Regime/MA 交叉/BTC‑ETH 价差 z-score 等指标，再结合 7 天预测生成图表，最终输出“偏多/偏空/观望”建议，满足 10 分钟趋势汇报的需求。

**Purpose / 目的** – Give retail investors and课堂评委一份“10 分钟即可读完”的趋势简报：统一数据来源、指标解释、预测结果和可视化风格，让任何人无需翻阅多份报告就能迅速判断 BTC/ETH/SOL 应该偏多、偏空还是观望。

**Quick Signal Logic / 简易判定逻辑**
- MA7 在线上、滚动夏普为正、波动率不是 high → `LEAN LONG`（偏多）
- MA7 在下、滚动夏普为负 → `LEAN SHORT`（偏空）
- 波动率 high 且近期回撤 >8% → `STAND ASIDE / WAIT`（观望）
- 不满足以上条件则保持 `WAIT`

## Overview 概述

**Why** – Retail investors constantly ask: *Is there a trend? Is volatility acceptable? Are multiple signals aligned?* We answer these within one CLI so every chart/table ties back to the same story.  
**痛点**：散户决策前需要确认“是否趋势”“波动率是否可接受”“信号是否一致”，我们将所有数据/图表/结论汇聚到同一 CLI 中，确保输出统一。

**What you get** – Full-history K-lines, a 90-day Price+MA focus view, interpretable indicator panels (drawdown, Sharpe, BTC–ETH spread z-score, volatility regimes, MA crossovers), and a “last 30 days + next 7 days” forecast.  
**交付**：历史 K 线、90 天 Price+MA 视图、指标面板（滚动回撤/夏普/BTC-ETH 价差 z-score/波动率 Regime/MA 交叉）、“过去 30 天 + 未来 7 天” 预测图。

## Objectives & Scope 目标与范围

- **Goal 目标**：Deliver a 10-minute bilingual deck/report where investors immediately know whether to lean long, lean short, or wait on BTC/ETH/SOL.  
- **Scope 范围**：数据抓取、指标计算、可视化、预测、信号解释、Excel/图像导出；未来可拓展至更多资产、策略和交互式仪表盘。

## Repository Layout 项目结构

```
data/             Fresh CSV generated every CLI run / 每次 CLI 运行生成的最新 CSV
src/              Data loading, analytics, viz, modelling modules / 数据加载、分析、可视化、建模模块
main.py           CLI entry point / CLI 入口
figures/, exports/  Generated PNG/HTML/XLSX (gitignored) / 生成物（已忽略）
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
   > If PowerShell blocks scripts, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.  
   > 如被 PowerShell 阻止脚本，管理员身份执行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。

2. **Install dependencies 安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
   Windows 可用 `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` 确保使用虚拟环境。

3. **Run the CLI 运行 CLI**（每次都会重新下载 yfinance 数据并覆盖 `data/*.csv`）
   ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 2000 --interval 1d \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
   - `--days ≥ 2000` so each asset has足够历史。  
   - CLI 会在 `figures/` 生成 Matplotlib PNG + Plotly HTML，在 `exports/` 输出 Excel，总结信号到终端。
   - `--force` 保留但已无效果，因为现在默认就会覆盖下载。

## Handling yfinance Rate Limits 处理 yfinance 限流

Because `download_price_history` now **always** re-fetches from yfinance, frequent CLI runs may trigger `429 Too Many Requests`. Reduce back-to-back executions, stagger symbols, or rotate networks if necessary.  
由于 `download_price_history` 现已强制重下 yfinance，频繁运行 CLI 可能触发 429，建议降低运行频率或切换网络/IP。

## Outputs at a Glance 输出一览

- **Excel price sheet Excel 价格表**：`exports/...xlsx` 包含 OHLCV、`change_abs/pct`、滚动波动率/回撤/Sharpe、MA 信号，便于课堂或 PPT 二次分析。
- **Interactive K-line 交互 K 线**：Plotly HTML 展示 O/H/L/C + 当日涨跌额/幅，可直接嵌入网页或附录。
- **90-day Price vs MA 价格+均线图**：`figures/<symbol>_price.png` 标注多空区间、MA7/MA30、成交量，直接贴入报告。
- **Indicator panel 指标面板**：`figures/<symbol>_indicator_panel.png` 显示波动率 Regime、滚动回撤、滚动 Sharpe，并给出“lean long / wait / lean short”文案。
- **Short-term forecast 短期预测图**：`figures/<symbol>_forecast_next7.png` 对比最近 30 天实值与未来 7 天预测，突出潜在拐点。
- **CLI signal snapshot CLI 信号快照**：终端输出最新 regime、drawdown、Sharpe、MA 状态、BTC-ETH z-score 及操作建议。

## Roadmap & Alignment 后续计划

| Track 方向 | Why 价值 | Deliverables 交付 |
| --- | --- | --- |
| Narrative & objectives 叙事与目标 | Keep everyone aligned to “10-minute trend briefing”. 紧扣“10 分钟简报”。 | README、persona、成功指标、CLI 文案。 |
| Data spine 数据骨干 | Clean pipelines keep input可信。 | 稳定的 BTC/ETH/SOL yfinance 下载、schema 文档、校验脚本。 |
| Indicators & insight 指标洞察 | Investors need interpretable triggers. 投资者需要可解释触发器。 | 滚动回撤/Sharpe/波动率 regime/BTC-ETH z-score/MA 交叉，含图含文本。 |
| Visualization & dashboard 可视化 | Visuals speed up storytelling. 视觉化更易说服。 | Price/MA、指标面板、短期预测等图表（PNG/HTML）。 |
| Modeling & strategy 建模策略 | Answer “what’s next”. 回答“之后怎么走”。 | LR/ARIMA/Prophet/LSTM，MA 交叉/收益策略，资金曲线/混淆矩阵。 |

## Team Roles 团队分工

1. **Repo structure & data ingestion (dyx)** – Owns repo layout, dependencies, and `src/data_loader.py`; 确保 yfinance 下载与 Excel 导出稳定。
2. **Data processing & indicator insight（li）** – 扩展 `src/analysis.py`，维护衍生字段/信号，并校验 CLI 与指标面板说明的准确性。
3. **Matplotlib visualizations (hy)** – 打磨 Price/MA 图与指标面板样式，保证 PNG 可直接用于汇报。
4. **Plotly & HTML visualizations（ss）** – 负责 Plotly K 线及其他交互式输出，支撑 Web/PPT 嵌入。
5. **Modeling & forecasting (csn)** – 迭代 LR/ARIMA/Prophet/LSTM，管理训练与 checkpoint，提供预测洞察。
6. **Matplotlib forecast graphics (nn)** – 聚焦预测相关 PNG（如 `forecast_next7`），统一配色/标注以便讲解。

> 每位成员的交付都要回扣“10 分钟趋势简报”这一目标，确保 README、PPT 与 CLI 输出保持同一故事线。  
> Each person anchors their work to the “10-minute trend briefing” narrative so docs, PPT, and CLI stay perfectly aligned.
