# WorldCup Predict Handoff

Current state:
- GitHub Pages repo: `https://github.com/jwang0127/worldcupxx.git`
- Published site: `https://jwang0127.github.io/worldcupxx/`
- Main workflow is now: Sporttery fetch -> daily board build -> review/index rebuild -> commit/push -> Pages publish.
- Current workspace root: `C:\Users\Administrator\Documents\世界杯预测`

What exists:
- `index.html` at repo root as the site entry page.
- Dated folder structure like `20260617/`.
- `data/YYYYMMDD.json` daily data payloads.
- `model_state.json` simple calibration state.
- `scripts/fetch_sporttery.ps1` fetches live Sporttery `ttg,had` data from `webapi.sporttery.cn` and writes `data/YYYYMMDD.json`.
- `scripts/fetch_sporttery.ps1` now also preserves and backfills richer match structure when refreshing an existing day file, and it is prepared to merge official result fields if Sporttery exposes them in the live payload.
- `scripts/backfill_results.ps1` attempts automatic result settlement for a day file. It currently uses stored official fields first and then tries a structured fallback scoreboard source keyed by team codes.
- `scripts/generate_daily_board.ps1` builds `YYYYMMDD/index.html` and `predict_YYYYMMDD.html` from the data file.
- `scripts/auto_update.ps1` regenerates the board, writes per-match `postReview` text, rebuilds the review page, updates model history, and can push.
- `scripts/daily_pipeline.ps1` is the single entry point for fetch -> generate -> review -> push.
- `push_to_github.ps1` pushes local changes to GitHub Pages.
- Automation `world-cup-daily-pipeline` is scheduled for every day at `13:00` local time.

Important details:
- The Sporttery API requires browser-like headers. Direct bare requests may be blocked by WAF.
- Current review generation is dynamic: if `result.homeGoals` and `result.awayGoals` exist, the page will produce settled post-match analysis and hit-rate stats; otherwise it writes a waiting summary into `postReview`.
- Live result settlement now has a fallback path, but the dedicated Sporttery result/detail endpoint is still not fully verified. The code first accepts official fields already present in stored matches, then tries a structured public scoreboard fallback.
- The full pipeline depends on outbound access to `webapi.sporttery.cn` and valid Git push credentials on the machine.

Suggested commands:
- Refresh data only: `powershell -ExecutionPolicy Bypass -File .\scripts\fetch_sporttery.ps1 -Date 20260618 -Force`
- Rebuild pages without push: `powershell -ExecutionPolicy Bypass -File .\scripts\auto_update.ps1 -Date 20260618 -RefreshData -NoPush`
- Full daily run: `powershell -ExecutionPolicy Bypass -File .\scripts\daily_pipeline.ps1 -Date 20260618`

Recommended next turn:
- If needed, continue tracing a dedicated Sporttery result/detail endpoint so same-day finished matches can be auto-settled without any manual score source.
