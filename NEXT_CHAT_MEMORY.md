# 新对话记忆文档：世界杯预测看板

请在新对话中先读取本文件，再继续执行。当前项目根目录：

`C:\Users\Administrator\Documents\世界杯预测`

## 用户核心目标

用户要的是“每日世界杯预测看板”，不是流程图、不是单独模型页、不是单独玄学页。每天根据世界杯赛程和竞彩足球赔率，生成当天 4 场比赛的独立 HTML 看板，并推送到 GitHub Pages。

发布地址：

`https://jwang0127.github.io/worldcupxx/`

GitHub 仓库：

`https://github.com/jwang0127/worldcupxx.git`

## 用户明确偏好

- 页面必须是中文，不能乱码。
- 页面顶部要有“今天该买什么/今日预测结果”的汇总表。
- 每场比赛都必须有详细分析，不能只有标题或套话。
- 分析维度必须包括：基本面、战术与教练、外部因素、小组形势、赔率解读。
- 玄学预测必须嵌入每场比赛卡片中，不要单独拆成页面。
- 玄学分析要写得充分，覆盖周易梅花/六爻、紫微斗数、奇门遁甲、干支五行、九宫飞星、诸葛神数/塔罗/民俗足彩等角度。
- 预测模型是“内置思考力”，用户不需要看到流程图。
- 复盘昨日预测必须放进今日模型看板里，并据此修正今日模型。
- 需要尽量推送 GitHub Pages；如果网络失败，要明确说明本地已完成但未推送。

## 最近已完成状态

最新成功推送：

- commit: `e3926bc`
- branch: `main`
- Pages: `https://jwang0127.github.io/worldcupxx/`

最近修复：

- 修复了页面里出现 `&#26368;...` 这类 HTML 实体乱码的问题。
- 修改了 `scripts/generate_daily_board.ps1`，在写入 `index.html` 和 `predict_YYYYMMDD.html` 前执行：
  `[System.Net.WebUtility]::HtmlDecode($html)`
- 修改了 `scripts/auto_update.ps1`，在写入 `review.html` 和根目录 `index.html` 前也执行实体解码。
- 已重新生成并推送：
  - `20260618/index.html`
  - `20260618/predict_20260618.html`
  - `20260618/review.html`
  - `20260619/index.html`
  - `20260619/predict_20260619.html`
  - 根目录 `index.html`

注意：源码中可能仍有 `&#127757;`、`&#128302;` 这类 emoji 实体，这是正常的，浏览器会显示成图标；真正要避免的是中文被显示成 `&#数字;`。

## 当前数据和页面

已有日期目录：

- `20260617/`
- `20260618/`
- `20260619/`

已有数据：

- `data/20260618.json`
- `data/20260619.json`

`20260618` 已有赛果复盘：

- 葡萄牙 vs 刚果(金)：1:1
- 英格兰 vs 克罗地亚：4:2
- 加纳 vs 巴拿马：1:0
- 乌兹别克斯坦 vs 哥伦比亚：1:3

`20260619` 今日预测四场：

- 周四025 捷克 vs 南非：总进球 2，稳胆 2:0 / 2:1，冷门 1:1
- 周四026 瑞士 vs 波黑：总进球 3，稳胆 2:1 / 3:0，冷门 1:1
- 周四027 加拿大 vs 卡塔尔：总进球 3，稳胆 3:0 / 3:1，冷门 1:1
- 周四028 墨西哥 vs 韩国：总进球 2，稳胆 1:1 / 2:1，冷门 0:1

## 关键脚本

- `scripts/generate_daily_board.ps1`
  - 从 `data/YYYYMMDD.json` 生成 `YYYYMMDD/index.html` 和 `YYYYMMDD/predict_YYYYMMDD.html`
  - 当前主要看板内容在这里生成，包括复盘、今日预测汇总、每场五项分析、玄学分析、组合推荐。

- `scripts/auto_update.ps1`
  - 自动回填赛果、生成看板、生成复盘页、更新模型状态，可选择推送。

- `scripts/backfill_results.ps1`
  - 自动结算赛果的入口。
  - 当前已配置结果源方案：API-Football、football-data.org、SerpApi、TheSportsDB、worldcup26.ir。
  - 多数 API 需要 key，`worldcup26.ir` 作为公开镜像可尝试。

- `scripts/fetch_sporttery.ps1`
  - 抓取竞彩足球数据，尤其总进球数、胜平负、让球胜平负赔率。
  - Sporttery 请求需要浏览器式 headers。

- `push_to_github.ps1`
  - 提交并推送到 GitHub Pages。
  - 如果网络失败，稍后重跑即可。

## 常用命令

重新生成某日看板：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& .\scripts\generate_daily_board.ps1 -Date 20260619
```

自动更新但不推送：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& .\scripts\auto_update.ps1 -Date 20260619 -NoPush
```

推送 GitHub：

```powershell
powershell -ExecutionPolicy Bypass -File .\push_to_github.ps1
```

如果嵌套启动 `powershell.exe` 报“拒绝访问”，改用当前 PowerShell 会话直接执行脚本：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& .\scripts\auto_update.ps1 -Date 20260619 -NoPush
```

检查中文实体乱码：

```powershell
rg -n "&#[0-9]{3,};" 20260618 20260619 index.html
```

如果只剩 `&#127757;`、`&#128302;` 等 emoji 实体通常不用修；如果中文句子中出现大量 `&#26368;`、`&#39044;` 等，需要修复生成器。

## 重要代码注意事项

- `scripts/generate_daily_board.ps1` 里不要使用变量名 `$home`，会和 PowerShell 内置只读变量 `$HOME` 冲突。之前已改为 `$homeTeamName`。
- PowerShell 脚本中中文直接写入容易受编码影响；当前文件以 UTF-8 写入。
- 页面写入前要保留 `HtmlDecode`，避免 HTML 实体在浏览器中原样显示。
- 用户不希望再生成可见的“模型流程图页面”或“玄学单独页面”。如果看见 `model.html`、`mystic.html`、`data-sources.html` 之类需求，除非用户重新明确要求，否则不要恢复。
- 玄学、赔率、基本面都可以是“娱乐分析”，但页面底部必须保留理性提示，不构成购彩建议。

## 下一轮优先事项

如果用户说“继续”或“执行今天”：

1. 先确认今天日期和当天比赛编号，当前系统日期是北京时间 `2026-06-19`。
2. 找到或抓取当天赔率截图/数据，更新 `data/YYYYMMDD.json`。
3. 如果昨天比赛已有赛果，先回填结果并复盘。
4. 根据复盘修正今日预测。
5. 重新生成 `YYYYMMDD/index.html` 和 `predict_YYYYMMDD.html`。
6. 检查中文乱码和五项分析是否都有内容。
7. 推送 GitHub Pages。

如果用户问“赛果自动更新能不能接 API”：

- 可以，但要说明：
  - API-Football、football-data.org 通常更适合正式赛果，但需要 token。
  - SerpApi 可作为 Google 体育卡片兜底，需要 key。
  - TheSportsDB 可作为元数据/比分兜底，覆盖率不一定稳定。
  - `worldcup26.ir/get/games` 可以尝试公开世界杯赛程/赛果镜像，但需要验证字段稳定性。
  - 代码已预留官方结果字段合并和多源回填结构。

## 新对话开场建议

用户开新对话后，可以直接说：

“读取 `NEXT_CHAT_MEMORY.md`，继续世界杯预测看板项目。”

助手应先读取本文件，再从当前任务继续，不要让用户重新解释需求。
