# 新对话续接记忆

新开对话后，先读这个文件，再继续执行。

## 当前项目位置

根目录：

`C:\Users\Administrator\Documents\世界杯预测`

分享执行手册：

[`SHAREABLE_PREDICTION_REVIEW_LOGIC.md`](C:/Users/Administrator/Documents/世界杯预测/SHAREABLE_PREDICTION_REVIEW_LOGIC.md)

## 当前模型状态

目前模型已经完成这些升级：

1. 主模型与玄学模型分离
2. 新增半全场预测
3. 新增总进球区间预测
4. 新增比分 EV 明细
5. 新增小组积分榜与出线分析
6. 新增外部实时数据区块

## 当前已接通的数据源

1. `worldcup26.ir/get/games`
   - 当前用于小组积分和赛果结构
2. `football-data.org`
   - 备源
3. `v3.football.api-sports.io`
   - 伤停、H2H、国家队查询
4. `TheSportsDB`
   - 球队资料
5. `SerpApi`
   - FIFA 排名补充

## 当前必须记住的硬规则

1. 所有预测前，必须先以 `2026年世界杯赛程表.xlsx` 为准
2. 玄学起卦必须使用比赛当地时间
3. 输出前必须再检查一次主客队、时间、小组、赔率归属
4. 体彩场次编号不能直接当作赛程顺序编号

## 已确认的重要错误

`035` 曾被错误写成 `厄瓜多尔 vs 克罗地亚`，正确应为 `厄瓜多尔 vs 库拉索`。

根因不是笔误，而是：

1. 没先过赛程表
2. 误把场次号当成赛程序号
3. 输出前没做最终复核

## 当前关键脚本

1. `scripts/auto_update.ps1`
2. `scripts/generate_daily_board.ps1`
3. `scripts/sync_schedule_metadata.ps1`
4. `scripts/enrich_match_data.py`
5. `scripts/backfill_results.ps1`
6. `push_to_github.ps1`

## 常用命令

全流程更新但不推送：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& .\scripts\auto_update.ps1 -Date 20260621 -NoPush
```

单独富化：

```powershell
C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\scripts\enrich_match_data.py --date 20260621 --data-file .\data\20260621.json
```

单独重建页面：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& .\scripts\generate_daily_board.ps1 -Date 20260621
```

推送 GitHub：

```powershell
powershell -ExecutionPolicy Bypass -File .\push_to_github.ps1
```

## 新对话建议的第一句话

如果用户说“继续执行”，先做这三件事：

1. 读取 `SHAREABLE_PREDICTION_REVIEW_LOGIC.md`
2. 确认今天要处理的日期和 4 场编号
3. 先检查赛程表，再动预测数据
