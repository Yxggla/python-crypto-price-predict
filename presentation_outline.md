# PPT Outline / 汇报提纲

10‑minute group presentation with six speakers, ~2 slides each. Focus on **what the project does, which technologies we used, why it matters, the workflow diagram, and individual contributions.**

## Agenda 概览

| Time | Slide(s) | Speaker | Content 摘要 |
| --- | --- | --- | --- |
| 0:00‑1:30 | 1‑2 | dyx | Title, team intro, problem/goal summary |
| 1:30‑3:00 | 3‑4 | dyx | Data sources + tech stack overview |
| 3:00‑4:30 | 5‑6 | li | Indicators & analytics logic |
| 4:30‑6:00 | 7‑8 | hy | Visualization outputs + storytelling |
| 6:00‑7:15 | 9‑10 | csn | Modelling & forecasting insights |
| 7:15‑8:30 | 11‑12 | nn | Strategy integration + overall flowchart |
| 8:30‑10:00 | 13‑14 | All | Rapid-fire individual highlights + Q&A buffer |

## Slide-by-slide Details 逐页要点

1. **Cover / 封面** (dyx)  
   - Project title, team name, members.  
   - Key value proposition: “10-minute cryptocurrency trend briefing.”
2. **Problem & Objective / 痛点与目标** (dyx)  
   - Pain points: fragmented data, uncertainty about trend/volatility/signals.  
   - Objective statement linking to investors’ quick decisions.
3. **Data Sources / 数据来源** (dyx)  
   - yfinance OHLCV + OKX dominance; mention caching strategy.  
   - Diagram/token logos to keep it visual.
4. **Tech Stack / 技术栈** (dyx)  
   - Python, Pandas, Matplotlib, Plotly, statsmodels/Prophet, CLI automation.  
   - Highlight reproducible CLI workflow.
5. **Indicator Design / 指标设计** (li)  
   - Rolling drawdown, Sharpe, volatility regime, MA crossovers.  
   - Rationale for each metric (interpretability, actionability).
6. **Signal Recommendation Logic / 信号决策逻辑** (li)  
   - How indicators combine into “lean long / wait / lean short.”  
   - Showcase snippet from CLI output or decision table.
7. **Matplotlib Visuals / 静态可视化** (hy)  
   - 90-day Price+MA chart anatomy, volume shading, bull/bear regimes.  
   - Screenshot/mock-up emphasising export-ready design.
8. **Indicator Panel & Forecast PNG / 指标面板 + 预测图** (hy)  
   - Explain layout of indicator panel and 30+7 forecast chart.  
   - Mention styling choices that aid storytelling.
9. **Modelling Approach / 建模方法** (csn)  
   - Models tried (LR/ARIMA/Prophet/LSTM), feature set, validation.  
   - Why Prophet/LSTM chosen (or lessons learned).
10. **Forecast Insights / 预测洞察** (csn)  
    - Example forecast vs actual, interpretation of next 7 days.  
    - Limitations + future improvements.
11. **Workflow Diagram / 项目流程图** (nn)  
    - End-to-end pipeline: data ingestion → processing → analytics → viz → model → strategy → exports.  
    - Use arrows/icons, highlight feedback loops.
12. **Strategy Integration / 策略整合** (nn)  
    - How outputs feed MA crossover / trading playbook, Excel exports, PPT assets.  
    - Emphasise reproducible CLI demo.
13. **Individual Highlights / 个人亮点** (all, 30s each)  
    - Each member states contribution + biggest challenge solved.  
    - Keep one shared slide with six columns or bullets.
14. **Wrap-up & Q&A / 总结与问答** (lead by dyx)  
    - Reiterate objective, key takeaways, next steps.  
    - Hold final 60‑90 seconds for questions.

## Flowchart Guidance 流程图提示

- Nodes: Data Sources → Data Loader → Indicator Engine → Visualization Layer → Modelling → Strategy Output → Deliverables (PPT/Excel/CLI).  
- Annotate technologies per step (e.g., `Pandas`, `Matplotlib`, `Prophet`).  
- Highlight parallel paths (visualisation & modelling) converging into final recommendation.

## Presenter Tips 演讲提示

1. Open with the “10-minute briefing” narrative so everyone understands why the workflow matters.  
2. Use the CLI screenshots/figures as visual anchors; avoid dense text.  
3. Transition cues: each speaker references the previous one (“As li’s signals show…”) to keep flow tight.  
4. Keep bilingual captions where needed (English titles + Chinese subtitles) to match README and rubric.  
5. Timebox rehearsals: target 75 seconds per speaker, leaving a 90-second Q&A buffer.
