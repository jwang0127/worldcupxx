# 淘汰赛预测模型 v3

生成时间：2026-06-28

## 固定输入

- 赛程主源：`2026世界杯淘汰赛赛程表_中文版_Codex.md`
- Excel 校验：`2026世界杯淘汰赛赛程表_中文版_Codex.xlsx`
- 淘汰赛模型底稿：`world_cup_knockout_model_optimization_codex.md`
- 复盘执行手册：`SHAREABLE_PREDICTION_REVIEW_LOGIC.md`
- 分享说明：`1.md`

## 强制校验

- 赛程 Markdown 为主源，Excel 为一致性校验
- 主客队、北京时间、当地时间、晋级路径必须逐项校验
- 主模型和玄学面板彻底分离，玄学不进入综合评分
- 输出必须含 90分钟胜平负、半场方向、最终晋级、比分 EV

## 权重

- `elo_strength`: 22%
- `group_stage_form`: 18%
- `attack_defense_xg`: 18%
- `odds_implied_market`: 16%
- `knockout_script`: 12%
- `injury_discipline`: 6%
- `schedule_rest_travel`: 4%
- `review_bias_correction`: 4%

## EV 规则

- EV = model_probability * market_decimal_odds - 1
- 无真实赔率时只输出模型 EV 倾向，不给出下注指令
- 比分 EV 以 Top6 覆盖为主，冷门比分单独标注，不覆盖主线

## 三串一生成规则

- 当日预测场次正好为 3 场时，生成 `比分三串一、总进球数三串一、半全场胜负平三串一` 三个三串一模块。
- 三串一赔率只从网站实时赔率数据读取：`Sporttery getMatchCalculatorV1 website API via scripts/fetch_sporttery.ps1`。
- 必须同时匹配 `crs、ttg、hafu` 三类赔率；缺任一市场或无法匹配场次时，不输出三串一模块。
- 当日只有 1 场比赛时，只输出常规预测，不生成三串一。

## 首场输出

- 比赛：南非 vs 加拿大
- 半场：0-0，方向 平
- 90分钟：1-1，方向 90分钟平局保护
- 晋级：加拿大
- Elo：1622 - 1708
- xG：1.02 - 1.16

## 玄学隔离

玄学面板只保留为娱乐表达，不进入 Elo、EV、半场、胜平负、比分概率和晋级概率。
