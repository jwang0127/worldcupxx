param(
  [string]$Date = (Get-Date -Format "yyyyMMdd")
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dataFile = Join-Path $root ("data\" + $Date + ".json")
$dayDir = Join-Path $root $Date
$dayIndex = Join-Path $dayDir "index.html"
$predictFile = Join-Path $dayDir ("predict_" + $Date + ".html")

if (-not (Test-Path $dataFile)) {
  throw "Missing data file: $dataFile"
}

if (-not (Test-Path $dayDir)) {
  New-Item -ItemType Directory -Force -Path $dayDir | Out-Null
}

$payload = Get-Content -Raw $dataFile | ConvertFrom-Json

$summaryCards = New-Object System.Collections.Generic.List[string]
$detailCards = New-Object System.Collections.Generic.List[string]
$navLinks = New-Object System.Collections.Generic.List[string]

$i = 0
foreach ($m in $payload.matches) {
  $i += 1
  $sectionId = "m$i"
  $navLinks.Add("<a href=""#$sectionId"">Match $i</a>")

  $hadText = "H $($m.odds.had.home) / D $($m.odds.had.draw) / A $($m.odds.had.away)"
  $ttgText = "0:$($m.odds.ttg.s0) 1:$($m.odds.ttg.s1) 2:$($m.odds.ttg.s2) 3:$($m.odds.ttg.s3) 4:$($m.odds.ttg.s4) 5:$($m.odds.ttg.s5) 6:$($m.odds.ttg.s6) 7+:$($m.odds.ttg.s7)"
  $summaryCards.Add(@"
<div class="mini">
  <span class="tag">$($m.matchNumStr)</span>
  <div class="teams">$($m.home) vs $($m.away)</div>
  <small>Total goals lean: $($m.prediction.totalGoals); scores: $($m.prediction.scores -join ", ")</small>
</div>
"@)

  $detailCards.Add(@"
<section id="$sectionId" class="card">
  <h3>$($m.matchNumStr) $($m.home) vs $($m.away)</h3>
  <div class="meta">$($m.kickoff) | $($m.league) | $($m.venue)</div>
  <div class="panel">
    <div class="pred">
      <div class="box">
        <h4>Total Goals</h4>
        <div class="big">$($m.prediction.totalGoals)</div>
        <small>Confidence: $($m.prediction.confidence)</small>
      </div>
      <div class="box">
        <h4>Main Scores</h4>
        <span class="score">$($m.prediction.scores[0])</span>
        <span class="score">$($m.prediction.scores[1])</span>
      </div>
      <div class="box">
        <h4>Upset Cover</h4>
        <span class="score upset">$($m.prediction.upset)</span>
      </div>
    </div>
    <div class="pred">
      <div class="box">
        <h4>HAD Odds</h4>
        <p>$hadText</p>
      </div>
      <div class="box">
        <h4>TTG Odds</h4>
        <p>$ttgText</p>
      </div>
      <div class="box">
        <h4>Review Note</h4>
        <p>$($m.review)</p>
      </div>
    </div>
  </div>
</section>
"@)
}

$reviewLink = ""
if (Test-Path (Join-Path $dayDir "review.html")) {
  $reviewLink = '<a href="./review.html">Review</a>'
}

$html = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>World Cup Prediction Board $Date</title>
<style>
:root{--bg:#06120f;--panel:#0b1d20;--card:#102528;--line:#1f4a43;--green:#33e28a;--mint:#8fffd0;--red:#ff6b6b;--blue:#7dd3fc;--text:#e9fff8;--muted:#9bb8b0}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;background:radial-gradient(circle at 18% 8%,rgba(51,226,138,.16),transparent 24%),linear-gradient(135deg,#020807,#06120f 42%,#071b2a);color:var(--text)}a{color:inherit;text-decoration:none}
header{position:sticky;top:0;z-index:5;background:rgba(3,12,11,.88);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.hero{max-width:1240px;margin:auto;padding:24px 18px 16px}h1{margin:0 0 14px;font-size:clamp(24px,4vw,42px)}nav{display:flex;gap:10px;flex-wrap:wrap}nav a{padding:9px 13px;border:1px solid var(--line);border-radius:8px;background:#0b201d;color:var(--mint);font-size:14px}
main{max-width:1240px;margin:auto;padding:20px 18px 50px}.section{margin:22px 0 34px}.section h2{font-size:26px;margin:0 0 16px;color:var(--blue)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}@media(max-width:950px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.grid{grid-template-columns:1fr}nav a{flex:1;text-align:center}}
.mini,.card{background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));border:1px solid var(--line);border-radius:8px;box-shadow:0 16px 36px rgba(0,0,0,.28)}.mini{padding:16px;transition:.22s}.mini:hover,.card:hover{transform:translateY(-3px);border-color:#39d98a}
.tag{display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:999px;background:#12362f;color:var(--green);font-size:12px;border:1px solid #246b59}.teams{font-size:21px;font-weight:800;margin:11px 0 6px}
.card{padding:18px;margin-bottom:22px;scroll-margin-top:110px}.card h3{font-size:28px;margin:0 0 6px}.meta{color:var(--muted);margin-bottom:14px}.panel{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:860px){.panel{grid-template-columns:1fr}}
.pred{display:grid;gap:10px}.box{border:1px solid #1c5048;background:#071817;border-radius:8px;padding:13px}.box h4{margin:0 0 8px;color:var(--blue)}.big{font-size:32px;color:var(--green);font-weight:900}.score{display:inline-block;margin:4px 8px 4px 0;padding:8px 12px;border-radius:8px;border:1px solid #2ecf7a;background:#0d3028;color:#a8ffd6;font-weight:800}.upset{border-color:var(--red);background:#331415;color:#ffd2b0}
footer{color:#8ea8a1;text-align:center;border-top:1px solid var(--line);padding:24px 12px;font-size:13px}
</style>
</head>
<body>
<header>
  <div class="hero">
    <h1>World Cup Prediction Board $Date</h1>
    <nav>
      <a href="../index.html">Home</a>
      $reviewLink
      $($navLinks -join "`n")
    </nav>
  </div>
</header>
<main>
<section class="section">
  <h2>Daily Overview</h2>
  <div class="grid">
    $($summaryCards -join "`n")
  </div>
</section>
$($detailCards -join "`n")
</main>
<footer>Auto-generated from Sporttery live data. For entertainment analysis only.</footer>
</body>
</html>
"@

$html | Set-Content -Encoding UTF8 $dayIndex
$html | Set-Content -Encoding UTF8 $predictFile
Write-Host "Generated daily board: $dayIndex"
