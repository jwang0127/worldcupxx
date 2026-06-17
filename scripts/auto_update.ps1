param(
  [string]$Date = (Get-Date -Format "yyyyMMdd"),
  [switch]$NoPush,
  [switch]$RefreshData
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $root "data"
$modelFile = Join-Path $root "model_state.json"
$dataFile = Join-Path $dataDir ($Date + ".json")
$dayDir = Join-Path $root $Date

if (-not (Test-Path $dataDir)) {
  New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
}

if (-not (Test-Path $modelFile)) {
  @'
{
  "version": 1,
  "updatedAt": "",
  "weights": {
    "odds": 0.35,
    "elo": 0.2,
    "form": 0.15,
    "tactics": 0.12,
    "motivation": 0.08,
    "external": 0.05,
    "mystic": 0.05
  },
  "history": []
}
'@ | Set-Content -Encoding UTF8 $modelFile
}

if ($RefreshData -or -not (Test-Path $dataFile)) {
  try {
    & (Join-Path $PSScriptRoot "fetch_sporttery.ps1") -Date $Date -OutFile $dataFile -Force:$RefreshData
  }
  catch {
    Write-Host "Auto fetch unavailable: $($_.Exception.Message)"
  }
}

if (-not (Test-Path $dataFile)) {
  throw "Missing data file: $dataFile"
}

try {
  & (Join-Path $PSScriptRoot "backfill_results.ps1") -Date $Date -DataFile $dataFile
}
catch {
  Write-Host "Result backfill unavailable: $($_.Exception.Message)"
}

$payload = Get-Content -Raw $dataFile | ConvertFrom-Json
$model = Get-Content -Raw $modelFile | ConvertFrom-Json

function Get-ResultLeanFromOdds {
  param($Had)

  if (-not $Had) {
    return "home"
  }

  $items = @(
    @{ code = "home"; value = $Had.home },
    @{ code = "draw"; value = $Had.draw },
    @{ code = "away"; value = $Had.away }
  ) | Where-Object { $_.value }

  if (-not $items) {
    return "home"
  }

  return ($items | Sort-Object { [decimal]$_.value } | Select-Object -First 1).code
}

function Get-ReviewSummary {
  param($Match)

  $lean = Get-ResultLeanFromOdds $Match.odds.had
  if (-not $Match.result -or $null -eq $Match.result.homeGoals -or $null -eq $Match.result.awayGoals) {
    return "Waiting for final score. Pre-match lean was $lean with total-goals call $($Match.prediction.totalGoals)."
  }

  $homeGoals = [int]$Match.result.homeGoals
  $awayGoals = [int]$Match.result.awayGoals
  $actualTotal = $homeGoals + $awayGoals
  $actualLean = "draw"
  if ($homeGoals -gt $awayGoals) {
    $actualLean = "home"
  }
  elseif ($awayGoals -gt $homeGoals) {
    $actualLean = "away"
  }

  $goalVerdict = if ([string]$actualTotal -eq [string]$Match.prediction.totalGoals) { "matched" } else { "missed" }
  $resultVerdict = if ($actualLean -eq $lean) { "aligned with the 1X2 lean" } else { "went against the 1X2 lean" }

  return "Final score $homeGoals`:$awayGoals. Total-goals call $goalVerdict at $actualTotal, and the match $resultVerdict."
}

& (Join-Path $PSScriptRoot "generate_daily_board.ps1") -Date $Date

if (-not (Test-Path $dayDir)) {
  New-Item -ItemType Directory -Force -Path $dayDir | Out-Null
}

$rows = New-Object System.Collections.Generic.List[string]
$hitCount = 0
$settledCount = 0

foreach ($m in @($payload.matches)) {
  $actualTotal = $null
  $hitText = "pending"
  $scoreText = "pending"
  $reviewText = Get-ReviewSummary $m

  if ($m.result -and $null -ne $m.result.homeGoals -and $null -ne $m.result.awayGoals) {
    $actualTotal = [int]$m.result.homeGoals + [int]$m.result.awayGoals
    $scoreText = "$($m.result.homeGoals):$($m.result.awayGoals)"
    $settledCount += 1
    if ([string]$actualTotal -eq [string]$m.prediction.totalGoals) {
      $hitText = "hit"
      $hitCount += 1
    }
    else {
      $hitText = "miss"
    }
  }

  $m | Add-Member -NotePropertyName postReview -NotePropertyValue $reviewText -Force
  $rows.Add("<tr><td>$($m.id)</td><td>$($m.home) vs $($m.away)</td><td>$($m.prediction.totalGoals)</td><td>$scoreText</td><td>$hitText</td><td>$reviewText</td></tr>")
}

$rate = "pending"
if ($settledCount -gt 0) {
  $rate = [math]::Round(($hitCount / $settledCount) * 100, 1).ToString() + "%"
}

$model.updatedAt = (Get-Date).ToString("s")
$historyItem = [pscustomobject]@{
  date = $Date
  settled = $settledCount
  totalGoalHits = $hitCount
  totalGoalHitRate = $rate
}
$existingHistory = @()
if ($model.history) {
  $existingHistory = @($model.history | Where-Object { $_.date -ne $Date })
}
$model.history = @($existingHistory + $historyItem)

$payload | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $dataFile
$model | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $modelFile

$html = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$Date Post Match Review</title>
<style>
body{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;background:#06120f;color:#e9fff8}
main{max-width:1100px;margin:auto;padding:28px 16px}
a{color:#8fffd0}
.card{border:1px solid #1f4a43;border-radius:8px;background:#102528;padding:18px;margin:16px 0}
table{width:100%;border-collapse:collapse;background:#071817}
th,td{padding:10px;border-bottom:1px solid #1f4a43;text-align:left;vertical-align:top}
th{color:#8fffd0}
.ok{color:#33e28a}.warn{color:#ffad4d}
</style>
</head>
<body>
<main>
<p><a href="../index.html">Back to index</a></p>
<h1>$Date Review And Model Update</h1>
<div class="card">
<p>Settled matches: $settledCount | Total-goals hits: $hitCount | Hit rate: $rate</p>
<p>Model note: settled matches update the running history automatically. When result data is still missing, the review stays in pending mode until a score source is available.</p>
</div>
<table>
<thead><tr><th>ID</th><th>Match</th><th>Predicted Total Goals</th><th>Final Score</th><th>Result</th><th>Post-Match Review</th></tr></thead>
<tbody>
$($rows -join "`n")
</tbody>
</table>
</main>
</body>
</html>
"@

$reviewFile = Join-Path $dayDir "review.html"
$html | Set-Content -Encoding UTF8 $reviewFile

$cards = New-Object System.Collections.Generic.List[string]
Get-ChildItem -Path $root -Directory |
  Where-Object { $_.Name -match "^\d{8}$" -and (Test-Path (Join-Path $_.FullName "index.html")) } |
  Sort-Object Name |
  ForEach-Object {
    $d = $_.Name
    $cards.Add("<a class=""card"" href=""./$d/""><div><div class=""date"">$d</div><div class=""meta"">Prediction board and post-match review</div></div><div class=""go"">Open &rarr;</div></a>")
  }

$index = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 World Cup Predictions</title>
<style>
:root{--line:#1f4a43;--text:#e9fff8;--muted:#9bb8b0;--green:#33e28a;--blue:#7dd3fc}
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:"Microsoft YaHei",Arial,sans-serif;background:radial-gradient(circle at 20% 10%,rgba(51,226,138,.18),transparent 26%),linear-gradient(135deg,#020807,#071b2a);color:var(--text)}
main{max-width:980px;margin:0 auto;padding:44px 18px}h1{font-size:clamp(28px,5vw,48px);margin:0 0 10px}p{color:var(--muted);line-height:1.8}.list{display:grid;gap:14px;margin-top:26px}.card{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:18px;border:1px solid var(--line);border-radius:8px;background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));text-decoration:none;color:var(--text);transition:.22s}.card:hover{transform:translateY(-3px);border-color:var(--green)}.date{font-size:24px;font-weight:800;color:var(--blue)}.meta{color:var(--muted);margin-top:6px}.go{color:var(--green);font-weight:800;white-space:nowrap}footer{margin-top:40px;color:#8ea8a1;font-size:13px}@media(max-width:620px){.card{align-items:flex-start;flex-direction:column}.go{white-space:normal}}
</style>
</head>
<body>
<main>
<h1>2026 World Cup Predictions</h1>
<p>Daily prediction boards, result reviews, and model calibration notes. For entertainment analysis only.</p>
<section class="list">
$($cards -join "`n")
</section>
<footer>Please play responsibly. This site is not betting advice.</footer>
</main>
</body>
</html>
"@
$index | Set-Content -Encoding UTF8 (Join-Path $root "index.html")

if (-not $NoPush) {
  & (Join-Path $root "push_to_github.ps1")
}

Write-Host "Auto update finished for $Date"
