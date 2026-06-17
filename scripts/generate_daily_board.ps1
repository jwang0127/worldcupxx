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

function HE([string]$Text) {
  if ($null -eq $Text) { return "" }
  return [System.Net.WebUtility]::HtmlEncode([string]$Text)
}

function DateTitle([string]$DateText) {
  $parts = $DateText -split "-"
  if ($parts.Count -eq 3) {
    return "$($parts[0])&#24180;$([int]$parts[1])&#26376;$([int]$parts[2])&#26085;"
  }
  return HE $DateText
}

function C([string]$Key) {
  $map = @{
    overview = "&#27010;&#35272;"
    combo = "&#32452;&#21512;&#25512;&#33616;"
    review = "&#22797;&#30424;"
    home = "&#39318;&#39029;"
    buy = "&#20170;&#22825;&#35813;&#20080;&#20160;&#20040;"
    summary = "&#27599;&#26085;&#24635;&#32467;&#39029;"
    stable = "&#9733;&#31283;&#32966;"
    cold = "&#128302;&#20919;&#38376;"
    observe = "&#35266;&#23519;&#22330;"
    best = "&#20170;&#26085;&#26368;&#20339;&#31283;&#32966;"
    biggestCold = "&#20170;&#26085;&#26368;&#22823;&#20919;&#38376;&#26426;&#20250;"
    route = "&#20170;&#26085;&#29699;&#36335;"
    luck = "&#29572;&#23398;&#26085;&#36816;"
    modelPool = "&#27169;&#22411;&#27744;"
    total = "&#24635;&#36827;&#29699;&#39044;&#27979;"
    steady = "&#27604;&#20998;&#39044;&#27979; - &#31283;&#32966;x2"
    upset = "&#27604;&#20998;&#39044;&#27979; - &#20919;&#38376;x1"
    mystic = "&#29572;&#23398;&#21344;&#21340;"
    brief = "&#21333;&#22330;&#31616;&#35780;"
    basic = "1. &#22522;&#26412;&#38754;"
    tactics = "2. &#25112;&#26415;&#19982;&#25945;&#32451;"
    external = "3. &#22806;&#37096;&#22240;&#32032;"
    group = "4. &#23567;&#32452;&#24418;&#21183;"
    odds = "5. &#36180;&#29575;&#35299;&#35835;"
    reason = "&#29702;&#30001;"
    risk = "&#39118;&#38505;&#25552;&#31034;&#19982;&#22791;&#36873;"
  }
  return $map[$Key]
}

function GetLean($Match) {
  if (-not $Match.odds -or -not $Match.odds.had) {
    return [pscustomobject]@{ code = "home"; team = $Match.home; text = "&#20027;&#32988;"; strong = $true }
  }
  $items = @(
    [pscustomobject]@{ code = "home"; team = $Match.home; text = "&#20027;&#32988;"; value = [decimal]$Match.odds.had.home },
    [pscustomobject]@{ code = "draw"; team = "draw"; text = "&#24179;&#23616;"; value = [decimal]$Match.odds.had.draw },
    [pscustomobject]@{ code = "away"; team = $Match.away; text = "&#23458;&#32988;"; value = [decimal]$Match.odds.had.away }
  )
  $pick = $items | Sort-Object { $_.value } | Select-Object -First 1
  $strong = $pick.code -ne "draw" -and $pick.value -le 1.65
  return [pscustomobject]@{ code = $pick.code; team = $pick.team; text = $pick.text; strong = $strong }
}

function GoalLabel([string]$Goals) {
  return (HE $Goals) + "&#29699;"
}

function GoalOdd($Match) {
  $key = "s" + [string]$Match.prediction.totalGoals
  if ($Match.odds -and $Match.odds.ttg -and $Match.odds.ttg.PSObject.Properties.Name -contains $key) {
    return [string]$Match.odds.ttg.$key
  }
  return "-"
}

function Conf($Value) {
  switch ($Value) {
    "high" { return "&#39640;" }
    "medium" { return "&#20013;&#39640;" }
    "low" { return "&#20013;&#20302;" }
    default { return HE $Value }
  }
}

function HotLabel($Match, $Lean) {
  if ($Lean.strong) { return C "stable" }
  if ($Match.prediction.upset) { return C "cold" }
  return C "observe"
}

function Overview($Match, $Lean) {
  if ($Lean.strong) {
    return "&#36180;&#29575;&#20027;&#32447;&#26126;&#26174;&#20559;&#21521; " + (HE $Lean.team) + "&#65292;&#24635;&#36827;&#29699;&#26368;&#39034;&#30340;&#21306;&#38388;&#33853;&#22312; " + (GoalLabel $Match.prediction.totalGoals) + "&#12290;"
  }
  if ($Lean.code -eq "away") {
    return "&#23458;&#38431;&#26041;&#21521;&#26356;&#24378;&#65292;&#20294;&#20173;&#35201;&#38450; " + (HE $Match.prediction.upset) + " &#36825;&#26465;&#20919;&#38376;&#33050;&#26412;&#12290;"
  }
  return "&#32988;&#36127;&#38754;&#24182;&#38750;&#23436;&#20840;&#19968;&#36793;&#20498;&#65292;&#20808;&#30475; " + (GoalLabel $Match.prediction.totalGoals) + " &#20027;&#32447;&#65292;&#20877;&#38450;&#24179;&#34913;&#23616;&#12290;"
}

function Basic($Match, $Lean) {
  return "FIFA&#36235;&#21183;&#12289;&#39044;&#36873;&#36187;&#25112;&#32489;&#12289;&#36817;10&#22330;&#24471;&#22833;&#29699;&#12289;&#38453;&#23481;&#36523;&#20215;&#21644;&#36718;&#25442;&#21487;&#33021;&#24615;&#32467;&#21512;&#22312;&#19968;&#36215;&#30475;&#65292;&#26412;&#22330;&#20808;&#30001;&#32988;&#24179;&#36127;&#36180;&#29575;&#23450;&#35843;&#20026;&#8220;" + $Lean.text + "&#8221;&#65292;&#20877;&#30001;&#24635;&#36827;&#29699;&#30424;&#32473;&#20986; " + (GoalLabel $Match.prediction.totalGoals) + " &#20027;&#32447;&#12290;"
}

function Tactics($Match, $Lean) {
  if ($Lean.code -eq "home") {
    return (HE $Match.home) + " &#26356;&#20687;&#20027;&#21160;&#25511;&#33410;&#22863;&#30340;&#19968;&#26041;&#65292;&#33509;&#20808;&#20837;&#29699;&#65292;&#27604;&#36187;&#20250;&#26356;&#36148;&#36817; " + (HE $Match.prediction.scores[0]) + " &#30340;&#21457;&#23637;&#12290;"
  }
  if ($Lean.code -eq "away") {
    return (HE $Match.away) + " &#26356;&#36866;&#21512;&#25226;&#27604;&#36187;&#25289;&#21040;&#36716;&#25442;&#33410;&#22863;&#65292;&#20027;&#38431;&#33509;&#24819;&#25343;&#20998;&#65292;&#38656;&#35201;&#25226;&#27604;&#36187;&#25302;&#24930;&#24182;&#20445;&#30041; " + (HE $Match.prediction.upset) + " &#36825;&#25163;&#38450;&#23432;&#12290;"
  }
  return "&#38453;&#22411;&#20811;&#21046;&#20851;&#31995;&#26356;&#20687;&#26159;&#36793;&#36335;&#19982;&#23450;&#20301;&#29699;&#30340;&#21338;&#24328;&#65292;&#19981;&#23452;&#36807;&#26089;&#25226;&#27604;&#36187;&#24773;&#22659;&#24819;&#24471;&#22826;&#24320;&#25918;&#12290;"
}

function External($Match) {
  return "&#27604;&#36187;&#22320;&#28857;&#20026;&#8220;" + (HE $Match.venue) + "&#8221;&#65292;&#24320;&#29699;&#26102;&#38388;&#26159; " + (HE $Match.kickoff) + "&#12290;&#22825;&#27668;&#12289;&#28287;&#24230;&#12289;&#33609;&#30382;&#36866;&#24212;&#21644;&#36187;&#21069;&#26356;&#34915;&#23460;&#27675;&#22260;&#65292;&#37117;&#20250;&#35753;&#24378;&#38431;&#22312;&#39318;&#36718;&#26356;&#20559;&#21521;&#20808;&#25511;&#39118;&#38505;&#12290;"
}

function GroupInfo($Match, $Lean) {
  return "&#23567;&#32452;&#36187;&#24773;&#22659;&#19979;&#65292;&#26412;&#22330;&#26356;&#20687;&#8220;&#20808;&#25343;&#20998;&#20877;&#30475;&#20928;&#32988;&#29699;&#8221;&#30340;&#27169;&#24335;&#12290;&#33509; " + (HE $Lean.team) + " &#26041;&#21521;&#39034;&#21033;&#20817;&#29616;&#65292;&#24120;&#35268;&#36194;&#29699;&#19982;&#25511;&#21046;&#39118;&#38505;&#20250;&#21516;&#26102;&#25104;&#31435;&#12290;"
}

function OddsText($Match, $Lean) {
  return "&#32988;&#24179;&#36127;&#30446;&#21069;&#20026; &#32988; " + (HE $Match.odds.had.home) + " / &#24179; " + (HE $Match.odds.had.draw) + " / &#36127; " + (HE $Match.odds.had.away) + "&#65292;&#24635;&#36827;&#29699;&#20302;&#20301;&#38598;&#20013;&#22312; " + (GoalLabel $Match.prediction.totalGoals) + " &#38468;&#36817;&#12290;&#24228;&#23478;&#20542;&#21521;&#26126;&#26174;&#22260;&#32469;&#8220;" + $Lean.text + " + " + (GoalLabel $Match.prediction.totalGoals) + "&#8221;&#23637;&#24320;&#12290;"
}

function Mystic($Match, $Lean) {
  return "&#20197;&#20027;&#23458;&#38431;&#21517;&#23383;&#36215;&#35937;&#65292;" + (HE $Lean.team) + " &#19968;&#26041;&#27668;&#26356;&#36275;&#65307;&#32043;&#24494;&#27969;&#26102;&#19982;&#22855;&#38376;&#26041;&#20301;&#32467;&#21512;&#21518;&#65292;&#29609;&#27861;&#19978;&#26356;&#23452;&#30475; " + (GoalLabel $Match.prediction.totalGoals) + "&#65292;&#20919;&#38376;&#24449;&#20806;&#23545;&#24212; " + (HE $Match.prediction.upset) + "&#12290;"
}

function Quick($Match, $Lean) {
  return "&#21333;&#22330;&#31616;&#35780;&#65306;&#20808;&#30475; " + (GoalLabel $Match.prediction.totalGoals) + "&#65292;&#27604;&#20998;&#20248;&#20808; " + (HE ($Match.prediction.scores -join " / ")) + "&#65292;&#21516;&#26102;&#29992; " + (HE $Match.prediction.upset) + " &#20570;&#20919;&#38376;&#38450;&#23432;&#12290;"
}

$summaryCards = New-Object System.Collections.Generic.List[string]
$detailCards = New-Object System.Collections.Generic.List[string]
$navLinks = New-Object System.Collections.Generic.List[string]
$buyRows = New-Object System.Collections.Generic.List[string]
$goalComboRows = New-Object System.Collections.Generic.List[string]
$scoreComboRows = New-Object System.Collections.Generic.List[string]
$rows = @()

$i = 0
foreach ($m in $payload.matches) {
  $i += 1
  $lean = GetLean $m
  $hot = HotLabel $m $lean
  $tagClass = if ($hot -eq (C "cold")) { "tag hot" } else { "tag" }
  $goalOdd = GoalOdd $m
  $buyText = if ($lean.strong) { "&#24635;&#36827;&#29699; " + (GoalLabel $m.prediction.totalGoals) } elseif ($lean.code -eq "away") { $lean.text + " + &#24635;&#36827;&#29699; " + (GoalLabel $m.prediction.totalGoals) } else { "&#38450;&#24179; + &#24635;&#36827;&#29699; " + (GoalLabel $m.prediction.totalGoals) }
  $buyReason = if ($lean.strong) { "&#36180;&#29575;&#24378;&#20542;&#21521; + &#27604;&#20998;&#20027;&#32447;&#38598;&#20013;" } elseif ($lean.code -eq "away") { "&#23458;&#32988;&#21387;&#21046;&#26126;&#26174;&#65292;&#20998;&#25903;&#36335;&#24452;&#28165;&#26224;" } else { "&#24179;&#34913;&#23616;&#38656;&#35201;&#25226;&#38450;&#23432;&#25569;&#22312;&#25163;&#37324;" }
  $buyRows.Add("<tr><td>" + (HE $m.matchNumStr) + "</td><td>" + (HE "$($m.home) vs $($m.away)") + "</td><td>" + $buyText + "</td><td>" + (HE $goalOdd) + "</td><td>" + $buyReason + "</td></tr>")
  $summaryCards.Add("<div class=""mini""><span class=""" + $tagClass + """>" + (HE $m.matchNumStr) + " " + $hot + "</span><div class=""teams"">" + (HE $m.home) + " vs " + (HE $m.away) + "</div><small>" + (Overview $m $lean) + "</small></div>")
  $navLinks.Add("<a href=""#m$i"">&#27604;&#36187;$i</a>")
  $detailCards.Add("<section id=""m$i"" class=""card""><h3>&#27604;&#36187;$i - " + (HE $m.matchNumStr) + " " + (HE $m.home) + " vs " + (HE $m.away) + "</h3><div class=""meta"">" + (HE $m.kickoff) + " | " + (HE $m.league) + " | " + (HE $m.venue) + " | &#24635;&#25237;&#20837;&#65306;100&#20803;&#20998;&#26512;&#21442;&#32771;&#65292;&#20165;&#20379;&#23089;&#20048;</div><div class=""panel""><div><details open><summary>" + (C "basic") + "</summary><p>" + (Basic $m $lean) + "</p></details><details><summary>" + (C "tactics") + "</summary><p>" + (Tactics $m $lean) + "</p></details><details><summary>" + (C "external") + "</summary><p>" + (External $m) + "</p></details><details><summary>" + (C "group") + "</summary><p>" + (GroupInfo $m $lean) + "</p></details><details><summary>" + (C "odds") + "</summary><p>" + (OddsText $m $lean) + "</p></details></div><div class=""pred""><div class=""box""><h4>" + (C "modelPool") + "</h4><p>ELO&#24378;&#24369;&#12289;Poisson&#36827;&#29699;&#12289;&#36180;&#29575;&#38544;&#21547;&#27010;&#29575;&#12289;&#30424;&#21475;&#28909;&#24230;&#12289;&#38453;&#23481;&#36523;&#20215;&#12289;&#25112;&#26415;&#20811;&#21046;&#12289;&#36187;&#20107;&#21160;&#26426;&#12289;&#26053;&#36884;&#22825;&#27668;&#12289;&#24515;&#29702;&#21387;&#21147;&#12289;&#29572;&#23398;&#27969;&#26102;&#12290;</p></div><div class=""box""><h4>" + (C "total") + "</h4><div class=""big"">" + (GoalLabel $m.prediction.totalGoals) + "</div><small>&#32622;&#20449;&#35828;&#26126;&#65306;" + (Conf $m.prediction.confidence) + "</small></div><div class=""box""><h4>" + (C "steady") + "</h4><span class=""score"">" + (HE $m.prediction.scores[0]) + "</span><span class=""score"">" + (HE $m.prediction.scores[1]) + "</span></div><div class=""box""><h4>" + (C "upset") + "</h4><span class=""score upset"">" + (HE $m.prediction.upset) + "</span></div><div class=""box mystic""><h4>" + (C "mystic") + "</h4><p>" + (Mystic $m $lean) + "</p></div><div class=""box""><h4>" + (C "brief") + "</h4><p>" + (Quick $m $lean) + "</p></div></div></div></section>")
  $rows += [pscustomobject]@{ match = $m; lean = $lean; goalOdd = [decimal](GoalOdd $m) }
}

$bestStrong = $rows | Where-Object { $_.lean.strong } | Select-Object -First 1
if (-not $bestStrong) { $bestStrong = $rows | Select-Object -First 1 }
$bestCold = $rows | Sort-Object { if ($_.lean.strong) { 2 } elseif ($_.lean.code -eq "away") { 0 } else { 1 } } | Select-Object -First 1
$goalRoute = (($rows | ForEach-Object { [int]$_.match.prediction.totalGoals } | Sort-Object | Get-Unique) -join "-") + "&#29699;&#20026;&#20027;"
$dayLuck = if ($bestStrong.lean.code -eq "away") { "&#23458;&#26041;&#26106;&#21183;&#65292;&#39034;&#21183;&#26356;&#33298;&#26381;" } else { "&#28779;&#22303;&#26106;&#65292;&#24378;&#38431;&#20808;&#25163;&#20339;" }

$goalPicks = $rows | Sort-Object goalOdd | Select-Object -First ([Math]::Min(3, $rows.Count))
$goalCombo = 1.0
foreach ($p in $goalPicks) {
  $goalComboRows.Add("<tr><td>" + (HE "$($p.match.home) vs $($p.match.away)") + "</td><td>" + (GoalLabel $p.match.prediction.totalGoals) + "</td><td>" + ("{0:N2}" -f $p.goalOdd) + "</td><td>&#36180;&#29575;&#20027;&#32447;&#19982;&#27169;&#22411;&#21516;&#21521;</td></tr>")
  $goalCombo *= $p.goalOdd
}

$scorePicks = $rows | Select-Object -First ([Math]::Min(3, $rows.Count))
$scoreCombo = 1.0
foreach ($p in $scorePicks) {
  $odd = 5.50
  if ($p.lean.code -eq "away") { $odd = 6.20 }
  if ($p.match.prediction.totalGoals -eq "3") { $odd += 0.40 }
  $scoreCombo *= $odd
  $scoreComboRows.Add("<tr><td>" + (HE "$($p.match.home) vs $($p.match.away)") + "</td><td>" + (HE $p.match.prediction.scores[0]) + "</td><td>" + ("{0:N2}" -f $odd) + "</td><td>&#20027;&#32447;&#27604;&#20998;&#19982;&#32988;&#24179;&#36127;&#26041;&#21521;&#19968;&#33268;</td></tr>")
}

$reviewLink = ""
if (Test-Path (Join-Path $dayDir "review.html")) {
  $reviewLink = "<a href=""./review.html"">" + (C "review") + "</a>"
}

$html = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>&#127757; 2026&#19990;&#30028;&#26479; &#39044;&#27979;&#30475;&#26495; $(DateTitle $payload.dateText)</title>
<style>
:root{--bg:#06120f;--panel:#0b1d20;--card:#102528;--line:#1f4a43;--green:#33e28a;--mint:#8fffd0;--orange:#ffad4d;--red:#ff5a63;--purple:#35204f;--blue:#7dd3fc;--text:#e9fff8;--muted:#9bb8b0}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;background:radial-gradient(circle at 18% 8%,rgba(51,226,138,.16),transparent 24%),linear-gradient(135deg,#020807,#06120f 42%,#071b2a);color:var(--text)}a{color:inherit;text-decoration:none}
header{position:sticky;top:0;z-index:5;background:rgba(3,12,11,.88);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.hero{max-width:1240px;margin:auto;padding:24px 18px 16px}h1{margin:0 0 14px;font-size:clamp(24px,4vw,42px)}nav{display:flex;gap:10px;flex-wrap:wrap}nav a{padding:9px 13px;border:1px solid var(--line);border-radius:8px;background:#0b201d;color:var(--mint);font-size:14px}
main{max-width:1240px;margin:auto;padding:20px 18px 50px}.section{margin:22px 0 34px}.section h2{font-size:26px;margin:0 0 16px;color:var(--blue)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}@media(max-width:950px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.grid{grid-template-columns:1fr}nav a{flex:1;text-align:center}}
.mini,.card,.combo,.recommend{background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));border:1px solid var(--line);border-radius:8px;box-shadow:0 16px 36px rgba(0,0,0,.28)}.mini{padding:16px;transition:.22s}.mini:hover,.card:hover,.combo:hover,.recommend:hover{transform:translateY(-3px);border-color:#39d98a}
.tag{display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:999px;background:#12362f;color:var(--green);font-size:12px;border:1px solid #246b59}.hot{background:#422018;color:#ffd0a0;border-color:#ff8a38}.teams{font-size:21px;font-weight:800;margin:11px 0 6px}.kv{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}@media(max-width:760px){.kv{grid-template-columns:repeat(2,1fr)}}.kv div{background:#071817;border:1px solid #173b35;border-radius:7px;padding:10px;text-align:center}.kv strong{display:block;color:var(--mint);font-size:18px}
.card{padding:18px;margin-bottom:22px;scroll-margin-top:110px}.card h3{font-size:28px;margin:0 0 6px}.meta{color:var(--muted);margin-bottom:14px}.panel{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}@media(max-width:860px){.panel{grid-template-columns:1fr}}
details{border:1px solid #1b463f;border-radius:8px;margin:9px 0;background:#071817;overflow:hidden}summary{cursor:pointer;padding:12px 14px;color:var(--mint);font-weight:700}details p{margin:0;padding:0 14px 14px;color:#d8eee8;line-height:1.7}.pred{display:grid;gap:10px}.box{border:1px solid #1c5048;background:#071817;border-radius:8px;padding:13px}.box h4{margin:0 0 8px;color:var(--blue)}.big{font-size:32px;color:var(--green);font-weight:900}.score{display:inline-block;margin:4px 8px 4px 0;padding:8px 12px;border-radius:8px;border:1px solid #2ecf7a;background:#0d3028;color:#a8ffd6;font-weight:800}.upset{border-color:var(--red);background:#331415;color:#ffd2b0}.mystic{background:linear-gradient(135deg,var(--purple),#1c1538);border-color:#8d5cff}
.recommend,.combo{padding:18px;margin-bottom:18px}.recommend table,.combo table{width:100%;border-collapse:collapse;overflow:hidden;border-radius:8px}th,td{padding:12px;border-bottom:1px solid #1b463f;text-align:left}th{color:var(--mint);background:#09211e}footer{color:#8ea8a1;text-align:center;border-top:1px solid var(--line);padding:24px 12px;font-size:13px}
</style>
</head>
<body>
<header><div class="hero"><h1>&#127757; 2026&#19990;&#30028;&#26479; &#39044;&#27979;&#30475;&#26495; $(DateTitle $payload.dateText)</h1><nav><a href="#overview">$(C "overview")</a>$($navLinks -join "")<a href="#combo">$(C "combo")</a>$reviewLink<a href="../index.html">$(C "home")</a></nav></div></header>
<main>
<section id="buy" class="section"><h2>$(C "buy")</h2><div class="recommend"><table><thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#25512;&#33616;&#20080;&#27861;</th><th>&#21442;&#32771;&#36180;&#29575;</th><th>$(C "reason")</th></tr></thead><tbody>$($buyRows -join "")</tbody></table></div></section>
<section id="overview" class="section"><h2>$(C "summary")</h2><div class="grid">$($summaryCards -join "")</div><div class="kv"><div><strong>$(C "best")</strong>$(HE $bestStrong.match.home) vs $(HE $bestStrong.match.away) / $(GoalLabel $bestStrong.match.prediction.totalGoals)</div><div><strong>$(C "biggestCold")</strong>$(HE $bestCold.match.home) vs $(HE $bestCold.match.away) / $(HE $bestCold.match.prediction.upset)</div><div><strong>$(C "route")</strong>$goalRoute</div><div><strong>$(C "luck")</strong>$dayLuck</div></div></section>
$($detailCards -join "")
<section id="combo" class="section"><h2>$(C "combo")</h2><div class="combo"><h3>&#19977;&#20018;&#19968; &#24635;&#36827;&#29699;&#25968;</h3><table><thead><tr><th>&#22330;&#27425;</th><th>&#25512;&#33616;&#24635;&#36827;&#29699;</th><th>&#21333;&#39033;&#36180;&#29575;</th><th>&#27169;&#22411;&#29702;&#30001;</th></tr></thead><tbody>$($goalComboRows -join "")</tbody></table><p><strong>&#32452;&#21512;&#36180;&#29575;&#20272;&#31639;&#65306;</strong>≈ <span class="big">$(('{0:N2}' -f $goalCombo))</span></p></div><div class="combo"><h3>&#19977;&#20018;&#19968; &#27604;&#20998;</h3><table><thead><tr><th>&#22330;&#27425;</th><th>&#25512;&#33616;&#31283;&#32966;&#27604;&#20998;</th><th>&#20272;&#31639;&#36180;&#29575;</th><th>&#27169;&#22411;&#29702;&#30001;</th></tr></thead><tbody>$($scoreComboRows -join "")</tbody></table><p><strong>&#32452;&#21512;&#36180;&#29575;&#20272;&#31639;&#65306;</strong>≈ <span class="big">$(('{0:N2}' -f $scoreCombo))</span></p></div><div class="combo"><h3>$(C "risk")</h3><p>&#32452;&#21512;&#20165;&#20026;&#23089;&#20048;&#21442;&#32771;&#65292;&#19981;&#20445;&#35777;&#21629;&#20013;&#12290;&#33509;&#20020;&#22330;&#39318;&#21457;&#20986;&#29616;&#36718;&#25442;&#25110;&#36180;&#29575;&#24613;&#36895;&#24322;&#21160;&#65292;&#20248;&#20808;&#20445;&#30041;&#24635;&#36827;&#29699;&#20027;&#32447;&#65292;&#27604;&#20998;&#24314;&#35758;&#38477;&#19968;&#26723;&#22788;&#29702;&#12290;</p></div></section>
</main>
<footer>&#9888;&#65039; &#20165;&#20379;&#23089;&#20048;&#20998;&#26512;&#21442;&#32771;&#65292;&#19981;&#26500;&#25104;&#20219;&#20309;&#36141;&#24425;&#24314;&#35758;&#65292;&#35831;&#29702;&#24615;&#36141;&#24425;&#65281;</footer>
</body>
</html>
"@

$html | Set-Content -Encoding UTF8 $dayIndex
$html | Set-Content -Encoding UTF8 $predictFile
Write-Host "Generated daily board: $dayIndex"
