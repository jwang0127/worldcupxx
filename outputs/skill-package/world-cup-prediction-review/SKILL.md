---
name: world-cup-prediction-review
description: Audit and review archived football or World Cup predictions by joining pre-match snapshots with 90-minute results, calculating total-goal, main-score, ranked score-pool, and win-draw-loss accuracy, separating advancement from settlement, identifying model lessons, and generating a transparent final review page. Use for 世界杯复盘、足球预测复盘、正确率汇总、总进球命中率、主比分命中率、比分池覆盖率、胜平负准确率、淘汰赛90分钟结算、赛后方法论沉淀, especially in C:\Users\Administrator\Documents\世界杯预测.
---

# World Cup Prediction Review

## Operating principle

Treat the review as an audit of frozen pre-match records. Never reconstruct a prediction from post-match prose. Keep the public disclaimer: `以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。`

## Required order

1. Locate authoritative 90-minute results and all pre-match prediction archives.
2. Read `references/settlement-methodology.md` before defining metrics or exclusions.
3. Inventory every tournament match as `settled prediction`, `no pre-match archive`, or `unresolved`.
4. Join daily JSON, knockout prediction JSON, and separate result JSON by stable match identity. Deduplicate repeated snapshots and keep the last clearly pre-kickoff version.
5. Calculate the four primary metrics: total goals, main score, ranked top-three score pool, and single-choice win/draw/loss.
6. Show excluded special samples in the raw table. Apply exclusions to calibration only when the flag and reason existed independently of the final accuracy calculation.
7. Generate both machine-readable JSON and a main-page review with coverage, denominators, stage breakdown, every settled match, methodology, and sources.
8. Run the project builder when present, then run `scripts/audit_review_dataset.py` on its JSON output.

## Project commands

For `C:\Users\Administrator\Documents\世界杯预测`:

```powershell
C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\scripts\build_tournament_review.py --root .
C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe C:\Users\Administrator\.codex\skills\world-cup-prediction-review\scripts\audit_review_dataset.py .\data\tournament_review_20260720.json
```

Inspect `index.html`, `accuracy/index.html`, the output JSON, and the final match row after generation.

## Mandatory reporting

Report:

- tournament match count and archived-prediction coverage;
- raw settled count and calibration count;
- hit count, denominator, and rate for all four primary metrics;
- 90-minute versus extra-time/penalty treatment;
- every exclusion and its reason;
- the largest structural errors and reusable conditional corrections;
- files generated and validation performed.

Never call incomplete archive coverage “all tournament matches.” Say “all archived predictions” and state the missing count.

