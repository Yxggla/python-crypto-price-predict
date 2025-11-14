# 加密货币趋势分析与预测

本项目提供一套可复现的工作流，用于下载、分析、可视化与建模主流加密货币的时间序列数据。目标是满足 COMM7330 课程要求，并支撑 6 人小组在数据采集、探索性分析、建模、可视化、报告与展示上的协同。

## 问题定义与目标

面向散户的加密投资者在建仓/减仓前常常需要在多个应用间切换，以回答三个问题：**市场是否在趋势中？波动率是否可接受？辅助信号能否佐证直觉？**  
我们新版的 10 分钟展示要做到：把 yfinance 的日 K 线、最近 90 天的 Price/MA+成交量特写、滚动最大回撤/夏普/BTC-ETH 价差 z-score/波动率 Regime/MA 交叉等指标，以及“接下来怎么走、如何操作”的预测洞察统一在一个仪表盘 + 报告中，帮投资者快速判断 **进入、持有或退出 BTC/ETH**。下文所有交付物都围绕这一核心目标。

## 项目结构

```
data/             # 缓存 yfinance / OKX 拉取的 CSV
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
3. 运行 CLI，一次性完成 yfinance OHLCV、OKX 优势蜡烛、图表、指标面板与模型。`--days` 请设置为 **2000 及以上**，保证每个币种都有 >2000 条历史记录：
   ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 2000 --interval 1d \
     --dominance-inst-id BTC-USDT \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
   程序会自动生成 Matplotlib PNG（含 Price/MA 与指标面板）、Plotly HTML，并弹出交互式图表；`--force` 会强制重拉 CSV，`--dominance-inst-id` 用于切换 OKX 配置。

## 模块概览

- `src/data_loader.py` —— 统一封装 yfinance 价格与 OKX BTC-USDT 蜡烛，全部缓存为 CSV。
- `src/analysis.py` —— 计算日收益、滚动波动率、跨资产相关性，以及从首开到末收的整体涨跌幅。
- `src/visualization.py` —— 提供价格 + 成交量、多均线、蜡烛图、预测对比等 Matplotlib/Plotly 辅助函数。
- `src/model.py` —— 实现线性回归基线与 ARIMA，后续可扩展到 Prophet/LSTM。

## 数据采集速查

> **环境准备**
> - `requirements.txt` 已包含 yfinance / requests 相关依赖，开箱即用。
>
> CLI 默认会调用这些助手函数：
> - yfinance —— 提供 `--symbols` 中每个币种的 OHLCV 历史，驱动价格图、收益统计、模型训练；
> - OKX 公共 API —— 通过 `download_okx_candles` 提供 BTC-USDT 优势蜡烛 (`open/high/low/close/volume_base`)，用于 dominance 相关导出。
>
> 下面的示例更适合单独脚本调试。

### 数据来源速览

- **yfinance**：BTC-USD、ETH-USD、SOL-USD 等所有价格序列。
- **OKX**：BTC-USDT dominance 蜡烛，仅用于优势度可视化/导出。

1. **币价历史（yfinance）**  
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
2. **BTC.D 优势代理（OKX BTC-USDT 蜡烛）**  
   ```python
   from src.data_loader import OkxCandlesConfig, download_okx_candles
   download_okx_candles(OkxCandlesConfig(inst_id="BTC-USDT", bar="1D"))
   ```
   生成的 CSV 含 `date, open, high, low, close, volume_base`。
3. *（预留）* 当前 CLI 仅依赖 yfinance + OKX，如需新增指标，可在此扩展。

## 输出一览

- **Excel 价格表**：`prices` 工作表中除了原有 K 线列，还新增 `change_abs`（= Close − Open）与 `change_pct`（相对当日开盘的涨跌百分比），方便在 Excel 中直接筛选涨跌幅。
- **交互式 K 线**：鼠标悬停在任意蜡烛上，会显示 O/H/L/C 以及当天的涨跌额与涨跌幅，无需再手算。
- **价格+均线图（最近 90 天）**：`figures/<symbol>_price.png` 聚焦最近 90 个交易日，区分 Close 相对 MA30 的多/空段落，MA7/MA30 使用虚线叠加，放量日以浅色背景突出，成交量柱则用绿色/红色区分“收涨/收跌”，并将纵轴改成以百万为单位，避免 `1e11` 这类刻度。
- **指标面板**：每次运行还会生成 `figures/<symbol>_indicator_panel.png`，包含 3 个子图：① 价格 + 波动率 Regime 背景，② 滚动最大回撤，③ 滚动 Sharpe，并在下方追加“偏多 / 偏空 / 观望 + 理由”的文字说明，10 分钟内就能读懂信号。
- **信号快照**：CLI 会提示最新的波动率 Regime、滚动最大回撤、滚动 Sharpe、MA7/MA30 状态、BTC-ETH 价差 z-score，并直接输出“偏多 / 偏空 / 观望”的文字建议及理由，让用户不必额外跑脚本就能迅速理解下一步动作。

## 对齐目标的扩展计划

| 方向 | 价值 | 具体交付物 |
| --- | --- | --- |
| **叙事与目标** | 确保团队始终围绕“10 分钟判断入/出场”推进。 | README + Persona 简报、成功指标，以及直接落地的图表/信号小结。 |
| **多源数据骨干** | 市场占比背景让信号更可信。 | 让 CLI/Excel 稳定输出 yfinance BTC-USD/ETH-USD/SOL-USD 与 OKX BTC-USDT 蜡烛，并编制数据字典与校验脚本。 |
| **指标与洞察** | 投资者需要可解释的触发器。 | 在 `src/analysis.py` 持续扩充滚动最大回撤、夏普、BTC-ETH 价差 z-score、波动率 Regime、MA 交叉，并让 CLI/指标面板直接解释触发逻辑。 |
| **可视化与仪表盘** | 视觉化更易说服听众。 | 构建价格/优势/模型叠加的 Plotly Dashboard 与 Matplotlib 面板，输出 PNG/GIF，直接用于 PPT。 |
| **建模与策略** | 回答“接下来怎么走、如何操作”。 | 在线性基线外实现 Prophet/LSTM，对比误差；实现 MA 交叉 + 预测收益策略，输出资金曲线、命中率、混淆矩阵。 |

## 团队分工（6 人）

1. **A：数据接入负责人(dyx)**
   - 负责 `src/data_loader.py` + CLI，确保 yfinance BTC/ETH/SOL 与 OKX 优势蜡烛下载稳定并去除时区。
   - 维护 CLI / Excel 导出结构及数据字典。
2. **B：特征工程与清洗(shanshan)**
   - 直接在 `src/analysis.py` 实现收益、价差等衍生字段，并写小测试验证样例行。
3. **C：指标与洞察(li)**
   - 在 `src/analysis.py` 增加最大回撤、夏普、波动 Regime、BTC-ETH z-score、MA 触发等函数，并确保 CLI/指标面板文字说明准确。
4. **D：可视化工程(nyc)**
   - 扩展 `src/visualization.py`（Plotly + Matplotlib），构建叠加价格/优势/模型信号的 Dashboard，输出 PNG/GIF。
5. **E：建模算法(csn)**
   - 负责 `src/model.py` 中的模型结构（LR/ARIMA 基线、Prophet/LSTM），调参并保存可复用的 checkpoint 或推理脚本。
6. **F：策略与流水线集成(hy)**
   - 将 E 生成的预测接入回测与导出层：在 `main.py` / Excel 导出里把 MA 交叉、预测收益策略等指标串联起来，编写 CLI 演示脚本并确认产出一致。
