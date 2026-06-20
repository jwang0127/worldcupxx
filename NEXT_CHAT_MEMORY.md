# 新对话记忆文档：世界杯预测看板

新开对话后，先读这个文件，再继续执行。

当前项目根目录:

`C:\Users\Administrator\Documents\世界杯预测`

## 项目目标

用户要的是“每日世界杯预测看板”，不是流程图，也不是单独模型页。

每天根据赛程、赔率和昨日赛果，生成:

1. 当日中文预测看板
2. 昨日复盘页
3. 可直接发布到 GitHub Pages 的 HTML 页面

发布仓库:

`https://github.com/jwang0127/worldcupxx.git`

页面地址:

`https://jwang0127.github.io/worldcupxx/`

## 用户明确偏好

1. 页面必须是中文
2. 顶部必须有“今天该买什么”和“今日预测结果”
3. 每场都要有详细分析，不能只给结论
4. 分析维度必须包括:
   - 基本面
   - 战术与教练
   - 外部因素
   - 小组形势
   - 赔率解读
5. 玄学分析必须嵌入单场卡片里，不能单独拆页
6. 页面底部必须保留“仅供娱乐分析参考，不构成购彩建议”

## 现在新增的硬规则

### 1. 赛程表是最高优先级基准

以后所有预测前，先以:

`C:\Users\Administrator\Documents\世界杯预测\2026年世界杯赛程表.xlsx`

为准，确认:

1. 主队
2. 客队
3. 北京时间
4. 当地时间
5. 小组

赔率材料只能补赔率，不能代替赛程核对。

### 2. 玄学统一按当地时间起卦

以后玄学判断不用北京时间直接起卦，统一用比赛当地时间。

页面中允许同时展示北京时间和当地时间，但玄学判断必须以当地时间为准。

### 3. 出稿前必须再检查一遍

每次输出前都要做最终复查，至少检查:

1. JSON 主客队是否与赛程表一致
2. 北京时间是否正确
3. 当地时间是否已写入
4. 页面是否与 JSON 一致
5. 易错场次是否再次核对

## 已定位的一次关键错误

### 错误内容

2026-06-21 预测中，原来把 `035` 写成了:

`厄瓜多尔 vs 克罗地亚`

实际应改为:

`厄瓜多尔 vs 库拉索`

### 错误原因

不是简单手误，而是流程错误:

1. 先看了赔率材料，没有先过赛程表
2. 默认把体彩场次号当成赛程顺序号
3. 人工补写球队时没有做最终校对

### 以后如何避免

1. 先跑赛程校验
2. 再录赔率
3. 再生成页面
4. 出稿前做最终复查

## 关键脚本

### `scripts/sync_schedule_metadata.ps1`

作用:

1. 读取 `2026年世界杯赛程表.xlsx`
2. 用赛程表校验并同步 `data/YYYYMMDD.json`
3. 写入组别、北京时间、当地时间
4. 修正明显的主客队串位问题

### `scripts/auto_update.ps1`

作用:

1. 自动执行赛程校验
2. 回填赛果
3. 生成页面
4. 更新复盘页和首页

### `scripts/generate_daily_board.ps1`

作用:

1. 生成 `YYYYMMDD/index.html`
2. 生成 `YYYYMMDD/predict_YYYYMMDD.html`
3. 页面中显示北京时间和当地时间
4. 玄学部分使用当地时间时辰

### `push_to_github.ps1`

作用:

1. 提交当前修改
2. 推送到 GitHub

## 常用命令

先同步赛程并生成:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& .\scripts\auto_update.ps1 -Date 20260621 -NoPush
```

单独跑赛程同步:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& .\scripts\sync_schedule_metadata.ps1 -DataFile .\data\20260621.json
```

推送 GitHub:

```powershell
powershell -ExecutionPolicy Bypass -File .\push_to_github.ps1
```

## 当前需要牢记的操作顺序

如果用户说“继续今天的预测”或“更新明日预测”，固定顺序是:

1. 先确认日期和要处理的场次
2. 先核对 `2026年世界杯赛程表.xlsx`
3. 再录入或检查赔率
4. 回填昨日赛果
5. 运行生成脚本
6. 复查主客队、时间、当地时间、页面文案
7. 再推送 GitHub

## 一句话提醒

以后任何人工补录的比赛，只要没有先过赛程表，就不能直接出稿。
