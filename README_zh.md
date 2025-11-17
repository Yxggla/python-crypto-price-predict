# 加密货币趋势分析与预测

本项目提供一套可复现的工作流，用于下载、分析、可视化与建模主流加密货币的时间序列数据。目标是满足 COMM7330 课程要求，并支撑 6 人小组在数据采集、探索性分析、建模、可视化、报告与展示上的协同。

## 问题定义与目标

面向散户的加密投资者在建仓/减仓前常常需要在多个应用间切换，以回答三个问题：**市场是否在趋势中？波动率是否可接受？辅助信号能否佐证直觉？**  
我们新版的 10 分钟展示要做到：把 yfinance 的日 K 线、最近 90 天的 Price/MA+成交量特写、滚动最大回撤/夏普/BTC-ETH 价差 z-score/波动率 Regime/MA 交叉等指标，以及“接下来怎么走、如何操作”的预测洞察统一在一个仪表盘 + 报告中，帮投资者快速判断 **进入、持有或退出 BTC/ETH**。下文所有交付物都围绕这一核心目标。

## 项目结构

```
data/             # 每次运行 CLI 生成的最新 CSV
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
   **Windows PowerShell**
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   **Windows CMD**
   ```cmd
   py -3 -m venv .venv
   .\.venv\Scripts\activate.bat
   ```
   > **PowerShell 提示**：首次执行 `Activate.ps1` 如果提示 *“running scripts is disabled on this system”*，请以管理员身份打开 PowerShell（一次即可），运行：
   > ```powershell
   > Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   > ```
   > 然后重新执行 `.\.venv\Scripts\Activate.ps1`。切换回 CMD 的话直接使用 `activate.bat`，无需修改策略。
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
   在 Windows 上若想确保使用虚拟环境内的 pip，可以运行：
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. 运行 CLI，一次性完成 yfinance OHLCV 下载、图表、指标面板与建模。`--days` 建议设置为 **2000+**，保证每个币种都有足够历史。CLI 默认会覆盖 `data/*.csv`：
   ```bash
   python main.py --symbols BTC-USD ETH-USD SOL-USD --days 2000 --interval 1d \
     --export-xlsx exports/crypto_dashboard.xlsx
   ```
运行结束后 `data/` 会被最新结果覆盖，无需手动清缓存。Windows 可使用 `py -3 main.py ...`。
程序会自动生成 Matplotlib PNG（Price/MA、指标面板、预测图）与 Plotly HTML K 线，并在终端输出信号。`--force` 保留但默认行为已是强制更新。

### yfinance 限流注意事项

- 由于 `download_price_history` 每次都会访问 yfinance，如果短时间内多次运行 CLI，有可能触发 `Too Many Requests`。建议减少频繁实验或切换不同网络。
- 如需备用数据源，可自行编写脚本拉取其他交易所数据并保存到 `data/*.csv`，但默认 CLI 会在下一次运行时用 yfinance 覆盖。

## 模块概览

- `src/data_loader.py` —— 统一封装 yfinance 价格下载逻辑，每次运行都会拉取并输出最新 CSV。
- `src/analysis.py` —— 计算日收益、滚动波动率、跨资产相关性，以及从首开到末收的整体涨跌幅。
- `src/visualization.py` —— 提供价格 + 成交量、多均线、蜡烛图、预测对比等 Matplotlib/Plotly 辅助函数。
- `src/model.py` —— 实现线性回归基线与 ARIMA，后续可扩展到 Prophet/LSTM。

## 数据采集速查

> **环境准备**
> - `requirements.txt` 已包含 yfinance / requests 相关依赖，开箱即用。
>
> CLI 默认会调用这些助手函数：
> - yfinance —— 提供 `--symbols` 中每个币种的 OHLCV 历史，驱动价格图、收益统计、模型训练。
>
> 下面的示例更适合单独脚本调试。

### 数据来源速览

- **yfinance**：BTC-USD、ETH-USD、SOL-USD 等所有价格序列。

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
3. *（预留）* 当前 CLI 仅依赖 yfinance，如需新增数据源或指标，可在此扩展。

## 输出一览

- **Excel 价格表**：`prices` 工作表中除了原有 K 线列，还新增 `change_abs`（= Close − Open）与 `change_pct`（相对当日开盘的涨跌百分比），方便在 Excel 中直接筛选涨跌幅。
- **交互式 K 线**：鼠标悬停在任意蜡烛上，会显示 O/H/L/C 以及当天的涨跌额与涨跌幅，无需再手算。
- **价格+均线图（最近 90 天）**：`figures/<symbol>_price.png` 聚焦最近 90 个交易日，区分 Close 相对 MA30 的多/空段落，MA7/MA30 使用虚线叠加，放量日以浅色背景突出，成交量柱则用绿色/红色区分“收涨/收跌”，并将纵轴改成以百万为单位，避免 `1e11` 这类刻度。
- **指标面板**：每次运行还会生成 `figures/<symbol>_indicator_panel.png`，包含 3 个子图：① 价格 + 波动率 Regime 背景，② 滚动最大回撤，③ 滚动 Sharpe，并在下方追加“偏多 / 偏空 / 观望 + 理由”的文字说明，10 分钟内就能读懂信号。
- **短期预测视图**：每个币种会额外生成 `figures/<symbol>_forecast_next7.png`，在同一张图中展示最近 30 天的实际价格与未来 7 天的预测曲线，让可能的拐点一目了然。
- **信号快照**：CLI 会提示最新的波动率 Regime、滚动最大回撤、滚动 Sharpe、MA7/MA30 状态、BTC-ETH 价差 z-score，并直接输出“偏多 / 偏空 / 观望”的文字建议及理由，让用户不必额外跑脚本就能迅速理解下一步动作。

## 对齐目标的扩展计划

| 方向 | 价值 | 具体交付物 |
| --- | --- | --- |
| **叙事与目标** | 始终围绕“10 分钟趋势简报”。 | README + Persona 简报、成功指标，以及 CLI 中的文字信号总结。 |
| **数据骨干** | 干净数据让信号可信。 | 稳定产出 yfinance BTC/ETH/SOL 数据，维护数据字典/校验脚本。 |
| **指标与洞察** | 投资者需要可解释的触发器。 | 在 `src/analysis.py` 扩充滚动回撤、Sharpe、价差 z-score、波动率 Regime、MA 交叉，并让 CLI/面板呈现逻辑。 |
| **可视化与仪表盘** | 视觉化更易说服听众。 | 打磨 Price/MA、指标面板、短期预测等图表，确保可直接放入汇报。 |
| **建模与策略** | 回答“接下来怎么走”。 | 在线性基线外迭代 Prophet/LSTM，完善 MA 交叉/预测收益策略，输出资金曲线、混淆矩阵。 |

## 团队分工（6 人）

1. **A：项目结构 & 数据接入(dyx)**
   - 维护仓库布局、依赖、`src/data_loader.py`，确保 yfinance 下载与 Excel 导出稳定。
2. **B：数据处理 & 指标洞察（li）**
   - 负责 `src/analysis.py` 衍生字段与信号实现，校验 CLI 输出与指标面板说明。
3. **C：图表可视化（Matplotlib）(hy)**
   - 打磨 Price/MA 图、指标面板。
4. **D：图表可视化（Plotly/HTML）（ss）**
   - 维护 Plotly K 线及其他交互式输出。
5. **E：模型与预测(csn)**
   - 在 `src/model.py` 持续优化 LR/ARIMA/Prophet/LSTM，管理训练与 checkpoint。
6. **F：图表可视化（Matplotlib）(nn)**
   - 预测图等 PNG 资产。。
