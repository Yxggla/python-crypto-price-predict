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
3. 运行 CLI，完成数据拉取、指标计算、基线建模与结果预览：
   ```bash
   python main.py --symbols BTC-USD ETH-USD --days 730 --interval 1d
   ```
   - 使用 `--force` 刷新 `data/` 目录中的缓存 CSV。
   - 加上 `--save-figures` 将价格走势、预测对比等图表保存到 `figures/`，方便报告或幻灯片使用。

## 模块概览

- `src/data_loader.py` —— 负责通过 yfinance 下载数据、缓存与读取 CSV。
- `src/analysis.py` —— 计算日收益、滚动波动率与跨资产相关性。
- `src/visualization.py` —— 提供价格 + 成交量、多均线、蜡烛图、预测对比等 Matplotlib/Plotly 辅助函数。
- `src/model.py` —— 实现线性回归基线与 ARIMA，后续可扩展到 Prophet/LSTM。

## 对齐目标的扩展计划

| 方向 | 价值 | 具体交付物 |
| --- | --- | --- |
| **用户故事与目标** | 始终强调“10 分钟内做出入场/出场决策”的场景。 | README + 幻灯片说明 Persona、决策流程以及各模块如何支撑。 |
| **更丰富的数据覆盖** | 入场/出场需要宏观 + 链上信号的确认。 | 扩展 `data_loader.py`：拉取 SOL-USD、BTC.D、FRED 利率、ETH 活跃地址、交易所净流入并缓存。 |
| **更深入的指标** | 让用户看到可解释的信号，而非纯价格曲线。 | 在 `src/analysis.py` 实现滚动最大回撤、夏普比率、BTC-ETH 价差 z-score、波动率 Regime，并标注触发点。 |
| **故事化可视化** | 决策者对视觉信息更敏感。 | Plotly 仪表盘（联动图、Regime 着色、信号注释），CLI `--save-figures` 导出 PNG/GIF。 |
| **模型与策略** | 量化“接下来会怎样”，并指向行动。 | 新增 Prophet 或 LSTM，与 LR/ARIMA 对比；实现 MA 金叉或模型信号回测，输出资金曲线与混淆矩阵。 |
| **叙事型 Notebook** | 证明流程可复现，可供老师审阅。 | 填充 `notebooks/01-03`：包含 Markdown 叙述、保存的结果与与 10 分钟故事对应的标注。 |

## 团队分工（6 人）

1. **A：项目负责人 / 叙事与报告**
   - 维护 README 与幻灯片中的“10 分钟入场/出场”主线，定义成功指标，并确保各模块产出与目标挂钩。
   - 收集并整理所有图表/截图，搭建报告大纲，撰写 10 分钟讲稿与讲者备注。
   - 每周主持同步，记录阻塞事项与决策；在 README 中更新进度和任务清单。

2. **B：数据采集与特征工程**
   - 扩展 `src/data_loader.py` 支持多资产、宏观与链上数据，详细记录 ETL 步骤至 `notebooks/01_data_cleaning.ipynb`。
   - 产出数据字典（字段含义、刷新频率、服务的决策场景）。
   - 编写数据校验脚本（缺失、频率对齐）并在 `data/` 提供示例 CSV。

3. **C：探索性分析与指标设计**
   - 在 `src/analysis.py` 中实现最大回撤、夏普、价差 z-score、波动率 Regime 等信号与阈值。
   - 负责 `notebooks/02_analysis.ipynb`：以 Markdown + 图表讲述指标如何提示好的/坏的入场时机。
   - 输出精炼 Insight 交给 A，用于报告与展示。

4. **D：可视化与仪表盘**
   - 升级 `src/visualization.py`，构建 Plotly 仪表盘：价格/成交量/指标/模型信号联动，并提供 Regime 着色、操作提示。
   - 使用 CLI `--save-figures` 生成可直接嵌入 PPT 的 PNG/GIF，一页即可覆盖关键信息。
   - 与 F 协同，保证 demo 时仪表盘可实时或顺滑播放。

5. **E：建模与回测**
   - 在 `src/model.py` 或新增模块实现 Prophet / LSTM，与线性回归、ARIMA 对比，并在 `notebooks/03_prediction.ipynb` 记录 MAE/MAPE 等指标。
   - 将模型输出转化为“买/卖/观望”规则（如 MA 金叉、预测收益 > 阈值），完成回测，输出资金曲线、命中率表、混淆矩阵。
   - 总结模型在何种情景给出建议以及置信度，供 A 述说策略优劣。

6. **F：集成、CLI 与 Demo 体验**
   - 维护 `main.py` 端到端流程（拉取 → 特征 → 指标 → 模型 → 图表），新增数据源、信号阈值、导出路径等参数。
   - 录制脚本化 CLI 演示（GIF 或终端录像），展示 Persona 如何在 10 分钟内操作系统。
   - 负责打包与复现性（依赖、README 指南、可选 Docker），确保老师能顺利运行。

## 下一步

- 按角色填充 `notebooks/01-03`，补充 Markdown 解读与图形输出。
- 视需要加入自动化测试（如 `pytest`）以覆盖关键数据转换。
- 在完成基线后探索更高阶模型或替代数据源（CoinGecko、链上指标 API 等）。

如需进一步定制任务或时间表，请随时更新本 README 或联系项目负责人。
