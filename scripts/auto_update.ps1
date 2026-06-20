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

& (Join-Path $PSScriptRoot "sync_schedule_metadata.ps1") -DataFile $dataFile -Quiet

try {
  & (Join-Path $PSScriptRoot "backfill_results.ps1") -Date $Date -DataFile $dataFile
}
catch {
  Write-Host "Result backfill unavailable: $($_.Exception.Message)"
}

$payload = Get-Content -Raw -Encoding UTF8 $dataFile | ConvertFrom-Json
$model = Get-Content -Raw -Encoding UTF8 $modelFile | ConvertFrom-Json

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

function Get-LeanText {
  param([string]$Value)

  switch ($Value) {
    "home" { return "&#20027;&#32988;" }
    "draw" { return "&#24179;&#23616;" }
    "away" { return "&#23458;&#32988;" }
    default { return $Value }
  }
}

function Get-ReviewSummary {
  param($Match)

  $lean = Get-ResultLeanFromOdds $Match.odds.had
  if (-not $Match.result -or $null -eq $Match.result.homeGoals -or $null -eq $Match.result.awayGoals) {
    return "&#31561;&#24453;&#36187;&#26524;&#22238;&#22635;&#12290;&#36187;&#21069;&#32988;&#24179;&#36127;&#20542;&#21521;&#20026; $(Get-LeanText $lean)&#65292;&#24635;&#36827;&#29699;&#39044;&#27979;&#20026; $($Match.prediction.totalGoals)&#12290;"
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

  $goalVerdict = if ([string]$actualTotal -eq [string]$Match.prediction.totalGoals) { "&#21629;&#20013;" } else { "&#26410;&#21629;&#20013;" }
  $resultVerdict = if ($actualLean -eq $lean) { "&#19982;&#36187;&#21069;&#32988;&#24179;&#36127;&#20542;&#21521;&#19968;&#33268;" } else { "&#19982;&#36187;&#21069;&#32988;&#24179;&#36127;&#20542;&#21521;&#30456;&#21453;" }

  return "&#26368;&#32456;&#27604;&#20998; $homeGoals`:$awayGoals&#12290;&#23454;&#38469;&#24635;&#36827;&#29699; $actualTotal&#65292;&#39044;&#27979;$goalVerdict&#65307;&#36187;&#26524;$resultVerdict&#12290;"
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
  $hitText = "&#24453;&#23450;"
  $scoreText = "&#24453;&#22238;&#22635;"
  $reviewText = Get-ReviewSummary $m

  if ($m.result -and $null -ne $m.result.homeGoals -and $null -ne $m.result.awayGoals) {
    $actualTotal = [int]$m.result.homeGoals + [int]$m.result.awayGoals
    $scoreText = "$($m.result.homeGoals):$($m.result.awayGoals)"
    $settledCount += 1
    if ([string]$actualTotal -eq [string]$m.prediction.totalGoals) {
      $hitText = "&#21629;&#20013;"
      $hitCount += 1
    }
    else {
      $hitText = "&#26410;&#20013;"
    }
  }

  $m | Add-Member -NotePropertyName postReview -NotePropertyValue $reviewText -Force
  $rows.Add("<tr><td>$($m.id)</td><td>$($m.home) vs $($m.away)</td><td>$($m.prediction.totalGoals)</td><td>$scoreText</td><td>$hitText</td><td>$reviewText</td></tr>")
}

$rate = "&#24453;&#23450;"
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

$payloadJson = $payload | ConvertTo-Json -Depth 10
$modelJson = $model | ConvertTo-Json -Depth 10
$payloadJson | Set-Content -Encoding UTF8 $dataFile
$modelJson | Set-Content -Encoding UTF8 $modelFile

$html = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$Date &#19990;&#30028;&#26479;&#22797;&#30424;</title>
<style>
body{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;background:#06120f;color:#e9fff8}
main{max-width:1100px;margin:auto;padding:28px 16px}
a{color:#8fffd0}
.card{border:1px solid #1f4a43;border-radius:8px;background:#102528;padding:18px;margin:16px 0}
table{width:100%;border-collapse:collapse;background:#071817}
th,td{padding:10px;border-bottom:1px solid #1f4a43;text-align:left;vertical-align:top}
th{color:#8fffd0}
</style>
</head>
<body>
<main>
<p><a href="../index.html">&#36820;&#22238;&#39318;&#39029;</a></p>
<h1>$Date &#19990;&#30028;&#26479;&#22797;&#30424;&#19982;&#27169;&#22411;&#26356;&#26032;</h1>
<div class="card">
<p>&#24050;&#32467;&#31639;&#22330;&#27425;&#65306;$settledCount &#65372; &#24635;&#36827;&#29699;&#21629;&#20013;&#65306;$hitCount &#65372; &#21629;&#20013;&#29575;&#65306;$rate</p>
<p>&#27169;&#22411;&#35828;&#26126;&#65306;&#24050;&#32467;&#31639;&#27604;&#36187;&#20250;&#33258;&#21160;&#20889;&#20837;&#21382;&#21490;&#34920;&#29616;&#65307;&#33509;&#36187;&#26524;&#26242;&#26410;&#22238;&#22635;&#65292;&#22797;&#30424;&#20250;&#20445;&#25345;&#24453;&#23450;&#29366;&#24577;&#65292;&#30452;&#21040;&#34917;&#21040;&#21487;&#38752;&#27604;&#20998;&#28304;&#12290;</p>
</div>
<table>
<thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#39044;&#27979;&#24635;&#36827;&#29699;</th><th>&#26368;&#32456;&#27604;&#20998;</th><th>&#32467;&#26524;</th><th>&#22797;&#30424;&#32467;&#35770;</th></tr></thead>
<tbody>
$($rows -join "`n")
</tbody>
</table>
</main>
</body>
</html>
"@

$reviewFile = Join-Path $dayDir "review.html"
$html = [System.Net.WebUtility]::HtmlDecode($html)
$html | Set-Content -Encoding UTF8 $reviewFile

$cards = New-Object System.Collections.Generic.List[string]
Get-ChildItem -Path $root -Directory |
  Where-Object { $_.Name -match "^\d{8}$" -and (Test-Path (Join-Path $_.FullName "index.html")) } |
  Sort-Object Name |
  ForEach-Object {
    $d = $_.Name
    $cards.Add("<a class=""card"" href=""./$d/""><div><div class=""date"">$d</div><div class=""meta"">&#39044;&#27979;&#30475;&#26495;&#19982;&#36187;&#21518;&#22797;&#30424;</div></div><div class=""go"">&#36827;&#20837; &rarr;</div></a>")
  }

$rootIndexHtml = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 &#19990;&#30028;&#26479;&#39044;&#27979;&#20013;&#24515;</title>
<style>
:root{--line:#1f4a43;--text:#e9fff8;--muted:#9bb8b0;--green:#33e28a;--blue:#7dd3fc}
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:"Microsoft YaHei",Arial,sans-serif;background:radial-gradient(circle at 20% 10%,rgba(51,226,138,.18),transparent 26%),linear-gradient(135deg,#020807,#071b2a);color:var(--text)}
main{max-width:980px;margin:0 auto;padding:44px 18px}h1{font-size:clamp(28px,5vw,48px);margin:0 0 10px}p{color:var(--muted);line-height:1.8}.list{display:grid;gap:14px;margin-top:26px}.card{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:18px;border:1px solid var(--line);border-radius:8px;background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));text-decoration:none;color:var(--text);transition:.22s}.card:hover{transform:translateY(-3px);border-color:var(--green)}.date{font-size:24px;font-weight:800;color:var(--blue)}.meta{color:var(--muted);margin-top:6px}.go{color:var(--green);font-weight:800;white-space:nowrap}footer{margin-top:40px;color:#8ea8a1;font-size:13px}@media(max-width:620px){.card{align-items:flex-start;flex-direction:column}.go{white-space:normal}}
</style>
</head>
<body>
<main>
<h1>2026 &#19990;&#30028;&#26479;&#39044;&#27979;&#20013;&#24515;</h1>
<p>&#36825;&#37324;&#27719;&#24635;&#27599;&#26085;&#39044;&#27979;&#30475;&#26495;&#12289;&#36187;&#26524;&#22797;&#30424;&#21644;&#27169;&#22411;&#26657;&#20934;&#35760;&#24405;&#65292;&#39029;&#38754;&#22522;&#20110;&#20844;&#24320;&#36180;&#29575;&#19982;&#20844;&#24320;&#36187;&#26524;&#25345;&#32493;&#26356;&#26032;&#12290;</p>
<section class="list">
$($cards -join "`n")
</section>
<footer>&#20165;&#20379;&#20844;&#24320;&#20449;&#24687;&#20998;&#26512;&#21442;&#32771;&#65292;&#19981;&#26500;&#25104;&#25237;&#27880;&#24314;&#35758;&#12290;</footer>
</main>
</body>
</html>
"@
$rootIndexHtml = [System.Net.WebUtility]::HtmlDecode($rootIndexHtml)
$rootIndexHtml | Set-Content -Encoding UTF8 (Join-Path $root "index.html")

if (-not $NoPush) {
  & (Join-Path $root "push_to_github.ps1")
}

Write-Host "Auto update finished for $Date"
