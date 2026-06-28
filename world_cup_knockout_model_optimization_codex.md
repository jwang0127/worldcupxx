# 2026 世界杯淘汰赛预测模型优化说明（Codex 执行版）

> 版本：v2-knockout-score-first  
> 更新日期：2026-06-28  
> 适用阶段：32 强淘汰赛、16 强、1/4 决赛、半决赛、三四名决赛、决赛  
> 用途：首页结构调整、淘汰赛预测模型重构、比分优先级上调、晋级剧本分析  
> 声明：仅供娱乐分析、模型复盘和页面展示，不构成购彩建议。

---

## 0. 本次调整总目标

当前项目已经从小组赛进入淘汰赛阶段，原模型中的“小组动机 / 出线压力 / 第三名比较 / 净胜球需求”需要整体切换为“晋级路径 / 对手剧本 / 加时点球 / 体能消耗 / 比分脚本”。

本次不是简单增加淘汰赛页面，而是要完成以下四类改造：

1. 首页结构调整：把此前首页所有日期的小组赛预测全部收进一个选择卡中，卡片名称为“**小组赛预测**”。
2. 首页排行榜调整：移除原首页“小组赛排行榜 / 小组积分榜”大窗口，只展示已经进入淘汰赛的 32 支球队当前战绩数据。
3. 剧本分析升级：每场淘汰赛必须重点展示“赢了下一场踢谁、输了进入什么路径”。
4. 赛程窗口调整：把“明日比赛”窗口改成“未来三天比赛”，所有分组、筛选、日期标题都按北京时间。
5. 比分优先级上调：比分预测不再作为最后辅助项，而是和方向、总进球并列为核心模块，并在页面中靠前展示。

---

## 1. 首页结构改造

### 1.1 小组赛预测收纳为选择卡

首页不再把所有历史日期预测平铺展示。

新增组件：

```text
GroupStagePredictionArchiveCard
```

组件位置：

```text
首页主内容区中上部，位于“淘汰赛今日重点”之后，位于“未来三天比赛”之前或之后均可，但不要占据首屏核心位置。
```

展示逻辑：

```text
卡片标题：小组赛预测
默认状态：折叠 / 只显示选择器
选择方式：日期下拉框、横向日期 tabs、或 segmented control 均可
选择内容：展示对应北京时间日期下的小组赛预测卡片
```

数据组织建议：

```json
{
  "group_stage_archive": {
    "title": "小组赛预测",
    "default_collapsed": true,
    "group_by": "beijing_date",
    "items": [
      {
        "date_bjt": "2026-06-12",
        "label": "6月12日 小组赛预测",
        "match_count": 4,
        "prediction_file": "predictions/group/2026-06-12.json"
      }
    ]
  }
}
```

Codex 执行要求：

- 保留历史小组赛预测内容，不要删除。
- 首页默认不平铺展示所有历史小组赛日期。
- 小组赛历史预测必须通过“选择卡”查看。
- 卡片内可以保留原来的方向、总进球、比分、复盘结果。
- 小组赛预测仍按北京时间日期归档。

---

### 1.2 淘汰赛预测继续按北京时间日期分组

淘汰赛预测不要收进“小组赛预测”卡。

淘汰赛首页展示逻辑：

```text
北京时间日期分组
  ├─ 2026-06-29
  │   └─ South Africa vs Canada
  ├─ 2026-06-30
  │   ├─ Brazil vs Japan
  │   ├─ Germany vs Paraguay
  │   └─ Netherlands vs Morocco
```

字段命名建议：

```json
{
  "stage": "knockout",
  "group_by": "beijing_date",
  "timezone": "Asia/Shanghai",
  "date_label_format": "M月D日 北京时间",
  "matches": []
}
```

必须注意：

- 淘汰赛所有页面标题、分组、未来三天筛选均按北京时间。
- 比赛当地时间可以作为辅助字段展示，但不能用于首页分组。
- 若同一北美当地日期跨到北京时间次日，必须归入北京时间日期。

---

## 2. 首页排行榜窗口改造

### 2.1 移除小组积分榜大窗口

删除或隐藏首页原来的：

```text
小组赛排行榜
小组积分榜窗口
Group Standings Window
```

原因：淘汰赛阶段用户已经不需要完整 12 组排名窗口，首页重点应转向 32 强球队状态和晋级路径。

---

### 2.2 新增 32 强球队状态表

新增组件：

```text
QualifiedTeamsStatsTable
```

组件标题建议：

```text
32强球队当前战绩
```

只展示进入淘汰赛的 32 支球队。

建议展示字段：

| 字段 | 说明 | 是否必须 |
|---|---|---|
| team_name | 球队名 | 必须 |
| team_code | 三字母代码 | 必须 |
| group | 原小组 | 建议 |
| qualifying_path | 出线路径：小组第1 / 小组第2 / 最佳第三名 | 建议 |
| played | 已赛 | 必须 |
| wins | 胜 | 必须 |
| draws | 平 | 必须 |
| losses | 负 | 必须 |
| goals_for | 进球 | 必须 |
| goals_against | 失球 | 建议 |
| goal_difference | 净胜球 | 建议 |
| points | 积分 | 建议 |
| first_knockout_match_id | 首场淘汰赛 game_id | 建议 |

页面上最少展示：

```text
球队 / 代码 / 胜 / 平 / 负 / 进球
```

推荐展示：

```text
球队 / 小组 / 出线路径 / 胜 / 平 / 负 / 进球 / 失球 / 净胜球
```

数据结构建议：

```json
{
  "qualified_teams_stats": [
    {
      "team_name": "England",
      "team_code": "ENG",
      "group": "L",
      "qualifying_path": "Group Winner",
      "played": 3,
      "wins": 3,
      "draws": 0,
      "losses": 0,
      "goals_for": 8,
      "goals_against": 2,
      "goal_difference": 6,
      "points": 9,
      "first_knockout_match_id": "53452565"
    }
  ]
}
```

Codex 执行要求：

- 只取进入淘汰赛的 32 支球队。
- 不再展示 48 队完整小组积分榜。
- 不要展示已经出局球队。
- 表格排序建议：
  1. 当前淘汰赛开赛日期升序；
  2. 同日按比赛时间升序；
  3. 同场按主队、客队顺序。
- 如果缺少最终小组完整数据，允许临时用已有 `standings.json` 或小组赛结果自动汇总，但必须在数据说明中标注。

---

## 3. “明日比赛”改为“未来三天比赛”

### 3.1 新组件名称

将原组件：

```text
TomorrowMatchesCard
```

替换为：

```text
UpcomingThreeDaysMatchesCard
```

页面标题：

```text
未来三天比赛（北京时间）
```

---

### 3.2 时间窗口定义

以北京时间作为唯一筛选口径。

建议逻辑：

```js
const nowBjt = toTimeZone(new Date(), 'Asia/Shanghai')
const start = startOfDay(nowBjt)
const end = addDays(start, 3)

upcomingMatches = matches.filter(match => {
  const kickoffBjt = parseAsiaShanghai(match.kickoff_bjt)
  return kickoffBjt >= start && kickoffBjt < end
})
```

解释：

```text
未来三天 = 从北京时间今日 00:00 起，到第三天 23:59:59 结束。
例如当前为北京时间 6 月 28 日，则窗口覆盖 6 月 28、6 月 29、6 月 30。
```

如果希望更贴近“未来 72 小时”，可以改为：

```js
const start = nowBjt
const end = addHours(nowBjt, 72)
```

但本项目建议使用“自然日三天”，因为更适合每日预测页和国内观赛。

---

## 4. 淘汰赛模型整体升级

## 4.1 核心变化

原小组赛模型偏重：

```text
出线压力、净胜球、第三名比较、末轮动机、轮换风险
```

淘汰赛模型改为偏重：

```text
90分钟比分脚本、晋级概率、加时点球风险、下一轮对手、体能消耗、保守/开放切换点
```

重要原则：

```text
淘汰赛必须把“90分钟赛果”和“最终晋级”分开。
```

示例：

```text
90分钟：1:1
加时/点球：A队晋级
方向：平局保护
晋级：A队 55%
```

不要把“预测晋级 A 队”误写成“90分钟 A 队必胜”。

---

## 4.2 全局权重调整

建议将 `model_state.json` 中淘汰赛阶段权重单独拆出：

```json
{
  "stage": "knockout",
  "global_weights": {
    "odds_market_signal": 0.20,
    "elo_strength_gap": 0.15,
    "recent_form": 0.13,
    "tactical_matchup_structure": 0.14,
    "knockout_path_and_script": 0.14,
    "finishing_goalkeeper_set_piece": 0.09,
    "schedule_fitness_travel": 0.06,
    "external_data": 0.05,
    "metaphysics_independent": 0.04
  }
}
```

调整说明：

- `小组动机/出线压力` 替换为 `knockout_path_and_script`。
- 新增 `finishing_goalkeeper_set_piece`，因为淘汰赛一球胜负、定位球、门将状态、点球能力权重更高。
- 赔率仍是锚，但不能机械站边。
- 玄学独立项保留，但不得压过赔率、实力、战术、比分矩阵。

---

## 4.3 输出优先级调整：比分优先级上调

新版页面输出优先级如下：

| 输出模块 | 权重 | 页面位置 |
|---|---:|---|
| 精确比分脚本 | 0.34 | 核心区靠前 |
| 胜平负方向，90分钟 | 0.24 | 核心区 |
| 总进球区间 | 0.20 | 核心区 |
| 晋级概率 / 下一轮剧本 | 0.17 | 核心区 |
| 风险提示 / 冷门路径 | 0.05 | 补充区 |

必须变化：

```text
旧逻辑：先看方向和小组剧本，再看总进球，最后看比分。
新逻辑：比分脚本前置，与方向、总进球并列；每场必须输出比分概率池。
```

页面展示顺序建议：

```text
1. 推荐比分主脚本
2. 90分钟方向
3. 总进球区间
4. 晋级概率
5. 赢球/输球剧本
6. 冷门比分
7. 加时/点球分歧
```

---

## 5. 比分模型专项升级

### 5.1 每场必须输出 5 类比分

每场淘汰赛必须生成：

| 类型 | 数量 | 说明 |
|---|---:|---|
| 主比分 | 1 | 模型综合概率最高且符合比赛脚本的比分 |
| 稳胆比分 | 2 | 与主方向一致的常规比分 |
| 平局保护比分 | 1-2 | 强弱接近或淘汰赛保守时必须给出 |
| 冷门比分 | 1 | 弱队晋级或强队被拖入加时的路径 |
| 加时/点球比分脚本 | 1 | 90分钟打平后的晋级描述 |

输出示例：

```json
{
  "score_prediction": {
    "main_score": "1-1",
    "safe_scores": ["1-0", "2-1"],
    "draw_protection_scores": ["0-0", "1-1"],
    "upset_score": "0-1",
    "extra_time_penalty_script": "90分钟1-1，A队加时或点球晋级",
    "score_confidence": 0.63
  }
}
```

---

### 5.2 比分矩阵计算要求

Codex 需要把比分从“文案生成”升级为“概率池生成”。

建议流程：

```text
1. 输入双方进攻强度、失球强度、Elo差、赔率隐含概率、大小球赔率。
2. 生成 0-0 到 5-5 的初始比分矩阵。
3. 用淘汰赛修正项压缩或放大尾部。
4. 用战术结构修正低比分 / 高比分概率。
5. 输出 Top 6 比分候选。
6. 从候选中挑选主比分、稳胆比分、平局保护、冷门比分。
```

伪代码：

```js
function buildScoreMatrix(match, features) {
  const baseLambdaHome = estimateExpectedGoals(match.home, match.away, features)
  const baseLambdaAway = estimateExpectedGoals(match.away, match.home, features)

  let matrix = poissonMatrix(baseLambdaHome, baseLambdaAway, { maxGoals: 5 })

  matrix = applyKnockoutCompression(matrix, features.knockout_pressure)
  matrix = applyTacticalTempoAdjustment(matrix, features.tempo)
  matrix = applyOddsGoalLineAdjustment(matrix, features.total_goals_odds)
  matrix = applyDrawProtection(matrix, features.draw_pressure)
  matrix = applyLateGameChaos(matrix, features.must_chase_after_conceding)

  return rankScores(matrix)
}
```

---

### 5.3 淘汰赛比分修正规则

#### 规则 A：强弱差明显，但强队热度过高

```text
倾向：1-0、2-0、2-1
不要默认 3-0、4-0。
```

触发条件：

```text
强队主胜赔率低，但让球没有同步加深；
或强队赛程密集，有留力和控节奏动机。
```

#### 规则 B：双方实力接近

```text
倾向：0-0、1-1、1-0、0-1
必须提高 90分钟平局概率。
```

触发条件：

```text
Elo差小；
平赔低位；
双方淘汰赛风格偏谨慎；
盘口没有明显方向。
```

#### 规则 C：强队控球优势大，但破密集防守能力一般

```text
倾向：1-0、1-1、2-0
比分尾部不宜过高。
```

#### 规则 D：弱队落后必须压上

```text
倾向：2-1、3-1、2-2
允许尾部上修。
```

#### 规则 E：定位球强队 / 门将弱点明显

```text
倾向：1-0、2-1、1-1
提高一球差和定位球破局比分。
```

#### 规则 F：点球能力差异明显

```text
90分钟可给平局，但晋级概率向点球更强一方倾斜。
```

---

## 6. 晋级剧本分析模块

### 6.1 每场必须输出剧本卡

新增组件：

```text
KnockoutScenarioCard
```

每场比赛必须展示：

```text
如果主队晋级：下一轮可能对手是谁
如果客队晋级：下一轮可能对手是谁
如果主队出局：路径是什么
如果客队出局：路径是什么
```

---

### 6.2 剧本字段结构

```json
{
  "scenario": {
    "match_id": "53452545",
    "home_team": "South Africa",
    "away_team": "Canada",
    "winner_advances_to_match_id": "53452511",
    "home_win_script": {
      "result": "South Africa advances",
      "next_match_id": "53452511",
      "next_opponent_source": "Winner of Netherlands vs Morocco",
      "script_label": "南非晋级后，下轮对阵荷兰/摩洛哥胜者"
    },
    "away_win_script": {
      "result": "Canada advances",
      "next_match_id": "53452511",
      "next_opponent_source": "Winner of Netherlands vs Morocco",
      "script_label": "加拿大晋级后，下轮对阵荷兰/摩洛哥胜者"
    },
    "home_loss_script": {
      "result": "South Africa eliminated",
      "script_label": "南非输球即出局"
    },
    "away_loss_script": {
      "result": "Canada eliminated",
      "script_label": "加拿大输球即出局"
    }
  }
}
```

---

### 6.3 不同轮次的输球路径

| 轮次 | 赢球路径 | 输球路径 |
|---|---|---|
| 32 强 | 进入 16 强 | 出局 |
| 16 强 | 进入 8 强 | 出局 |
| 1/4 决赛 | 进入半决赛 | 出局 |
| 半决赛 | 进入决赛 | 进入三四名决赛 |
| 三四名决赛 | 获得季军 | 获得第四名 |
| 决赛 | 冠军 | 亚军 |

半决赛特殊逻辑：

```text
半决赛输球不是直接结束，而是进入三四名决赛。
```

决赛特殊逻辑：

```text
决赛输球为亚军，不再有下一场。
```

三四名决赛特殊逻辑：

```text
赢球季军，输球第四名。
```

---

## 7. 每场淘汰赛预测卡结构

新版每场比赛卡片建议统一结构：

```text
MatchPredictionCard
├─ 比赛基础信息
│   ├─ 轮次
│   ├─ 主队 vs 客队
│   ├─ 当地时间
│   ├─ 北京时间
│   └─ game_id
├─ 核心预测区
│   ├─ 主比分
│   ├─ 稳胆比分
│   ├─ 冷门比分
│   ├─ 90分钟方向
│   ├─ 总进球区间
│   └─ 晋级概率
├─ 剧本分析区
│   ├─ 主队赢了下轮踢谁
│   ├─ 客队赢了下轮踢谁
│   ├─ 主队输了路径
│   └─ 客队输了路径
├─ 加时/点球区
│   ├─ 90分钟平局概率
│   ├─ 加时倾向
│   └─ 点球倾向
└─ 风险提示
    ├─ 热度风险
    ├─ 冷门触发条件
    └─ 数据完整度
```

---

## 8. 淘汰赛输出模板

每场预测文案建议固定为以下格式，方便 Codex 生成 HTML：

```md
### {home_team} vs {away_team}

- 轮次：{round}
- 北京时间：{kickoff_bjt}
- 当地时间：{kickoff_local}
- game_id：{game_id}

#### 核心判断

- 90分钟方向：{home_win/draw/away_win}
- 主比分：{main_score}
- 稳胆比分：{safe_score_1} / {safe_score_2}
- 冷门比分：{upset_score}
- 总进球区间：{goals_range}
- 晋级倾向：{advance_team} 晋级
- 晋级概率：{home_advance_probability}% / {away_advance_probability}%

#### 剧本分析

- {home_team} 赢：进入 {next_match_id}，下轮对阵 {next_opponent_source}
- {away_team} 赢：进入 {next_match_id}，下轮对阵 {next_opponent_source}
- {home_team} 输：{home_loss_path}
- {away_team} 输：{away_loss_path}

#### 比分脚本

- 主脚本：{main_score_script}
- 保守脚本：{conservative_score_script}
- 开放脚本：{open_score_script}
- 加时/点球脚本：{extra_time_penalty_script}

#### 风险提示

- {risk_1}
- {risk_2}
```

---

## 9. 数据层改造建议

### 9.1 knockout_schedule 数据表

建议字段：

```json
{
  "game_id": "53452545",
  "round": "Round Of 32",
  "stage": "knockout",
  "home_team": "South Africa",
  "home_code": "RSA",
  "away_team": "Canada",
  "away_code": "CAN",
  "kickoff_local": "2026-06-28 15:00 EDT",
  "kickoff_bjt": "2026-06-29 03:00 UTC+08",
  "beijing_date": "2026-06-29",
  "winner_advances_to": "53452511",
  "loser_advances_to": null,
  "status": "Scheduled"
}
```

### 9.2 prediction_result 数据表

```json
{
  "game_id": "53452545",
  "generated_at": "2026-06-28T00:00:00+08:00",
  "model_version": "v2-knockout-score-first",
  "direction_90min": "draw",
  "main_score": "1-1",
  "safe_scores": ["1-0", "2-1"],
  "draw_protection_scores": ["0-0", "1-1"],
  "upset_score": "0-1",
  "goals_range": "1-2",
  "home_advance_probability": 0.48,
  "away_advance_probability": 0.52,
  "advance_pick": "Canada",
  "extra_time_penalty_script": "90分钟1-1，加拿大加时/点球小优",
  "score_confidence": 0.61,
  "direction_confidence": 0.56,
  "data_completeness": 0.82
}
```

---

## 10. 页面验收标准

Codex 完成后必须满足：

- [ ] 首页不再平铺所有小组赛日期预测。
- [ ] 小组赛历史预测被收进“**小组赛预测**”选择卡。
- [ ] 淘汰赛预测仍按北京时间日期分组展示。
- [ ] 首页移除完整小组积分榜 / 小组排行榜窗口。
- [ ] 首页新增“32强球队当前战绩”表。
- [ ] 32强表只显示晋级淘汰赛球队。
- [ ] “明日比赛”改为“未来三天比赛（北京时间）”。
- [ ] 每场比赛必须有主比分、稳胆比分、冷门比分。
- [ ] 每场比赛必须区分 90分钟方向 和 最终晋级。
- [ ] 每场比赛必须有“赢了下轮踢谁 / 输了进入什么路径”。
- [ ] 半决赛输球路径必须进入三四名决赛，不得写成直接出局。
- [ ] 决赛输球路径必须写亚军，不得写出局。
- [ ] 比分模块在页面上必须前置，不能放到最后作为附属内容。

---

## 11. 禁止事项

- 禁止把淘汰赛 90分钟平局直接当成某队出局。
- 禁止只输出胜平负，不输出比分池。
- 禁止只写“胜者晋级”，不写下一轮对手来源。
- 禁止继续在首页展示 48 队完整小组积分榜大窗口。
- 禁止将淘汰赛按北美当地日期分组，必须按北京时间。
- 禁止删除历史小组赛预测数据。
- 禁止把比分预测隐藏在折叠区最底部。
- 禁止让玄学项覆盖赔率、实力、战术、比分矩阵的主判断。

---

## 12. 推荐实现顺序

1. 新建 `v2-knockout-score-first` 配置，不覆盖原小组赛模型。
2. 整理 `knockout_schedule`，补齐 `beijing_date`、`winner_advances_to`、`loser_advances_to`。
3. 新增 `QualifiedTeamsStatsTable`，替换首页小组积分榜。
4. 新增 `GroupStagePredictionArchiveCard`，收纳历史小组赛预测。
5. 将 `TomorrowMatchesCard` 改造为 `UpcomingThreeDaysMatchesCard`。
6. 重构每场预测输出结构，前置比分模块。
7. 新增 `KnockoutScenarioCard`，输出赢球/输球路径。
8. 回归测试 32 强、16 强、1/4 决赛、半决赛、决赛的路径逻辑。
9. 生成页面并检查北京时间分组是否正确。
10. 更新 README 或页面底部模型说明。

---

## 13. 新版模型一句话总结

```text
淘汰赛阶段不再以小组出线压力为核心，而是以“90分钟比分脚本 + 最终晋级路径 + 下一轮对手剧本”为核心；比分预测前置，方向和总进球作为交叉验证，所有比赛按北京时间日期组织。
```
