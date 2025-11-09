# 加密货币趋势分析与预测

本项目提供一套可复现的工作流，用于下载、分析、可视化与建模主流加密货币的时间序列数据。目标是满足 COMM7330 课程要求，并支撑 6 人小组在数据采集、探索性分析、建模、可视化、报告与展示上的协同。

## 问题定义与目标

面向散户的加密投资者在建仓/减仓前常常需要在多个应用间切换，以回答三个问题：**市场是否在趋势中？波动率是否可接受？辅助信号能否佐证直觉？**  
我们 10 分钟的展示（以及支撑它的系统）必须帮助“新手投资者”在单一仪表盘 + 报告中判断 **进入、持有或退出 BTC/ETH** 的最佳时机。下文所有交付物都要围绕这一核心目标。

## 项目结构

```
data/             # 通过 yfinance 缓存的 CSV
notebooks/        # 分阶段的 Jupyter Notebook（由各角色撰写）
src/              # 数据加载、分析、可视化、建模模块
main.py           # 端到端 CLI 入口
requirements.txt  # 依赖列表
```

## 快速开始

1. 创建并激活虚拟环境（示例 `venv`）：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置必要的 API Key（当前需要 CoinMarketCap）。可以直接 `export`，或在 `.env` 文件中写入并 `source`：
   ```bash
   # 方式 A：直接 export
   export COINMARKETCAP_API_KEY="<你的 CoinMarketCap Key>"

   # 方式 B：写入 .env 并加载
   echo 'COINMARKETCAP_API_KEY="<你的 CoinMarketCap Key>"' >> .env
   set -a; source .env; set +a
   ```
4. 运行 CLI，完成数据拉取、指标计算、基线建模与结果预览：
   ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 730 --interval 1d \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
   - 使用 `--force` 刷新 `data/` 目录中的缓存 CSV。
   - 加上 `--save-figures` 将价格走势、预测对比等图表保存到 `figures/`，方便报告或幻灯片使用。
   - `--quiet` 可关闭 CLI 中的表格打印，直接生成缓存文件/图表。
   - `--macro-series DGS10`（或 `--macro-series none`）控制 FRED 指标，`--dominance-inst-id BTC-USDT` 切换 OKX 优势代理，`--skip-cmc` 可跳过 CoinMarketCap 下载。

## 模块概览

- `src/data_loader.py` —— 覆盖 yfinance 价格、OKX BTC-USDT 蜡烛（用作 BTC.D 代理）、FRED 宏观序列及 CoinMarketCap 全球/资产指标，统一缓存到 CSV。
- `src/analysis.py` —— 计算日收益、滚动波动率与跨资产相关性。
- `src/visualization.py` —— 提供价格 + 成交量、多均线、蜡烛图、预测对比等 Matplotlib/Plotly 辅助函数。
- `src/model.py` —— 实现线性回归基线与 ARIMA，后续可扩展到 Prophet/LSTM。

## 数据采集速查

> **环境准备**
> - `requirements.txt` 已包含 `pandas-datareader`，用于 FRED 拉取。
> - 使用 CoinMarketCap 时，请先 `export COINMARKETCAP_API_KEY=<你的密钥>`（或在 `.env` 中加载）。
>
> CLI 默认会调用这些助手函数（OKX BTC-USDT 优势代理、FRED、CoinMarketCap），并可通过 `--export-xlsx` 一次性导出 Excel。下面的示例更适合单独 Notebook 或脚本调试。

1. **币价历史（BTC / ETH / SOL）**  
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
2. **BTC.D 优势代理（OKX BTC-USDT 蜡烛）**  
   ```python
   from src.data_loader import OkxCandlesConfig, download_okx_candles
   download_okx_candles(OkxCandlesConfig(inst_id="BTC-USDT", bar="1D"))
   ```
   生成的 CSV 含 `date, open, high, low, close, volume_base`。
3. **宏观序列（示例：联邦基金利率 FEDFUNDS）**  
   ```python
   from src.data_loader import MacroSeriesConfig, download_macro_series
   download_macro_series(MacroSeriesConfig(series_id="FEDFUNDS", start="2010-01-01"))
   ```
   如 FRED 要求 API Key，可在 config 里传 `api_key` 或设置 `FRED_API_KEY`。
4. **CoinMarketCap 指标（全球市值 + 即时报价）**  
   ```python
   from src.data_loader import (
       CoinMarketCapGlobalConfig,
       CoinMarketCapAssetConfig,
       download_cmc_global_metrics,
       download_cmc_asset_quotes,
   )

   download_cmc_global_metrics(CoinMarketCapGlobalConfig(convert="USD"))
   download_cmc_asset_quotes(CoinMarketCapAssetConfig(symbols=["BTC", "ETH", "SOL"], convert="USD"))
   ```
   需要 `COINMARKETCAP_API_KEY`。全球 CSV 提供总市值、主导率、成交量；报价 CSV 则包含各币种价格、市值与涨跌幅。

## 对齐目标的扩展计划

| 方向 | 价值 | 具体交付物 |
| --- | --- | --- |
| **叙事与目标** | 确保团队始终围绕“10 分钟判断入/出场”推进。 | README + Persona 简报、成功指标、Notebook 中指向 PPT 的小结。 |
| **多源数据骨干** | 市值占比 + 宏观背景让信号更可信。 | 让 CLI/Excel 稳定输出 BTC/ETH/SOL、OKX BTC-USDT 蜡烛、FRED FEDFUNDS + DGS10、CoinMarketCap 全球/报价，并编制数据字典与校验脚本。 |
| **指标与宏观洞察** | 投资者需要可解释的触发器。 | 在 `src/analysis.py` 加滚动最大回撤、夏普、BTC-ETH 价差 z-score、波动率 Regime、MA 交叉，并在 Notebook 02 解释触发逻辑。 |
| **可视化与仪表盘** | 视觉化更易说服听众。 | 构建价格/优势/宏观/模型叠加的 Plotly Dashboard，提供 Regime 标注与 PNG/GIF 导出，直接用于 PPT。 |
| **建模与策略** | 回答“接下来怎么走、如何操作”。 | 在线性基线外实现 Prophet/LSTM，对比误差；实现 MA 交叉 + 预测收益策略，输出资金曲线、命中率、混淆矩阵。 |
| **Notebook 讲故事** | 最终 PPT/报告直接引用 Notebook。 | 在 `notebooks/01-03` 写完整 Markdown 解读、保存图表/表格，并注明对应的 PPT 章节。 |

## 团队分工（6 人）

1. **A：数据接入负责人(dyx)**
   - 负责 `src/data_loader.py` + CLI，确保 BTC/ETH/SOL、OKX 优势蜡烛、FRED、CoinMarketCap 下载稳定并去除时区。
   - 在 Notebook 01 编写 ETL、数据字典与校验脚本，并维持 Excel 导出结构。
2. **B：特征工程与清洗(shanshan)**
   - 在 Notebook 01 和 `src/analysis.py` 实现收益、宏观合并、价差等衍生字段，并写小测试验证样例行。
   - 将清洗后的数据交付给指标/建模同学使用。
3. **C：指标与宏观洞察(li)**
   - 在 `src/analysis.py` 增加最大回撤、夏普、波动 Regime、BTC-ETH z-score、MA 触发等函数，并在 Notebook 02 用代码+图表解释。
   - 输出可引用的 Insight 与图像并标注对应代码单元。
4. **D：可视化工程(nyc)**
   - 扩展 `src/visualization.py`（Plotly + Matplotlib），构建叠加价格/优势/宏观/模型信号的 Dashboard，提供导出脚本。
   - 通过 CLI `--save-figures` 或 Notebook 生成 PNG/GIF，并说明如何用 Excel 数据复现。
5. **E：建模算法(csn)**
   - 负责 Notebook 03 / `src/model.py` 中的模型结构（LR/ARIMA 基线、Prophet/LSTM），调参并保存可复用的 checkpoint 或推理脚本。
   - 记录训练与评估流程，方便他人复现指标或替换模型。
6. **F：策略与流水线集成(hy)**
   - 将 E 生成的预测接入回测与导出层：在 `main.py` / Excel 导出里把 MA 交叉、预测收益策略等指标串联起来。
   - 编写 CLI/脚本展示完整流程（数据→指标→模型→策略输出），并核对每次运行是否产出预期的 CSV/Excel/图表。
