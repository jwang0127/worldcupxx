param(
  [string]$Date = (Get-Date -Format "yyyyMMdd")
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dataFile = Join-Path $root ("data\" + $Date + ".json")
$dayDir = Join-Path $root $Date
$dayIndex = Join-Path $dayDir "index.html"
$predictFile = Join-Path $dayDir ("predict_" + $Date + ".html")
$rootIndex = Join-Path $root "index.html"
$rootStandingsPage = Join-Path $root "standings.html"

if (-not (Test-Path $dataFile)) {
  throw "Missing data file: $dataFile"
}

if (-not (Test-Path $dayDir)) {
  New-Item -ItemType Directory -Force -Path $dayDir | Out-Null
}

$payload = Get-Content -Raw -Encoding UTF8 $dataFile | ConvertFrom-Json
$teamAliasFile = Join-Path $root "team_aliases.json"
$script:teamAliasMap = @{}
$script:teamDisplayMap = @{}
if (Test-Path $teamAliasFile) {
  try {
    $aliasEntries = Get-Content -Raw -Encoding UTF8 $teamAliasFile | ConvertFrom-Json
    foreach ($entry in @($aliasEntries)) {
      $code = ([string]$entry.code).Trim().ToUpperInvariant()
      if (-not $code) { continue }
      if ($entry.zh) {
        $script:teamDisplayMap[$code] = [string]$entry.zh
      }
      foreach ($candidate in @([string]$entry.zh, [string]$entry.en, [string]$entry.code) + @($entry.aliases)) {
        if ([string]::IsNullOrWhiteSpace([string]$candidate)) { continue }
        $script:teamAliasMap[([string]$candidate).Trim()] = $code
      }
    }
  }
  catch {
  }
}
$script:teamAliasMap["刚果民主共和国"] = "COD"
$script:teamAliasMap["刚果（金）"] = "COD"
$script:teamAliasMap["刚果(金)"] = "COD"
$script:teamAliasMap["DR Congo"] = "COD"
$script:teamAliasMap["Congo DR"] = "COD"

function HE([string]$Text) {
  if ($null -eq $Text) { return "" }
  return [System.Net.WebUtility]::HtmlEncode([string]$Text)
}

function DisplayTeamName([string]$Team) {
  if ([string]::IsNullOrWhiteSpace($Team)) { return "" }
  $teamKey = TeamKey $Team
  if ($teamKey -and $script:teamDisplayMap.ContainsKey($teamKey)) {
    return [string]$script:teamDisplayMap[$teamKey]
  }
  return [string]$Team
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
    final = "&#20170;&#26085;&#39044;&#27979;&#32467;&#26524;"
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
  if (-not $Match.odds) {
    return [pscustomobject]@{ code = "home"; team = $Match.home; text = "&#20027;&#32988;"; strong = $true }
  }

  $items = @()
  if ($Match.odds.had) {
    if ($Match.odds.had.home) { $items += [pscustomobject]@{ code = "home"; team = $Match.home; text = "&#20027;&#32988;"; value = [decimal]$Match.odds.had.home } }
    if ($Match.odds.had.draw) { $items += [pscustomobject]@{ code = "draw"; team = "draw"; text = "&#24179;&#23616;"; value = [decimal]$Match.odds.had.draw } }
    if ($Match.odds.had.away) { $items += [pscustomobject]@{ code = "away"; team = $Match.away; text = "&#23458;&#32988;"; value = [decimal]$Match.odds.had.away } }
  }
  if (-not $items -and $Match.odds.hhad) {
    if ($Match.odds.hhad.home) { $items += [pscustomobject]@{ code = "home"; team = $Match.home; text = "&#20027;&#32988;"; value = [decimal]$Match.odds.hhad.home } }
    if ($Match.odds.hhad.draw) { $items += [pscustomobject]@{ code = "draw"; team = "draw"; text = "&#24179;&#23616;"; value = [decimal]$Match.odds.hhad.draw } }
    if ($Match.odds.hhad.away) { $items += [pscustomobject]@{ code = "away"; team = $Match.away; text = "&#23458;&#32988;"; value = [decimal]$Match.odds.hhad.away } }
  }
  if (-not $items) {
    return [pscustomobject]@{ code = "home"; team = $Match.home; text = "&#20027;&#32988;"; strong = $false }
  }

  if (-not ($Match.odds.had -and $Match.odds.had.home -and $Match.odds.had.draw -and $Match.odds.had.away) -and $Match.odds.hhad) {
    $hHome = ToDouble $Match.odds.hhad.home 0
    $hAway = ToDouble $Match.odds.hhad.away 0
    $seedGap = [math]::Abs((InferGroupSeed $Match ([string]$Match.home)) - (InferGroupSeed $Match ([string]$Match.away)))
    $goal2 = ToDouble $Match.odds.ttg.s2 0
    $goal3 = ToDouble $Match.odds.ttg.s3 0
    if ($hHome -gt 0 -and $hAway -gt 0 -and [math]::Abs($hHome - $hAway) -le 0.08 -and $seedGap -le 1 -and $goal2 -gt 0 -and $goal3 -gt 0 -and $goal2 -le 4.4 -and $goal3 -le 3.8) {
      return [pscustomobject]@{ code = "draw"; team = "draw"; text = "&#24179;&#23616;"; strong = $false }
    }
  }

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

function MatchKickoffLocal($Match) {
  if ($Match.PSObject.Properties.Name -contains "localKickoff" -and $Match.localKickoff) {
    return [string]$Match.localKickoff
  }
  return [string]$Match.kickoff
}

function MatchKickoffBeijingFull($Match) {
  $raw = if ($Match.PSObject.Properties.Name -contains "kickoff" -and $Match.kickoff) {
    [string]$Match.kickoff
  } else {
    MatchKickoffLocal $Match
  }

  if (-not $raw) { return "" }
  try {
    return ([datetime]$raw).ToString("yyyy-MM-dd HH:mm:ss")
  }
  catch {
    return $raw
  }
}

function MatchKickoffClock($Match) {
  $raw = if ($Match.PSObject.Properties.Name -contains "kickoff" -and $Match.kickoff) {
    [string]$Match.kickoff
  } else {
    MatchKickoffLocal $Match
  }
  if (-not $raw) {
    return ""
  }
  try {
    return ([datetime]$raw).ToString("HH:mm")
  }
  catch {
    if ($raw.Length -ge 16) {
      return $raw.Substring(11, 5)
    }
    return $raw
  }
}

function MatchKickoffBeijing($Match) {
  $raw = if ($Match.PSObject.Properties.Name -contains "kickoff" -and $Match.kickoff) {
    [string]$Match.kickoff
  } else {
    MatchKickoffLocal $Match
  }

  if (-not $raw) {
    return ""
  }

  try {
    return ([datetime]$raw).ToString("MM-dd HH:mm")
  }
  catch {
    if ($raw.Length -ge 16) {
      return $raw.Substring(5, 11)
    }
    return $raw
  }
}

function WinDrawLossSummary($Match) {
  if ($Match.odds -and $Match.odds.had) {
    return "胜 " + (HE ([string]$Match.odds.had.home)) + " / 平 " + (HE ([string]$Match.odds.had.draw)) + " / 负 " + (HE ([string]$Match.odds.had.away))
  }
  if ($Match.odds -and $Match.odds.hhad) {
    return "胜平负主盘暂缺，参考让球(" + (HE ([string]$Match.odds.hhad.handicap)) + ")为 胜 " + (HE ([string]$Match.odds.hhad.home)) + " / 平 " + (HE ([string]$Match.odds.hhad.draw)) + " / 负 " + (HE ([string]$Match.odds.hhad.away))
  }
  return "胜平负主盘待补"
}

function MatchWindowSummary($Match) {
  $raw = if ($Match.PSObject.Properties.Name -contains "kickoff" -and $Match.kickoff) {
    [string]$Match.kickoff
  } else {
    MatchKickoffLocal $Match
  }

  if (-not $raw) {
    return "北京时间窗口待补"
  }

  try {
    $hour = ([datetime]$raw).Hour
  }
  catch {
    return "北京时间窗口待补"
  }

  if ($hour -lt 3) { return "北京时间深夜场，节奏通常先稳后开，强队更容易在后程提速。" }
  if ($hour -lt 6) { return "北京时间凌晨场，前段偏试探，后程体能与换人质量会放大差距。" }
  if ($hour -lt 9) { return "北京时间早场，对抗和执行力更关键，比赛更容易收在一球到两球区间。" }
  if ($hour -lt 12) { return "北京时间上午场，节奏更看重阵型完整与情绪管理，平局保护不能丢。" }
  return "北京时间日场，体能分配与比赛管理更重要，低比分与后程决胜更常见。" }

function Conf($Value) {
  switch ($Value) {
    "high" { return "&#39640;" }
    "medium" { return "&#20013;&#39640;" }
    "low" { return "&#20013;&#20302;" }
    default { return HE $Value }
  }
}

function MatchGroupStandingBrief($Match, $StandingsBundle) {
  $group = InferGroupName $Match
  $homeRow = $StandingsBundle.teamLookup[(TeamKey ([string]$Match.home))]
  $awayRow = $StandingsBundle.teamLookup[(TeamKey ([string]$Match.away))]
  if (-not $homeRow -or -not $awayRow) {
    return ""
  }
  $homePlayed = [int](ToDouble $homeRow.played 0)
  $awayPlayed = [int](ToDouble $awayRow.played 0)
  if ($homePlayed -eq 0 -and $awayPlayed -eq 0) {
    return "$group&#65306;&#39318;&#36718;&#26410;&#24320;&#36187;&#65292;" + (HE $Match.home) + "&#21021;&#22987;&#39034;&#20301;&#31532;$($homeRow.rank)&#65292;" + (HE $Match.away) + "&#21021;&#22987;&#39034;&#20301;&#31532;$($awayRow.rank)"
  }
  return "$group&#65306;" + (HE $Match.home) + "&#31532;$($homeRow.rank)&#65288;$($homeRow.points)&#20998;/&#36827;$($homeRow.gf)&#29699;&#65289;&#65292;" + (HE $Match.away) + "&#31532;$($awayRow.rank)&#65288;$($awayRow.points)&#20998;/&#36827;$($awayRow.gf)&#29699;&#65289;"
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
  $homeTeamName = HE $Match.home
  $away = HE $Match.away
  $goal = GoalLabel $Match.prediction.totalGoals
  $scores = HE ($Match.prediction.scores -join " / ")
  $risk = HE $Match.prediction.upset
  $had = WinDrawLossSummary $Match

  switch ([string]$Match.id) {
    "025" {
      return "$homeTeamName 的胜赔 1.69 给出优势，但没有到绝对碾压区间；让一球玩法里客向 1.92 更低，说明市场并不相信 $homeTeamName 必然大胜。基本面按强弱排序仍看 $homeTeamName 控球和机会更多，但复盘 6/18 后要扣掉&#8220;热门必穿&#8221;的机械分，防止把主胜直接推成 3 球以上大胜。$away 的反击和定位球价值要纳入冷门层，所以本场主结论是 $homeTeamName 不败偏胜，$goal 主线，稳胆比分 $scores，冷门防 $risk。"
    }
    "026" {
      return "$homeTeamName 胜赔 1.35 是今日最强基本面信号之一，阵容完整度、比赛经验、攻防稳定性都应高于 $away。原始总进球最低点在 2 球附近，但昨天强队场出现 4:2、1:3 这种尾部放大，说明首轮强队领先后未必收死，反而可能因弱队压出而制造第三球。本场基本面不只看主胜，还要看 $homeTeamName 是否能在领先后继续制造 xG，因此模型从 2 球上调到 $goal，比分主线 $scores，冷门只保留 $risk。"
    }
    "027" {
      return "$homeTeamName 胜赔 1.24 是强压制盘，基本面差距最明显；2 球 3.40 与 3 球 3.45 极近，盘口没有排斥 3 球路径。昨天复盘显示弱队并非完全无进球能力，强队压制盘里更容易出现 3:0 或 3:1，而不是保守 2:0。$away 若早早丢球，比赛会转入被迫压出来的结构，反而提高总进球尾部。本场基本面给 $homeTeamName 明显优势，$goal 主线，稳胆 $scores，冷门极端脚本 $risk。"
    }
    "028" {
      return "$homeTeamName 胜赔 1.86 只是轻优势，平赔 3.00 明显被压低，说明基本面并非单边。$away 的速度、纪律性和反击效率足以让比赛进入低比分缠斗；这场不能按&#8220;主胜最低赔&#8221;简单处理。模型复盘后降低本场置信度，把平局权重和客队偷袭权重同时抬高。基本面结论是 $homeTeamName 稍占主动但容错低，$goal 主线，稳胆 $scores，冷门防 $risk。"
    }
    "029" {
      return "$homeTeamName 胜赔 1.45 明显占优，但让一球三项里主胜 2.51、客胜 2.36 接近，说明市场更认同 $homeTeamName 赢球而非轻松穿盘。比分盘里 1:0、2:0、2:1 都压在低位，结构很像强队控局但对手具备回敬一球能力的中强热盘。结合昨日复盘，不能把强队热度直接外推到 3 球以上大胜，因此本场基本面定为 $homeTeamName 主胜优先，$goal 主线，稳胆比分 $scores，冷门先防 $risk。"
    }
    "030" {
      return "$away 胜赔 1.59 是本组最清晰的客强主弱信号之一，说明市场对 $away 的整体实力、推进效率和比赛成熟度给出了足够尊重。让球玩法是主队受让一球后主胜 2.07、客胜 3.00，意味着 $away 更像小胜打穿难、直接赢球稳的结构。基本面上 $homeTeamName 若无法先稳住低位防守，很容易被 $away 的中前场连续推进压制，所以本场主结论是 $away 方向占优，$goal 主线，稳胆比分 $scores，冷门只保留 $risk。"
    }
    "031" {
      return "胜平负暂未开售，但让两球主胜 1.73 已经足够说明 $homeTeamName 属于重压级强势方。比分盘 2:0、3:0、4:0 全在可打区间，总进球低位从 3 球一路延伸到 4 球和 5 球，说明市场预期并不是简单的小胜，而是看 $homeTeamName 持续施压。结合昨日强队后段持续进球的反馈，本场基本面不压回 3 球以下，而是把 $goal 作为主线，稳胆比分 $scores，冷门只防 $risk 这种弱队偷一球脚本。"
    }
    "032" {
      return "$homeTeamName 胜赔 1.92 只是轻微占优，平赔 3.10 压得偏低，让一球客胜 1.69 更进一步说明这场最像一球胜负或平局缠斗。比分盘 1:1 是最低点，1:0 和 2:1 紧随其后，结构上明显不是开放式对攻，而是节奏容易被拉慢的均衡盘。基本面判断是 $homeTeamName 纸面稍优，但容错很低，模型不宜给高置信，因此本场以 $goal 为主线，稳胆比分 $scores，冷门继续保留 $risk。"
    }
    "033" {
      return "$homeTeamName 胜赔 1.59 已经给出明确优势，但让一球客向 2.04 更低，说明市场对 $homeTeamName 的赢球认可强于大胜认可。总进球 2 球与 3 球几乎贴在一起，结合昨日复盘对强队尾部上修，本场不能只守 2 球。基本面更像 $homeTeamName 控局、小心瑞典反击偷一球的结构，因此主线落在 $goal，稳胆比分 $scores，冷门保留 $risk。"
    }
    "034" {
      return "$homeTeamName 胜赔 1.40 是较为清晰的强势盘，整体实力、阵地战组织和比赛经验都应高于 $away。让一球后三项没有极端失衡，说明市场更认可稳定赢球，而不是无脑打穿。总进球 3 球低位最低，说明德国这场更像 2:0 / 3:1 这类中高效赢球脚本。基本面结论是 $homeTeamName 主胜为先，$goal 主线，冷门只保留 $risk。"
    }
    "035" {
      return "胜平负暂未开售，但让两球主胜 1.90 已足以给出强弱排序，说明 $homeTeamName 至少被市场当作一档明显优势方。比分盘 2:0 与 3:0 都在低位，总进球最低点落在 3 球，结构上更像压制型强主盘。结合复盘后对强队尾部的上修，本场不保守压到 2 球，而是先走 $goal 主线，稳胆比分 $scores，防守端只留 $risk 这一条弱队偷球路径。"
    }
    "036" {
      return "$away 胜赔 1.38 是明天最强的单边赔率之一，说明市场对日本的整体执行力和比赛控制能力相当认可。受让一球后三项依然拉扯，意味着日本更像稳稳拿三分，而不是轻松横扫。比分盘 0:1、0:2、1:2 都在可打区，叠加总进球 2 球低位，基本面最合理的主脚本仍是客胜+小比分，稳胆 $scores，冷门保留 $risk。"
    }
    "037" {
      return "$homeTeamName 胜赔没有开出，但让两球主胜 1.66 已经直接把强弱差写在台面上，说明市场预期是西班牙掌控球权、持续压制、并且至少具备两球赢面的比赛。总进球最低点压在 3 球，3:0、2:0 与 3:1 这类比分都处在可兑现区间。基本面上 $homeTeamName 的传控、阵地渗透和边中轮转明显高于 $away，本场不是要不要赢的问题，而是能否把优势兑现成净胜球，因此主线给到 $goal，稳胆比分 $scores，冷门只留 $risk。"
    }
    "038" {
      return "$homeTeamName 胜赔 1.28 是当天最清晰的强势信号之一，但让一球后主胜只有 1.92，并没有把深穿完全写死。这说明市场更认同比利时赢球本身，而不是无条件暴打。总进球 2 球与 3 球都压在低位，结构很像强队压住比赛、但客队仍有一次反击或定位球回敬空间的盘。基本面结论仍然是 $homeTeamName 优势明确，主线 $goal，稳胆比分 $scores，冷门保留 $risk。"
    }
    "039" {
      return "$homeTeamName 胜赔 1.30 足够说明乌拉圭是盘面主导方，但让一球后三项没有失真，意味着市场承认乌拉圭赢面很大，却不愿直接把净胜两球以上送出来。总进球最低点落在 2 球，1:0、2:0、2:1 都是典型对应脚本。基本面上 $homeTeamName 的对抗、控场和老练程度仍高于 $away，但更像稳控型主胜而非极端开放局，因此主线先看 $goal，稳胆比分 $scores，冷门用 $risk 兜底。"
    }
    "040" {
      return "$away 胜赔 1.44 已经把埃及放在了更稳的一侧，但受让一球后主胜与客胜接近，说明盘口表达的是埃及赢球更顺、穿盘未必轻松。总进球 2 球最低，比分盘集中在 0:1、0:2、1:1 附近，结构上就是典型的客强窄胜盘。基本面上 $away 的成熟度、比赛节奏控制和锋线效率都优于 $homeTeamName，本场不宜追大开大合，主线落在 $goal，稳胆比分 $scores，冷门只保留 $risk。"
    }
  }

  return "$homeTeamName vs $away 基本面先按胜平负赔率 $had 定方向，再结合昨日复盘修正总进球尾部。当前方向为 " + $Lean.text + "，总进球主线 $goal，稳胆比分 $scores，冷门防 $risk。"
}

function Tactics($Match, $Lean) {
  $homeTeamName = HE $Match.home
  $away = HE $Match.away
  $scores = HE ($Match.prediction.scores -join " / ")
  $risk = HE $Match.prediction.upset

  switch ([string]$Match.id) {
    "025" {
      return "$homeTeamName 更可能采取稳控推进，先用中场压迫和边路传中建立优势；$away 若退得太深，会把禁区前沿让给 $homeTeamName 的二点球。关键变量是 $homeTeamName 领先后是否继续压上：如果继续压，比分会靠近 2:1；如果控风险，2:0 或 1:1 都更合理。战术上不支持盲目大球，因为让一球盘已经提示 $homeTeamName 的净胜球空间有限。"
    }
    "026" {
      return "$homeTeamName 的战术优势在于攻守切换更整齐，能通过高位逼抢压缩 $away 的出球路线；$away 若选择五后卫或低位密集，前 30 分钟可能拖住节奏，但体能下滑后容易丢第二、第三球。昨天强队场暴露出领先后空间变大这一点，因此本场把 2:1 / 3:0 作为更合理的战术落点。若 $away 先偷到定位球，冷门防线才转向 $risk。"
    }
    "027" {
      return "$homeTeamName 的优势不是单纯控球，而是能把比赛压到 $away 半场后持续制造二次进攻。$away 如果坚持低位，容易被 $homeTeamName 边路反复冲击；如果提前压出来，又会暴露身后空间。战术路径上 3:0 是强压制成功，3:1 是 $away 在被动局面里抓到一次转换或定位球。这里总进球 3 比 2 更符合复盘后的模型修正。"
    }
    "028" {
      return "$homeTeamName 会更像主动推进的一方，但 $away 的防线纪律和反击速度决定了这场不适合高估主队穿盘。若 $homeTeamName 中路推进受阻，比赛会变成边路传中和远射堆量，效率不一定高；$away 则会等待 $homeTeamName 边后卫身后的反击空间。战术上最像 1:1 / 2:1 的窄比分，若 $homeTeamName 久攻不下，0:1 冷门路径真实存在。"
    }
    "029" {
      return "$homeTeamName 更可能掌握控球和边路压迫，先用持续传导把 $away 压回半场；但让一球盘没有完全站向主队，说明 $away 的退防密度和转换速度值得尊重。若 $homeTeamName 早早领先，比赛会向 2:0 靠近；若迟迟打不开，$away 的反击就会把脚本推向 2:1 或 $risk。战术上支持主队小胜，不支持盲追大开大合。"
    }
    "030" {
      return "$away 的战术优势更像中前场推进质量和反抢速度高一档，能够把 $homeTeamName 压到守转攻的低位脚本里。$homeTeamName 若只靠长传和二点拼抢，容易让比赛节奏完全落入 $away 的控制；但受让一球盘并未完全看空主队，说明 $away 领先后未必继续重压。战术落点因此更像 0:1 / 0:2，若主队守住半场节奏，则平局冷门才会升温到 $risk。"
    }
    "031" {
      return "$homeTeamName 的战术面不是单纯控球，而是可以持续把比赛压成高位围攻和二次进攻回收。$away 一旦退到禁区前沿，面对的将是不断重来的边中结合；如果冒险前提压迫，又会给 $homeTeamName 留出更大的肋部和身后空间。战术路径最像 3:0 或 4:0，一旦 $away 体能掉线，第四球并不夸张；冷门只有在强队轮换、效率下降时才可能滑向 $risk。"
    }
    "032" {
      return "$homeTeamName 会是更主动的一方，但 $away 的身体对抗和中后场保护足以把比赛拖进低比分绞杀。若 $homeTeamName 边路推进被限制，中路组织就很容易断成碎片，比赛会反复落在定位球和二点球争抢上；$away 则会等待主队压上后的纵深空间。战术上这场更像 1:1 / 2:1 这种窄口分胜负，若主队情绪先急，$risk 的反击冷门会迅速变真。"
    }
    "033" {
      return "$homeTeamName 会更主动掌控节奏，但 $away 的防线韧性和转换冲击力决定了这不是适合盲追穿盘的比赛。若荷兰上半场先破门，比分会向 2:1 或 3:0 分叉；若长时间僵住，瑞典的定位球和反击会把平局风险推高。战术层面因此支持主队赢球，同时保留瑞典偷一球的通道。"
    }
    "034" {
      return "$homeTeamName 的优势会体现在阵地推进、边中转换和压迫回收效率上，$away 若退得过深，后程体能下滑后容易连续丢机会。德国一旦早早领先，比赛会更像控节奏下的第二球、第三球推进，而不是无序对攻。战术落点更贴近 2:0 / 3:1，若科特迪瓦先顶住前 30 分钟，$risk 才会升温。"
    }
    "035" {
      return "$homeTeamName 这场更像持续高压和二次进攻回收的压制局，$away 若始终低位死守，最怕的就是边路传中加禁区二点球循环。让两球盘没有直接倾向极端大胜，说明比赛主结构仍是强队压制但节奏可控。战术上 2:0 是保守兑现，3:0 是压制扩张，$risk 则代表弱队趁强队收力偷一球。"
    }
    "036" {
      return "$away 的优势在于攻守转换整齐和前场效率更高，能把 $homeTeamName 压到被动防守脚本。$homeTeamName 若只能靠长传和定位球抢点，比赛更容易被 $away 拖成窄比分客胜。战术落点上 0:1 / 0:2 最符合盘口语言，只有当日本浪费机会过多时，平局冷门 $risk 才会真正变重。"
    }
    "037" {
      return "$homeTeamName 的战术主线会是长时间控球、边锋内收和禁区前沿连续渗透，目标不是一脚解决，而是把 $away 压到退无可退。$away 若全线回收，前 30 分钟可能还能靠密集站位拖住，但一旦先失球，比赛会迅速切换成西班牙继续围攻的剧本。战术层面最像上半场先平后胜、下半场再拉开差距，所以半全场更适合看平/胜或胜/胜，比分落点以 2:0、3:0 为主，只有强队效率偏低时才会滑向 $risk。"
    }
    "038" {
      return "$homeTeamName 更可能通过中前场逼抢和边中结合先把比赛压在伊朗半场，但 $away 的防守韧性与回收速度不会让这场轻松变成对攻。若比利时早早进球，比赛会向 2:0 或 2:1 分叉；若上半场迟迟不破，伊朗的定位球和反击会把平局保护抬高。战术路径支持主队赢球，但不支持无脑追穿盘，半全场以平/胜、胜/胜更顺，冷门则是 $risk。"
    }
    "039" {
      return "$homeTeamName 更像先稳住中后场对抗、再靠前场强点与二点球压出差距的一方。$away 如果前段能把比赛拖成碎片化肉搏，乌拉圭的节奏会被拉慢，比赛就更贴近 1:0 或 1:1；但若乌拉圭率先进球，后续控节奏能力足以把比赛收在 2:0。战术上支持主队小胜，半全场更像平/胜或胜/胜，不适合把脚本直接放大成高比分碾压。"
    }
    "040" {
      return "$away 的战术优势在于阵型更整齐、攻守转换更快，能够把 $homeTeamName 压成守转攻和长传找点的被动结构。新西兰若想拿分，首先要把前 45 分钟守住，把比赛拖成低速绞杀；一旦埃及先破门，后续就更容易走成 0:1 / 0:2 的客队控局模式。战术路径最支持平/负或负/负，若埃及边路推进效率一般，平局冷门 $risk 才会放大。"
    }
  }

  if ($Lean.code -eq "home") { return "$homeTeamName 更像主动控节奏的一方，战术主线靠近 $scores；但仍要用 $risk 防守反击或定位球冷门。" }
  if ($Lean.code -eq "away") { return "$away 更适合把比赛拉到转换节奏，主队若想拿分，需要压低节奏并保留 $risk 这条防守路径。" }
  return "阵型克制关系更像边路与定位球博弈，主线比分 $scores，冷门脚本 $risk。"
}

function External($Match) {
  $homeTeamName = HE $Match.home
  $away = HE $Match.away
  $venue = HE $Match.venue
  $beijingKickoff = HE (MatchKickoffBeijingFull $Match)
  $window = HE (MatchWindowSummary $Match)

  switch ([string]$Match.id) {
    "025" { return "比赛时间（北京时间）$beijingKickoff，属于偏晚场窗口，节奏通常比清晨场更容易先谨慎后提速。赛地信息为&#8220;$venue&#8221;，目前按中立场处理，不给主队额外主场加成。外部变量里最重要的是强队心态：$homeTeamName 若把比赛当成必须稳拿三分，会先控风险；$away 只要前 20 分钟不丢球，心理优势会上升。因此外部因素支持小胜或平局防线，不支持极端大胜。" }
    "026" { return "比赛时间（北京时间）$beijingKickoff，属于夜场对抗，进入下半场后体能和专注度会成为分水岭。$homeTeamName 的比赛经验更适合处理这种时段，$away 如果前段消耗过大，后段防守质量会下降。赛地仍按中立场处理，因此不额外加入主场噪音，只看旅途适应、湿度、草皮和临场轮换。外部因素与复盘修正同向：强队后段继续进球概率上升。" }
    "027" { return "比赛时间（北京时间）$beijingKickoff，对美洲球队节奏适应更友好，$homeTeamName 在身体对抗和推进速度上更容易进入状态。$away 若需要长距离适应气候和时差，开局抗压能力会是风险点。中立场条件下，外部因素不削弱 $homeTeamName 的强势，反而加强其前压倾向；但如果天气湿热，强队领先后的防线专注度也会下降，所以 3:1 比单纯 3:0 更有复盘价值。" }
    "028" { return "比赛时间（北京时间）$beijingKickoff，节奏更可能接近日间高强度对抗。$homeTeamName 与 $away 都具备较强球迷属性和情绪波动，舆论压力会放大先丢球后的战术选择。中立场下 $homeTeamName 的名义优势有限，$away 的跑动和反击不应被低估。外部因素综合后更像谨慎开局、后段拉扯，支持 2 球附近和冷门防线。" }
    "029" { return "比赛时间（北京时间）$beijingKickoff，仍在主流强队的身体节奏适应区间内。$homeTeamName 的阵容深度和比赛强度更适合这种时段，而 $away 若开局顶不住压迫，很容易被迫长期回收。中立场条件下不额外给主场红利，因此外部因素更偏向强队赢球、弱队守住净负的结构，支持小胜和 2 球附近。" }
    "030" { return "比赛时间（北京时间）$beijingKickoff，已经接近清晨场，体能和专注度波动会比午夜场更明显。$away 若能在上半场先取得领先，后续就有机会把比赛拖入自己更熟悉的控节奏模式；$homeTeamName 则更需要靠开局阶段的执行力抢情绪。赛地仍按中立场处理，所以外部因素不改写客强逻辑，但会抑制大比分打穿。" }
    "031" { return "比赛时间（北京时间）$beijingKickoff，对强队而言更像可以完整发力的比赛窗口。$homeTeamName 的板凳深度和轮换空间会在这个时段显得更有价值，$away 若前 30 分钟连续失位，体能和心理都可能提前崩盘。中立场与天气因素不会削弱强弱差，只会决定是 3 球还是 4 球以上的尾部展开，因此外部条件与强势大胜脚本同向。" }
    "032" { return "比赛时间（北京时间）$beijingKickoff，进入日场对抗后，比赛更容易被身体碰撞和节奏切碎。$homeTeamName 与 $away 都是情绪驱动明显的球队，谁先失误谁就容易被舆论和场面压力放大。中立场下没有绝对气势加成，外部因素综合后更支持谨慎开局、后段分胜负，所以 2 球主线和冷门防线都要保留。" }
    "033" { return "比赛时间（北京时间）$beijingKickoff，属于偏早场窗口，整体节奏通常更容易先谨慎后拉开。$homeTeamName 的比赛控制力更适合这种时段，但 $away 若能把前 30 分钟拖成僵局，心理层面就会快速升温。中立场不额外给任何一方主场加成，因此外部因素更支持主队赢球、小比分分叉和防平。" }
    "034" { return "比赛时间（北京时间）$beijingKickoff，夜场对强队的连续施压能力更友好，但也更考验后程注意力。$homeTeamName 的板凳与比赛节奏处理更占优，$away 若前段跑动消耗过大，下半场守转攻质量会明显下降。中立场条件下，外部因素与德国主胜脚本同向，但不一定把比赛推成特别夸张的大比分。" }
    "035" { return "比赛时间（北京时间）$beijingKickoff，属于强队可完整发力的窗口。$homeTeamName 若在体能和推进速度上占优，会更容易把比赛压成单边半场攻防；$away 一旦适应慢，前 30 分钟就是最大风险区。中立场下外部条件不削弱强弱差，因此支持压制型主胜和 3 球附近。"}
    "036" { return "比赛时间（北京时间）$beijingKickoff，接近日场高温高对抗时段，比赛很容易被节奏管理和体能分配主导。$away 的整体节奏感更好，适合把比赛拉入自己更舒服的控局模式；$homeTeamName 则更需要等反击或定位球。外部因素综合后更支持客胜小比分，不支持无脑追特别大球。" }
    "037" { return "比赛时间（北京时间）$beijingKickoff，属于晚场但并非深夜，节奏通常会从谨慎试探逐步过渡到强队提速压制。$homeTeamName 对这种窗口的控场适应性更强，$away 则更依赖前 30 分钟防线完整度和门将状态。中立场不额外给任何一方主场红利，因此外部变量主要体现在西班牙能否尽早破局；若迟迟不进，盘面就会从 3:0 压回 2:0 或 1:1 保护。" }
    "038" { return "比赛时间（北京时间）$beijingKickoff，属于球员体能和专注度都较平稳的时段，更适合强队按部就班地把比赛压住。$homeTeamName 的板凳深度和临场换人质量更适合这种窗口，$away 若上半场被长期压制，下半场体能掉速会更明显。中立场条件下，外部因素支持比利时控局取胜，但不额外鼓励大穿。" }
    "039" { return "比赛时间（北京时间）$beijingKickoff，已经进入偏晚场窗口，节奏更容易先硬碰硬再慢慢分层。$homeTeamName 的老练与身体对抗更能适应这种比赛气质，$away 若能把开局拖成胶着，心理面就会迅速站住。中立场下没有额外主场噪音，因此外部因素更支持乌拉圭赢球、小比分收束和防平路径并存。" }
    "040" { return "比赛时间（北京时间）$beijingKickoff，夜场更考验阵型稳定度与专注力延续。$away 的比赛管理能力更好，适合在这种节奏下把比赛做成一球优势后慢慢收口；$homeTeamName 若长时间追不上节奏，只能依赖定位球或二次进攻抢机会。外部因素因此与埃及客胜小比分同向，不支持极端大球。" }
    "041" { return "比赛时间（北京时间）$beijingKickoff，当前属于$window。$homeTeamName 更适合先把控球和前压节奏握在手里，$away 则更依赖前 20 到 30 分钟的防线完整度与门将状态。赛地信息为&#8220;$venue&#8221;，本场继续按中立场处理，不额外引入主场红利。外部变量的核心不是哪一方名气更大，而是谁先把比赛拖进自己熟悉的节奏；若 $homeTeamName 迟迟不破局，平局保护会迅速升温，若早早破门，后续就更容易走向强侧控场收口。" }
    "042" { return "比赛时间（北京时间）$beijingKickoff，当前属于$window。$homeTeamName 的阵地推进、换人深度和后程持续压迫更适合这种节奏，而 $away 若前段长时间回撤，体能与专注力会在下半场同步下滑。中立场处理意味着不加情绪面主场分，因此外部因素更偏向主队控局取胜，但不会自动把比赛推成无脑大穿，仍需保留一球回撤和对手偷一球的分支。" }
    "043" { return "比赛时间（北京时间）$beijingKickoff，当前属于$window。比赛更容易先进入身体对抗和中场绞杀，再由更稳的一方慢慢把优势兑现出来。$homeTeamName 若能把前段节奏控制在自己脚下，赢面会逐步放大；$away 若把比赛拖成碎片化拉扯，低比分和平局保护就会变重。中立场下没有额外主场噪音，因此外部因素更支持小比分分胜负，而不是高比分对攻。" }
    "044" { return "比赛时间（北京时间）$beijingKickoff，当前属于$window。$away 的整体协同性与比赛管理更强，适合把比赛压成低速、高成功率推进；$homeTeamName 若前段守不住二点与边路回防，后面会越来越被动。外部条件因此更偏向客队小比分控局，主线更像 0:1 / 0:2 这种收口盘，而不是节奏失控后的大开大合。" }
  }

  return "比赛地点为&#8220;$venue&#8221;，比赛时间（北京时间）$beijingKickoff。天气、湿度、草皮、旅途和赛前舆论都会影响节奏；本场外部因素按中立场模型处理。"
}

function GroupInfo($Match, $Lean) {
  $homeTeamName = HE $Match.home
  $away = HE $Match.away
  $team = HE $Lean.team

  switch ([string]$Match.id) {
    "025" { return "小组赛语境下，$homeTeamName 的第一目标是拿三分，但盘口没有给出强穿信号，所以&#8220;赢球优先、净胜其次&#8221;更合理。$away 若是小组弱势方，本场拿到 1 分价值很高，会愿意牺牲控球换防守密度。这个形势会压低上半场风险，提升 1:1 冷门价值；若 $homeTeamName 早进球，才会打开 2:1 路径。" }
    "026" { return "$homeTeamName 若想建立小组出线主动权，本场不仅要赢，还要尽量争取净胜球；这就是模型把 2 球上调到 3 球的重要原因。$away 面对强队时未必死守到底，落后后必须争取一个进球，否则后续净胜球压力会很大。小组形势因此支持 $homeTeamName 主胜，同时支持 2:1 / 3:0 的分叉。" }
    "027" { return "$homeTeamName 作为强势方，本场有明显刷净胜球动机：面对 $away 这种盘面弱侧，如果只小胜会给后续小组排名留下压力。$away 的策略大概率是先守平，但一旦丢球，心理上会从保平切到抢分，空间被拉开。小组形势支持 $homeTeamName 主胜并向 3 球靠拢，冷门只在长时间 0:0 时升温。" }
    "028" { return "$homeTeamName 与 $away 的小组形势更接近六分战，输球成本高于其他强弱分明场。双方都不会轻易把阵型完全打开，尤其 $away 拿 1 分可接受时，会更愿意压低节奏。这个形势解释了为什么平赔 3.00 被压低，也解释了为什么本场虽看 $homeTeamName 稍优，但置信度只能给中低。" }
    "029" { return "$homeTeamName 在小组赛阶段的目标不会只是拿分，更要避免在强势定位下丢掉节奏主动权，因此赢球优先、净胜其次更符合形势。$away 若能拖住前 60 分钟，1 分的战略价值会迅速抬高，这也是平局冷门 $($Match.prediction.upset) 不能删掉的原因。小组语境支持 $homeTeamName 主胜，但不支持盲目追净胜两球以上。" }
    "030" { return "$away 若想在小组中建立真正的主动权，这类对中游或弱侧的比赛必须先兑现成三分。$homeTeamName 作为受压一方，最现实的目标是先守住半场甚至 70 分钟，把比赛拖成单球决胜。小组形势因此强化了客队赢球逻辑，但不一定把比分推到过深位置，0:1 / 0:2 是更像形势语言的分叉。" }
    "031" { return "$homeTeamName 这类重压制盘往往伴随净胜球任务，因为同组强队之间最终可能回到净胜球排序。$away 一旦先失球，就很难继续只为守 1 分，会被迫在后程打开一些空间。小组形势与盘口语言一起，支持 $homeTeamName 不只赢球，还要争取把净胜球拉开，所以模型把总进球抬到 " + (GoalLabel $Match.prediction.totalGoals) + "。" }
    "032" { return "$homeTeamName 与 $away 的组内处境更像标准六分战，输球代价高，平局虽然不理想但也未必完全不可接受。这个背景会让双方在前段更谨慎，不愿轻易把比赛踢成开放式互爆。小组形势解释了平赔为何被压低，也决定了本场即使看主队稍热，置信度依旧不能拉高。" }
    "033" { return "$homeTeamName 若想稳住小组主动权，这种主热盘比赛不能只满足于场面优势，必须尽量兑现成三分。$away 对 1 分的接受度显然更高，这也是平局始终不能完全删除的原因。小组形势与盘口一起，支持荷兰赢球，但不支持无脑追净胜两球以上。"}
    "034" { return "$homeTeamName 这场除了要拿分，还带有净胜球争夺意义，因此不会满足于低节奏拖完 90 分钟。$away 若先失球，就很难一直把比赛守在最小差距内。小组形势因此强化了德国主胜与 3 球主线的同向关系，平局冷门只在前程僵持时保留。"}
    "035" { return "$homeTeamName 面对这类让两球盘比赛，最大的任务往往不只是拿三分，而是尽量拉开净胜球。$away 若早丢球，会从保平转为保少输，比赛结构反而更利于强队继续扩张。小组形势与盘口语言一致，支持压制型主胜和 3 球主线。"}
    "036" { return "$away 若想在组内提前建立优势，这类客强盘比赛必须尽快兑现成三分。$homeTeamName 对 1 分的容忍度会更高，所以前段更可能优先守住阵型。小组形势因此进一步支持日本方向，但也解释了为什么盘口更像窄胜，而不是全面碾压。"}
    "037" { return "$homeTeamName 这场带着明显的净胜球任务和出线主动权任务，面对小组弱侧若只拿一球小胜，后续容错并不会太舒服。$away 的战略目标则更现实，首先是把比赛拖慢、争取半场不丢，其次才是偷一个平局。小组形势因此强化了西班牙赢球与 3 球主线，但也解释了为什么 1:1 必须留下作为强队迟迟打不开局面的防线。"}
    "038" { return "$homeTeamName 若想把小组主动权真正握在手里，这类一档强队对中下游的比赛必须先兑现成三分。$away 对 1 分的接受度显然更高，因此前段更可能优先压缩空间、把比赛踢碎。小组语境支持比利时赢球，但不支持盲追净胜两球以上，2:0 / 2:1 才更像形势语言。"}
    "039" { return "$homeTeamName 在这个阶段首先要确保三分，其次才是净胜球，因此比赛策略更可能是先拿下、再看有没有继续扩大比分的空间。$away 若能守住前半段，1 分的战略价值会迅速抬高，所以平局脚本不能删。小组形势因此支持乌拉圭主胜，但更像窄口兑现，不像无脑大开。"}
    "040" { return "$away 若想保住小组竞争力，这类客强盘比赛必须先兑现成三分，否则后续赛程压力会明显变大。$homeTeamName 对 1 分甚至小负的容忍度都高于对攻失控，因此前段更可能把阵型放低。小组形势进一步支持埃及方向，同时解释了为什么盘口主结构是客胜窄比分。"}
  }

  return "小组赛情境下，本场更像&#8220;先拿分再看净胜球&#8221;的模式。若 $team 方向顺利兑现，常规赢球与控制风险会同时成立。"
}

function OddsText($Match, $Lean) {
  $had = "胜 " + (HE $Match.odds.had.home) + " / 平 " + (HE $Match.odds.had.draw) + " / 负 " + (HE $Match.odds.had.away)
  $ttg = "0球 " + (HE $Match.odds.ttg.s0) + "，1球 " + (HE $Match.odds.ttg.s1) + "，2球 " + (HE $Match.odds.ttg.s2) + "，3球 " + (HE $Match.odds.ttg.s3) + "，4球 " + (HE $Match.odds.ttg.s4)
  $hhad = ""
  if ($Match.odds.hhad) {
    $hhad = "让球(" + (HE $Match.odds.hhad.handicap) + ")为 胜 " + (HE $Match.odds.hhad.home) + " / 平 " + (HE $Match.odds.hhad.draw) + " / 负 " + (HE $Match.odds.hhad.away) + "。"
  }
  $goal = GoalLabel $Match.prediction.totalGoals

  switch ([string]$Match.id) {
    "025" { return "胜平负为 $had，主胜低但不是碾压；$hhad 总进球低位：$ttg。赔率核心矛盾是&#8220;主胜方向清楚，但让一球不支持大穿&#8221;，所以 2 球是主线，3 球只能做升温备选。复盘后模型不再只跟最低赔，而是把 1:1 冷门和 2:1 小胜放进同一组风险池。" }
    "026" { return "胜平负为 $had，主胜压得很低，方向最清楚；$hhad 总进球低位：$ttg。2 球 3.35 与 3 球 3.55 差距很小，结合昨日强队盘尾部放大，本场不能机械选择最低的 2 球，而应把 $goal 作为修正后主线。盘口语言是主胜稳、进球数从 2 向 3 倾斜。" }
    "027" { return "胜平负为 $had，是强压制盘；$hhad 总进球低位：$ttg。2 球 3.40 与 3 球 3.45 几乎贴在一起，说明庄家没有强烈排斥 3 球。结合比分盘 3:0、3:1 的可行性，以及昨日复盘对强队后段进球的修正，本场 $goal 是比 2 球更合理的模型输出。" }
    "028" { return "胜平负为 $had，主胜只是轻优势，平赔 3.00 很低；$hhad 总进球低位：$ttg。赔率不是强主胜结构，而是&#8220;主队稍热 + 平局保护 + 小比分&#8221;。因此 2 球仍是主线，但置信度必须下调，1:1 是核心稳胆之一，0:1 是需要防的盘口逆向冷门。" }
    "029" { return "胜平负为 $had，主胜方向明确；$hhad 总进球低位：$ttg。真正的赔率信息不在于主胜低，而在于让一球后主队没有完全压住客队，说明市场对净胜两球以上仍有保留。因此 2 球是最稳妥主线，2:0 / 2:1 比 3 球以上大胜更贴近盘意，" + (HE $Match.prediction.upset) + " 作为平局冷门仍要留住。" }
    "030" { return "胜平负为 $had，客胜 1.59 已经很有力度；$hhad 总进球低位：$ttg。受让一球后三项分布比较均衡，说明庄家更认可 " + (HE $Match.away) + " 赢球，但不急着给深穿剧本。赔率语言因此是&#8220;客胜清楚、比分偏窄、平局保底&#8221;，模型选择 $goal 和 0:1 / 0:2，冷门只保留 " + (HE $Match.prediction.upset) + "。" }
    "031" { return "胜平负暂未开售，但让球(-2)为胜 " + (HE $Match.odds.hhad.home) + " / 平 " + (HE $Match.odds.hhad.draw) + " / 负 " + (HE $Match.odds.hhad.away) + "，已经足够构成强弱判断；总进球低位：$ttg。3 球 3.70、4 球 4.20、5 球 5.80 呈现连续低位，说明盘口并不担心比赛被锁死在小球区。本场赔率语言是强队压制 + 中大球共振，所以 $goal 比保守 3 球更符合结构。" }
    "032" { return "胜平负为 $had，主胜只是轻热；$hhad 总进球低位：$ttg。让一球客胜 1.69 和比分盘 1:1 最低点共同说明这是一场典型的&#8220;主队稍占优，但穿盘困难，平局不低估&#8221;的盘。赔率结构并不支持高置信站边，更适合围绕 2 球、1:1、2:1 和 " + (HE $Match.prediction.upset) + " 这几条主副脚本来布防。" }
    "033" { return "胜平负为 $had，主胜 1.59 已经站稳优势；$hhad 总进球低位：$ttg。真正的关键信息是让一球后客向更低，说明市场对荷兰赢球认可高，但对净胜两球仍保留。2 球与 3 球赔率极近，结合强队盘复盘修正，本场更适合用 3 球主线承接 2:1 / 3:0。"}
    "034" { return "胜平负为 $had，德国方向非常清楚；$hhad 总进球低位：$ttg。3 球赔率最低，而让一球主胜与客胜没有拉开到失真区间，说明这是典型的&#8220;主胜稳、比分中段、深穿待观察&#8221;盘。赔率语言支持 2:0 / 3:1，而不是盲追 4 球以上极端打穿。"}
    "035" { return "胜平负暂未开售，但让球(-2)为胜 " + (HE $Match.odds.hhad.home) + " / 平 " + (HE $Match.odds.hhad.draw) + " / 负 " + (HE $Match.odds.hhad.away) + "，已经足够构成强弱判断；总进球低位：$ttg。3 球最低，4 球与 2 球同价，说明盘口并不排斥更大的尾部，但主结构仍是 3 球压制盘。模型因此先看 3 球和 2:0 / 3:0，而不是一步冲到极端大比分。"}
    "036" { return "胜平负为 $had，客胜 1.38 是最强信号之一；$hhad 总进球低位：$ttg。受让一球后三项依然胶着，说明盘口表达的是日本赢球较稳，但净胜两球以上并不轻松。总进球 2 球最低，比分盘 0:1 / 0:2 / 1:2 集中，这就是标准的客强窄胜盘。"}
    "037" { return "让球(-2)为胜 " + (HE $Match.odds.hhad.home) + " / 平 " + (HE $Match.odds.hhad.draw) + " / 负 " + (HE $Match.odds.hhad.away) + "；总进球低位：$ttg。关键不在于西班牙能不能赢，而在于庄家已经把两球门槛摆了出来，同时又没有把三球以上极端打穿写死。赔率语言是强主线 + 3 球共振，因此模型围绕 2:0 / 3:0 展开，平局冷门用 " + (HE $Match.prediction.upset) + " 防守。"}
    "038" { return "胜平负为 $had，主胜 1.28 非常低；$hhad 总进球低位：$ttg。真正的关键信息是让一球后主胜 1.92 仍算可打，说明盘口认同比利时赢球，但并不无脑押注大穿。总进球 2 球与 3 球都压在主流区间，因此赔率结构最支持 2:0 / 2:1 和 3 球主线。"}
    "039" { return "胜平负为 $had，主胜 1.30 已经足够清晰；$hhad 总进球低位：$ttg。让一球后三项没有完全倒向主队，说明庄家更认同乌拉圭稳定拿下，而不是轻松净胜两球。赔率语言因此是主胜清楚、比分偏窄、2 球优先，模型顺着 1:0 / 2:0 与 " + (HE $Match.prediction.upset) + " 布局。"}
    "040" { return "胜平负为 $had，客胜 1.44 明显占优；$hhad 总进球低位：$ttg。受让一球后主胜与客胜几乎对冲，说明盘口核心是埃及赢球更稳，但净胜空间未必舒适。赔率结构最支持 0:1 / 0:2 和 2 球主线，" + (HE $Match.prediction.upset) + " 是唯一需要重点留的逆向路径。"}
  }

  return "胜平负目前为 $had，$hhad 总进球低位为 $ttg。模型围绕&#8220;" + $Lean.text + " + $goal&#8221;展开，同时参考昨日复盘修正低赔机械权重。"
}

function ExternalLiveData($Match) {
  if (-not ($Match.PSObject.Properties.Name -contains "external") -or -not $Match.external) {
    return "外部实时数据暂未接入。"
  }

  $ext = $Match.external
  $parts = New-Object System.Collections.Generic.List[string]

  if ($ext.fifaRanking -and $ext.fifaRanking.home -and $ext.fifaRanking.away) {
    $homeRank = $ext.fifaRanking.home.rank
    $awayRank = $ext.fifaRanking.away.rank
    if ($homeRank -or $awayRank) {
      $parts.Add("FIFA参考排名：" + (HE $Match.home) + " " + (HE ([string]$homeRank)) + "；" + (HE $Match.away) + " " + (HE ([string]$awayRank)) + "。")
    }
  }

  if ($ext.teamMeta -and $ext.teamMeta.home -and $ext.teamMeta.away) {
    $homeMeta = $ext.teamMeta.home
    $awayMeta = $ext.teamMeta.away
    if ($homeMeta.status -eq "ok" -or $awayMeta.status -eq "ok") {
      $homeInfo = if ($homeMeta.status -eq "ok") { ([string]$homeMeta.country) + " / " + ([string]$homeMeta.stadium) } else { "待补" }
      $awayInfo = if ($awayMeta.status -eq "ok") { ([string]$awayMeta.country) + " / " + ([string]$awayMeta.stadium) } else { "待补" }
      $parts.Add("球队资料：" + (HE $Match.home) + " " + (HE $homeInfo) + "；" + (HE $Match.away) + " " + (HE $awayInfo) + "。")
    }
  }

  if ($ext.injuries -and $ext.injuries.source -eq "api-sports") {
    $homeInj = @($ext.injuries.home)
    $awayInj = @($ext.injuries.away)
    $parts.Add("伤停监测：主队 " + $homeInj.Count + " 条，客队 " + $awayInj.Count + " 条。")
  }

  if ($ext.h2h -and $ext.h2h.status -eq "ok" -and @($ext.h2h.matches).Count -gt 0) {
    $latest = $ext.h2h.matches[0]
    $parts.Add("近5场交锋已接入，最近一场：" + (HE ([string]$latest.home)) + " " + (HE ([string]$latest.score)) + " " + (HE ([string]$latest.away)) + "。")
  }

  if ($ext.oddsMovement -and $ext.oddsMovement.status) {
    $status = [string]$ext.oddsMovement.status
    if ($status -eq "pending-live-odds-source") {
      $oddsTime = $null
      if ($Match.odds -and $Match.odds.had -and $Match.odds.had.updatedAt) {
        $oddsTime = [string]$Match.odds.had.updatedAt
      }
      if (-not $oddsTime -and $Match.odds -and $Match.odds.ttg -and $Match.odds.ttg.updatedAt) {
        $oddsTime = [string]$Match.odds.ttg.updatedAt
      }
      if ($oddsTime) {
        $parts.Add("赔率走势：独立实时走势源尚未接通，当前仅展示静态赔率快照，更新时间 " + (HE $oddsTime) + "。")
      } else {
        $parts.Add("赔率走势：独立实时走势源尚未接通，当前仅展示静态赔率快照。")
      }
    } else {
      $parts.Add("赔率走势：" + (HE $status) + "。")
    }
  }

  if ($parts.Count -eq 0) {
    return "外部实时数据已挂载，但本场有效摘要仍在补齐。"
  }
  return ($parts -join "")
}

function Mystic($Match, $Lean) {
  $team = HE $Lean.team
  $homeTeam = HE $Match.home
  $awayTeam = HE $Match.away
  $goal = GoalLabel $Match.prediction.totalGoals
  $upset = HE $Match.prediction.upset
  $score = HE ($Match.prediction.scores -join " / ")
  $mysticTime = HE (MatchKickoffClock $Match)

  switch ([string]$Match.id) {
    "025" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20026;&#20307;&#12289;" + $awayTeam + "&#20026;&#29992;&#65292;&#20307;&#21350;&#24471;&#29983;&#20294;&#21160;&#29275;&#19981;&#23433;&#65292;&#26159;&#8220;&#20027;&#38431;&#24471;&#21183;&#19981;&#23452;&#36807;&#28909;&#8221;&#20043;&#35937;&#65307;&#27604;&#20998;&#20027;&#32447; " + $score + "&#65292;&#20919;&#38376;&#39035;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>00:00 &#23376;&#21021;&#27700;&#27668;&#36215;&#65292;&#21033;&#38450;&#23432;&#25910;&#26463;&#19982;&#24555;&#36895;&#21453;&#20987;&#65292;" + $homeTeam + "&#19978;&#21322;&#22330;&#21344;&#21183;&#65292;&#20294;&#19979;&#21322;&#22330;&#33509;&#20037;&#25915;&#19981;&#19979;&#65292;" + $awayTeam + "&#26377;&#20599;&#19968;&#29699;&#20043;&#35937;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#22312;&#20027;&#26041;&#25915;&#21183;&#20391;&#65292;&#20294;&#24778;&#38376;&#36843;&#36817;&#20013;&#36335;&#65292;&#24635;&#36827;&#29699;&#23452;&#23432; " + $goal + "&#65292;&#19981;&#36861;&#22823;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#28779;&#22303;&#27668;&#29983;&#25206;&#20013;&#27431;&#30828;&#24230;&#65292;&#20294;&#21335;&#38750;&#33394;&#24425;&#26408;&#28779;&#20063;&#26377;&#21457;&#29983;&#65292;&#24418;&#25104;&#8220;&#20027;&#32988;&#20013;&#34255;&#24179;&#8221;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#20013;&#19978;&#65292;&#22612;&#32599;&#35265;&#8220;&#33410;&#21046;&#8221;&#65292;&#26126;&#26174;&#25351;&#21521;2&#29699;&#19982;&#23567;&#32988;&#65292;&#24524;&#30450;&#30446;&#21387;&#22823;&#32988;&#12290;"
    }
    "026" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#24471;&#29992;&#21350;&#30456;&#29983;&#65292;&#19990;&#29275;&#24471;&#20301;&#65292;&#26159;&#20170;&#26085;&#26368;&#31283;&#30340;&#26106;&#26041;&#20043;&#19968;&#65307;&#21160;&#29275;&#33853;&#20094;&#20817;&#65292;&#27604;&#20998;&#25351;&#21521; " + $score + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>03:00 &#23553;&#30424;&#20837;&#23493;&#65292;&#20027;&#38431;&#21629;&#23467;&#24471;&#22825;&#30456;&#21491;&#24380;&#20043;&#35937;&#65292;&#20020;&#22330;&#35843;&#25972;&#33021;&#21147;&#24378;&#65307;&#23458;&#38431;&#30142;&#21380;&#23467;&#35265;&#28779;&#38083;&#65292;&#38450;60&#20998;&#38047;&#21518;&#20307;&#33021;&#26029;&#23618;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#20540;&#31526;&#29983;&#20027;&#26041;&#23467;&#65292;&#24320;&#38376;&#33853;&#36793;&#36335;&#65292;&#36827;&#25915;&#36830;&#32493;&#24615;&#22909;&#65307;&#20294;&#20260;&#38376;&#33853;&#23458;&#26041;&#21453;&#20987;&#28857;&#65292;&#38450;1:1&#30340;&#36807;&#28193;&#20919;&#38376;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#30333;&#32418;&#20043;&#27668;&#24471;&#28779;&#22303;&#29983;&#25206;&#65292;&#29790;&#22763;&#24471;&#20196;&#65307;&#39134;&#26143;&#20061;&#32043;&#21160;&#65292;&#27604;&#26152;&#26085;&#26356;&#23452;&#25260;&#21040;3&#29699;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#20808;&#38459;&#21518;&#36890;&#8221;&#65292;&#22612;&#32599;&#35265;&#25112;&#36710;+&#22826;&#38451;&#65292;&#20027;&#32988;&#19982;3&#29699;&#21516;&#21521;&#12290;"
    }
    "027" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#34987;&#21046;&#65292;&#24378;&#24369;&#24046;&#26126;&#26174;&#65307;&#21160;&#29275;&#33853;&#20094;&#20817;&#65292;&#20027;&#32447;&#20174;2&#29699;&#25260;&#21040;3&#29699;&#65292;&#27604;&#20998;&#20027;&#30475; " + $score + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>06:00 &#21359;&#26102;&#26408;&#28779;&#28176;&#29983;&#65292;&#20027;&#38431;&#25915;&#20987;&#23467;&#24471;&#21513;&#26143;&#65292;&#36866;&#21512;&#21069;&#21387;&#21644;&#21047;&#20928;&#32988;&#29699;&#65307;&#23458;&#38431;&#35265;&#19971;&#26432;&#28779;&#26143;&#65292;&#38450;&#21518;&#38450;&#36830;&#38145;&#22833;&#20301;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#33853;&#20027;&#26041;&#31163;&#23467;&#65292;&#25915;&#21183;&#26126;&#65292;&#24778;&#38376;&#33853;&#23458;&#26041;&#21491;&#36335;&#65292;&#23481;&#26131;&#34987;&#25171;&#36523;&#21518;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#21152;&#25343;&#22823;&#32418;&#30333;&#24471;&#28779;&#37329;&#30456;&#21161;&#65292;&#21345;&#22612;&#23572;&#28145;&#32418;&#34429;&#26377;&#28779;&#27668;&#20294;&#21463;&#22303;&#27844;&#65292;&#26159;&#24378;&#20027;&#21387;&#21046;&#30424;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#24471;&#21183;&#36861;&#20987;&#8221;&#65292;&#22612;&#32599;&#22826;&#38451;&#21516;&#26102;&#24102;&#26469;&#22823;&#32988;&#19982;&#22823;&#29699;&#24847;&#35937;&#65292;&#20294;&#20445;&#30041;1:1&#20316;&#20026;&#26497;&#31471;&#20919;&#38376;&#12290;"
    }
    "028" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20026;&#20307;&#12289;" + $awayTeam + "&#20026;&#29992;&#65292;&#20307;&#29992;&#30456;&#25345;&#19981;&#31639;&#22823;&#21513;&#65292;&#20027;&#32988;&#26377;&#24418;&#20294;&#24179;&#23616;&#27668;&#24456;&#37325;&#65307;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>09:00 &#36784;&#24051;&#20132;&#30028;&#65292;&#20027;&#38431;&#24471;&#21270;&#31108;&#20294;&#23458;&#38431;&#26377;&#21491;&#24380;&#25252;&#36523;&#65292;&#26159;&#8220;&#20027;&#38431;&#26377;&#21183;&#65292;&#23458;&#38431;&#26377;&#25269;&#25239;&#8221;&#30340;&#30424;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#20540;&#31526;&#19981;&#23436;&#20840;&#24402;&#20027;&#65292;&#26460;&#38376;&#33853;&#20013;&#36335;&#65292;&#33410;&#22863;&#26131;&#32982;&#30528;&#65307;&#24778;&#38376;&#36843;&#36817;&#23458;&#26041;&#24555;&#36895;&#21453;&#20987;&#20391;&#65292;&#38450;0:1&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#22696;&#35199;&#21733;&#32511;&#30333;&#32418;&#26408;&#37329;&#28779;&#28151;&#26434;&#65292;&#38889;&#22269;&#30333;&#32418;&#24471;&#28779;&#21183;&#65292;&#20116;&#34892;&#19981;&#20998;&#32477;&#23545;&#39640;&#19979;&#65292;&#26356;&#20687;2&#29699;&#24179;&#34913;&#30424;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20013;&#24179;&#65292;&#22612;&#32599;&#35265;&#38544;&#22763;+&#21629;&#36816;&#20043;&#36718;&#65292;&#23567;&#29699;&#12289;&#38391;&#24179;&#12289;&#19968;&#27425;&#21453;&#20987;&#25913;&#21629;&#26159;&#20027;&#35201;&#39118;&#38505;&#12290;"
    }
    "029" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#24471;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#26377;&#25269;&#65292;&#26159;&#8220;&#24378;&#26041;&#21487;&#36194;&#65292;&#20294;&#19981;&#23452;&#36807;&#28909;&#8221;&#20043;&#35937;&#65307;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>03:00 &#23493;&#26102;&#27700;&#26408;&#30456;&#29983;&#65292;&#20027;&#38431;&#24320;&#23616;&#27668;&#21183;&#36739;&#36275;&#65292;&#20294;&#19979;&#21322;&#22330;&#33509;&#23481;&#26131;&#27714;&#31283;&#65292;&#20928;&#32988;&#31354;&#38388;&#20250;&#34987;&#21387;&#32553;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#33853;&#20027;&#26041;&#65292;&#20294;&#24778;&#38376;&#36843;&#36793;&#65292;&#20027;&#32988;&#21487;&#26395;&#12289;&#31359;&#30424;&#26410;&#24517;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#26143;&#30424;&#28779;&#22303;&#36739;&#26106;&#65292;&#26377;&#21033;&#20110;" + $homeTeam + "&#25511;&#21046;&#19968;&#27573;&#33410;&#22863;&#65292;&#20294;" + $awayTeam + "&#30340;&#26408;&#27668;&#29983;&#21457;&#20173;&#26377;&#20599;&#19968;&#29699;&#26426;&#20250;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#31283;&#20013;&#26377;&#38459;&#8221;&#65292;&#22612;&#32599;&#35265;&#30343;&#24093;&#27491;&#20301;+&#33410;&#21046;&#65292;&#25351;&#21521;&#24378;&#38431;&#36194;&#29699;&#19982;2&#29699;&#20027;&#32447;&#12290;"
    }
    "030" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $awayTeam + "&#29992;&#21350;&#24471;&#26106;&#65292;" + $homeTeam + "&#20307;&#21350;&#21463;&#21046;&#65292;&#23458;&#24378;&#20027;&#24369;&#26684;&#23616;&#26126;&#26174;&#65307;&#27604;&#20998;&#20027;&#32447;&#25351;&#21521; " + $score + "&#65292;&#20919;&#38376;&#39035;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>06:00 &#21359;&#26102;&#38451;&#27668;&#28176;&#36215;&#65292;&#23458;&#38431;&#21629;&#23467;&#24471;&#36733;&#21183;&#65292;&#26356;&#21033;&#20110;&#19979;&#21322;&#22330;&#25509;&#31649;&#27604;&#36187;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#22312;&#23458;&#26041;&#65292;&#29983;&#38376;&#21487;&#36827;&#65292;&#20294;&#26223;&#38376;&#26410;&#20840;&#24320;&#65292;&#24847;&#21619;&#30528;&#36194;&#29699;&#36335;&#24452;&#27604;&#36739;&#31361;&#20986;&#65292;&#22823;&#31359;&#26410;&#24517;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#25705;&#27931;&#21733;&#32418;&#32511;&#33394;&#24425;&#24471;&#26408;&#28779;&#20043;&#21161;&#65292;&#33487;&#26684;&#20848;&#21463;&#37329;&#27700;&#21387;&#21046;&#65292;&#26356;&#20687;&#34987;&#21160;&#38450;&#23432;&#30424;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#20808;&#25289;&#25199;&#21518;&#21457;&#21147;&#8221;&#65292;&#22612;&#32599;&#25112;&#36710;&#36870;&#20301;&#25552;&#37266;&#23458;&#32988;&#34429;&#20248;&#65292;&#20173;&#35201;&#30041;&#24847;1:1&#30340;&#25289;&#38199;&#24179;&#23616;&#12290;"
    }
    "031" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#22823;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#34987;&#21387;&#65292;&#26159;&#20856;&#22411;&#30340;&#24378;&#38431;&#21387;&#21046;&#23616;&#12290;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#21482;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>08:30 &#36784;&#26408;&#36716;&#28779;&#65292;&#25915;&#21183;&#27491;&#26106;&#65292;" + $homeTeam + "&#26377;&#21047;&#20928;&#32988;&#29699;&#30340;&#21629;&#27668;&#65292;&#19979;&#21322;&#22330;&#20877;&#36827;&#29699;&#30340;&#35937;&#24847;&#24456;&#37325;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#20540;&#31526;&#20837;&#20027;&#23467;&#65292;&#24320;&#38376;&#19982;&#29983;&#38376;&#21516;&#21521;&#65292;&#36825;&#26159;&#23569;&#35265;&#30340;&#24378;&#21387;&#21046;&#21487;&#24310;&#23637;&#30424;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#24052;&#35199;&#40644;&#32511;&#28779;&#26408;&#20004;&#26106;&#65292;&#28023;&#22320;&#21463;&#27700;&#22303;&#29301;&#21046;&#65292;&#20116;&#34892;&#24046;&#36739;&#22823;&#65292;&#22823;&#29699;&#23614;&#37096;&#19981;&#23452;&#20302;&#20272;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#39034;&#21183;&#25910;&#21151;&#8221;&#65292;&#22612;&#32599;&#35265;&#22826;&#38451;+&#19990;&#30028;&#65292;&#25351;&#21521;&#24378;&#32988;&#19982;4&#29699;&#20027;&#32447;&#12290;"
    }
    "032" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20026;&#20307;&#12289;" + $awayTeam + "&#20026;&#29992;&#65292;&#20307;&#29992;&#30456;&#20105;&#65292;&#24179;&#27668;&#36739;&#37325;&#65292;&#26159;&#8220;&#21487;&#30475;&#20027;&#38431;&#31245;&#28909;&#65292;&#20294;&#19981;&#23452;&#37325;&#21387;&#8221;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>11:00 &#21320;&#26102;&#28779;&#27668;&#24378;&#65292;&#24773;&#32490;&#21644;&#23545;&#25239;&#23481;&#26131;&#25918;&#22823;&#65292;&#20808;&#36827;&#29699;&#19968;&#26041;&#21453;&#32780;&#26356;&#23481;&#26131;&#20445;&#23432;&#25910;&#32447;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#26460;&#38376;&#19982;&#24778;&#38376;&#30456;&#37051;&#65292;&#24847;&#21619;&#30528;&#20013;&#36335;&#32544;&#26007;&#22810;&#12289;&#36793;&#36335;&#20915;&#32988;&#35201;&#32032;&#37325;&#65292;&#30340;&#30830;&#26356;&#20687;2&#29699;&#20026;&#19978;&#38480;&#30340;&#32494;&#26432;&#30424;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#22303;&#32819;&#20854;&#28779;&#22303;&#20043;&#27668;&#31245;&#26106;&#65292;&#24052;&#25289;&#22317;&#30333;&#32418;&#24471;&#37329;&#27700;&#25252;&#20307;&#65292;&#20004;&#36793;&#26377;&#26426;&#20250;&#20114;&#30475;&#23545;&#26041;&#38169;&#35823;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#25345;&#34913;&#21518;&#20915;&#26029;&#8221;&#65292;&#22612;&#32599;&#35265;&#27491;&#20041;+&#21147;&#37327;&#65292;&#25903;&#25345;&#23567;&#27604;&#20998;&#12289;&#34987;&#21160;&#38450;&#20919;&#38376;&#30340;&#21452;&#37325;&#38450;&#32447;&#12290;"
    }
    "033" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#31245;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#26377;&#25269;&#65292;&#26159;&#8220;&#20027;&#38431;&#21487;&#36194;&#65292;&#20294;&#19981;&#23452;&#36807;&#28909;&#8221;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#20316;&#20026;&#24403;&#22320;&#36215;&#21350;&#26102;&#28857;&#65292;&#30424;&#24847;&#26356;&#20559;&#21521;&#20808;&#31283;&#20303;&#38450;&#32447;&#20877;&#24819;&#21150;&#27861;&#25226;&#27604;&#36187;&#25171;&#24320;&#65292;&#25152;&#20197;&#24179;&#23616;&#27668;&#19981;&#33021;&#23436;&#20840;&#19995;&#25481;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#20559;&#20027;&#26041;&#65292;&#20294;&#24778;&#38376;&#30424;&#26041;&#26410;&#36828;&#65292;&#34920;&#31034;&#20027;&#38431;&#33021;&#36194;&#65292;&#20294;&#31359;&#30424;&#38656;&#30475;&#20013;&#21518;&#27573;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#33655;&#20848;&#27225;&#33394;&#28779;&#22303;&#24471;&#21183;&#65292;&#29790;&#20856;&#40644;&#34013;&#20043;&#27668;&#20559;&#37329;&#27700;&#65292;&#26131;&#24418;&#25104;&#8220;&#20027;&#38431;&#21387;&#21046;+&#23458;&#38431;&#20599;&#19968;&#29699;&#8221;&#32467;&#26500;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#31283;&#20013;&#26377;&#38459;&#8221;&#65292;&#22612;&#32599;&#35265;&#30343;&#24093;+&#33410;&#21046;&#65292;&#25351;&#21521;3&#29699;&#20027;&#32447;&#21644;1:1&#20919;&#38376;&#20445;&#30041;&#12290;"
    }
    "034" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#24471;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#21463;&#21046;&#65292;&#26159;&#20170;&#26085;&#36739;&#31283;&#30340;&#24378;&#26041;&#20043;&#19968;&#65307;&#27604;&#20998;&#25351;&#21521; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#20316;&#20026;&#24403;&#22320;&#36215;&#21350;&#26102;&#28857;&#65292;&#30424;&#38754;&#23545;&#20027;&#38431;&#21518;&#31243;&#25552;&#36895;&#26356;&#26377;&#21033;&#65292;&#26131;&#23558;&#27604;&#36187;&#25512;&#21521;&#31532;&#20108;&#29699;&#25110;&#31532;&#19977;&#29699;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#20540;&#31526;&#29983;&#20027;&#26041;&#65292;&#24320;&#38376;&#33853;&#20013;&#21069;&#22330;&#65292;&#26159;&#26377;&#21033;&#20110;&#25235;&#20027;&#32988;&#19982;3&#29699;&#30340;&#32467;&#26500;&#30424;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#24503;&#22269;&#40657;&#30333;&#28779;&#37329;&#30456;&#29983;&#65292;&#31185;&#29305;&#36842;&#29926;&#27225;&#32511;&#26408;&#28779;&#26377;&#21453;&#20987;&#27668;&#65292;&#25152;&#20197;&#26356;&#20687;2:0 / 3:1&#32780;&#38750;&#21333;&#32431;&#22823;&#23648;&#26432;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#20808;&#31283;&#21518;&#24320;&#8221;&#65292;&#22612;&#32599;&#25112;&#36710;+&#22826;&#38451;&#21516;&#21521;&#65292;&#20027;&#32988;&#20027;&#32447;&#28165;&#26224;&#12290;"
    }
    "035" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#27665;&#65292;" + $awayTeam + "&#29992;&#21350;&#34987;&#21387;&#65292;&#26159;&#24378;&#20027;&#21387;&#21046;&#30424;&#30340;&#35937;&#24847;&#65307;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#20316;&#20026;&#24403;&#22320;&#36215;&#21350;&#26102;&#28857;&#65292;&#20027;&#38431;&#21069;&#22330;&#36830;&#32493;&#26045;&#21387;&#30340;&#36135;&#37327;&#26356;&#23481;&#26131;&#25171;&#20986;&#26469;&#65292;&#20294;&#21518;&#27573;&#33509;&#25910;&#21147;&#65292;&#23458;&#38431;&#20173;&#26377;&#20599;&#19968;&#29699;&#30340;&#31354;&#38388;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#20559;&#20027;&#65292;&#29983;&#38376;&#26410;&#31163;&#65292;&#25915;&#21183;&#33021;&#34987;&#24310;&#23637;&#25104;&#31532;&#20108;&#29699;&#12289;&#31532;&#19977;&#29699;&#65292;&#26159;&#26631;&#20934;3&#29699;&#32467;&#26500;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#21380;&#29916;&#22810;&#23572;&#40644;&#34013;&#24471;&#28779;&#22303;&#30456;&#25206;&#65292;&#24211;&#25289;&#32034;&#40644;&#34013;&#33410;&#22863;&#20559;&#24555;&#65292;&#26356;&#20687;&#24378;&#38431;&#21387;&#21046;&#19979;&#30340;2:0 / 3:0&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#39034;&#21183;&#25512;&#36827;&#8221;&#65292;&#22612;&#32599;&#35265;&#21147;&#37327;+&#19990;&#30028;&#65292;&#25903;&#25345;&#24378;&#21387;&#21046;&#20027;&#32988;&#12290;"
    }
    "036" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $awayTeam + "&#29992;&#21350;&#24471;&#26106;&#65292;" + $homeTeam + "&#20307;&#21350;&#21463;&#25233;&#65292;&#23458;&#24378;&#26684;&#23616;&#36739;&#26126;&#26174;&#65307;&#27604;&#20998;&#20027;&#32447;&#25351;&#21521; " + $score + "&#65292;&#20919;&#38376;&#39035;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#20316;&#20026;&#24403;&#22320;&#36215;&#21350;&#26102;&#28857;&#65292;&#26356;&#26377;&#21033;&#20110;&#33410;&#22863;&#25511;&#21046;&#33021;&#21147;&#26356;&#22909;&#30340;&#19968;&#26041;&#65292;&#23545;" + $awayTeam + "&#26356;&#26377;&#21033;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#22312;&#23458;&#26041;&#65292;&#26223;&#38376;&#19981;&#31639;&#24378;&#65292;&#24847;&#21619;&#30528;&#36194;&#29699;&#26041;&#21521;&#28165;&#26970;&#65292;&#20294;&#27604;&#20998;&#20173;&#20559;&#31364;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#26085;&#26412;&#34013;&#30333;&#24471;&#37329;&#27700;&#28165;&#27668;&#65292;&#31361;&#23612;&#26031;&#32418;&#30333;&#28779;&#37329;&#26377;&#21453;&#25169;&#65292;&#26131;&#24418;&#25104;0:1 / 0:2&#36825;&#31181;&#23567;&#27604;&#20998;&#23458;&#32988;&#26684;&#23616;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#20808;&#25511;&#21518;&#21457;&#8221;&#65292;&#22612;&#32599;&#27491;&#20041;+&#26143;&#26143;&#65292;&#23458;&#32988;&#20027;&#32447;&#28165;&#26224;&#65292;&#24179;&#23616;&#26159;&#21807;&#19968;&#35201;&#38450;&#30340;&#24847;&#22806;&#12290;"
    }
    "037" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#22823;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#21463;&#21046;&#65292;&#23646;&#20110;&#24378;&#26041;&#21487;&#25511;&#20840;&#23616;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#21482;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#20316;&#20026;&#24403;&#22320;&#36215;&#21350;&#26102;&#28857;&#65292;&#21463;&#30424;&#27668;&#24433;&#21709;&#65292;&#26356;&#20687;&#19978;&#21322;&#22330;&#20808;&#35835;&#23616;&#12289;&#19979;&#21322;&#22330;&#20877;&#25226;&#33410;&#22863;&#25351;&#21040;&#24378;&#26041;&#36523;&#19978;&#65292;&#21322;&#20840;&#22330;&#23452;&#30475;&#24179;/&#32988;&#25110;&#32988;/&#32988;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#29983;&#20027;&#65292;&#26223;&#38376;&#21448;&#33021;&#25509;&#19978;&#21518;&#31243;&#25915;&#21183;&#65292;&#34892;&#30424;&#35821;&#35328;&#23601;&#26159;&#8220;&#24378;&#38431;&#26202;&#21457;&#21147;&#8221;&#65292;&#25903;&#25345;2:0 / 3:0&#36825;&#31181;&#21518;&#31243;&#25289;&#24320;&#20928;&#32988;&#30340;&#33050;&#26412;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#35199;&#29677;&#29273;&#32418;&#40644;&#28779;&#22303;&#24471;&#21183;&#65292;&#27801;&#29305;&#32511;&#30333;&#26408;&#27668;&#26377;&#25269;&#20294;&#38590;&#20197;&#38271;&#26102;&#38388;&#25215;&#21463;&#22260;&#25915;&#65292;&#26131;&#24418;&#25104;&#8220;&#19978;&#21322;&#22330;&#38264;&#30528;&#65292;&#19979;&#21322;&#22330;&#24320;&#38376;&#8221;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#31283;&#20013;&#21518;&#24320;&#8221;&#65292;&#22612;&#32599;&#22826;&#38451;+&#25112;&#36710;&#21516;&#21521;&#65292;&#24378;&#32988;&#20027;&#32447;&#28165;&#26224;&#65292;&#24179;&#23616;&#21482;&#26159;&#24378;&#38431;&#19978;&#21322;&#22330;&#25928;&#29575;&#19981;&#22815;&#26102;&#30340;&#22791;&#38450;&#12290;"
    }
    "038" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#24471;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#26377;&#25269;&#65292;&#26159;&#8220;&#20027;&#38431;&#36194;&#38754;&#22823;&#65292;&#20294;&#31359;&#30424;&#38656;&#30475;&#33410;&#22863;&#8221;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#30340;&#27668;&#21475;&#26356;&#21033;&#20110;&#24378;&#38431;&#20808;&#25511;&#23616;&#38754;&#12289;&#20877;&#31561;&#23545;&#25163;&#20986;&#38169;&#65292;&#21322;&#20840;&#22330;&#26356;&#39034;&#30340;&#33050;&#26412;&#26159;&#24179;/&#32988;&#25110;&#32988;/&#32988;&#65292;&#32780;&#19981;&#26159;&#19968;&#24320;&#22330;&#23601;&#23558;&#27604;&#36187;&#25171;&#31359;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#33853;&#20027;&#26041;&#65292;&#20294;&#24778;&#38376;&#23432;&#22312;&#23458;&#38431;&#21453;&#20987;&#32447;&#19978;&#65292;&#24847;&#21619;&#30528;&#27604;&#21033;&#26102;&#20027;&#32988;&#26159;&#22823;&#27010;&#29575;&#65292;&#21487;&#26159;&#20234;&#26391;&#20173;&#26377;&#19968;&#27425;&#25226;&#27604;&#20998;&#25289;&#22238;&#21040;2:1&#30340;&#31354;&#38388;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#27604;&#21033;&#26102;&#40657;&#40644;&#28779;&#37329;&#30456;&#29983;&#65292;&#20234;&#26391;&#32418;&#30333;&#28779;&#26408;&#20559;&#20110;&#21453;&#20987;&#65292;&#26131;&#24418;&#25104;&#8220;&#20027;&#38431;&#25511;&#22330;+&#23458;&#38431;&#20599;&#19968;&#29699;&#8221;&#30340;&#32047;&#35745;&#24335;&#33050;&#26412;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#20808;&#31283;&#21518;&#23450;&#8221;&#65292;&#22612;&#32599;&#30343;&#24093;+&#33410;&#21046;&#65292;&#20027;&#32988;&#20027;&#32447;&#28165;&#26970;&#65292;&#20851;&#38190;&#26159;&#21322;&#22330;&#33021;&#19981;&#33021;&#25552;&#21069;&#30772;&#23616;&#12290;"
    }
    "039" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#24471;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#21487;&#25269;&#65292;&#26159;&#8220;&#21487;&#32988;&#20294;&#23452;&#31364;&#19981;&#23452;&#20998;&#22823;&#8221;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#23545;&#25239;&#24847;&#21619;&#37325;&#65292;&#26356;&#20687;&#20808;&#32905;&#25615;&#21518;&#20915;&#32988;&#30340;&#26102;&#28857;&#65292;&#21322;&#20840;&#22330;&#26356;&#39034;&#30340;&#26159;&#24179;/&#32988;&#65292;&#22914;&#26524;&#20027;&#38431;&#26089;&#30772;&#23616;&#65292;&#25165;&#20250;&#39034;&#25512;&#21040;&#32988;/&#32988;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#20559;&#20027;&#65292;&#20294;&#29983;&#38376;&#26410;&#33073;&#31163;&#20013;&#36335;&#32422;&#26463;&#65292;&#24847;&#21619;&#30528;&#20116;&#25289;&#22205;&#30340;&#32905;&#25615;&#21619;&#24456;&#37325;&#65292;&#20027;&#32988;&#33021;&#30475;&#65292;&#21487;&#27604;&#20998;&#22810;&#21322;&#20250;&#34987;&#38145;&#22312;1:0 / 2:0&#36825;&#31181;&#31364;&#21475;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#20044;&#25289;&#22317;&#22825;&#34013;&#28779;&#22303;&#31245;&#26106;&#65292;&#20315;&#24471;&#35282;&#32511;&#28784;&#27700;&#22303;&#20559;&#20110;&#25302;&#33410;&#22863;&#65292;&#26131;&#24418;&#25104;&#8220;&#19978;&#21322;&#22330;&#25345;&#34913;&#65292;&#19979;&#21322;&#22330;&#20915;&#33021;&#8221;&#30340;&#32047;&#35745;&#30424;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#31283;&#25171;&#31283;&#25910;&#8221;&#65292;&#22612;&#32599;&#27491;&#20041;+&#21147;&#37327;&#65292;&#20027;&#32988;&#26377;&#24213;&#65292;&#20294;1:1&#20173;&#26159;&#21807;&#19968;&#38656;&#30041;&#30340;&#20919;&#38376;&#21453;&#25169;&#12290;"
    }
    "040" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $awayTeam + "&#29992;&#21350;&#24471;&#26106;&#65292;" + $homeTeam + "&#20307;&#21350;&#21463;&#21046;&#65292;&#23646;&#20110;&#23458;&#24378;&#19988;&#23567;&#27604;&#20998;&#26356;&#39034;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#32447;&#25351;&#21521; " + $score + "&#65292;&#20919;&#38376;&#39035;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#30340;&#22812;&#22330;&#27668;&#21475;&#26356;&#21033;&#20110;&#38453;&#22411;&#23436;&#25972;&#30340;&#19968;&#26041;&#65292;&#21322;&#20840;&#22330;&#26368;&#39034;&#30340;&#36335;&#24452;&#26159;&#24179;/&#36127;&#25110;&#36127;/&#36127;&#65292;&#22914;&#26524;&#22522;&#22467;&#22312;&#21069;30&#20998;&#38047;&#23601;&#39046;&#20808;&#65292;&#27604;&#36187;&#23601;&#20250;&#24456;&#24555;&#36827;&#20837;&#25511;&#33410;&#22863;&#27169;&#24335;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#22312;&#23458;&#26041;&#65292;&#20294;&#26223;&#38376;&#19981;&#24378;&#65292;&#36825;&#26159;&#26631;&#20934;&#30340;&#8220;&#33021;&#36194;&#19981;&#19968;&#23450;&#22823;&#32988;&#8221;&#30424;&#65292;0:1 / 0:2 &#27604;&#31435;&#21051;&#25918;&#22823;&#21040;&#22823;&#29699;&#26356;&#31526;&#21512;&#30424;&#24847;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>&#22467;&#21450;&#32418;&#30333;&#40657;&#24471;&#28779;&#22303;&#31283;&#21183;&#65292;&#26032;&#35199;&#20848;&#30333;&#40657;&#20043;&#27668;&#20559;&#20110;&#38450;&#23432;&#21453;&#25169;&#65292;&#26131;&#24418;&#25104;&#8220;&#23458;&#38431;&#20808;&#25511;&#65292;&#20027;&#38431;&#31561;&#20320;&#20986;&#38169;&#8221;&#30340;&#33050;&#26412;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#20808;&#31364;&#21518;&#31361;&#30772;&#8221;&#65292;&#22612;&#32599;&#38544;&#22763;+&#25112;&#36710;&#36870;&#20301;&#65292;&#23458;&#32988;&#20027;&#32447;&#28165;&#26224;&#65292;&#24179;&#23616;&#26159;&#21807;&#19968;&#38656;&#30041;&#24847;&#30340;&#21345;&#28857;&#12290;"
    }
    "041" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#26356;&#26126;&#65292;" + $awayTeam + "&#29992;&#21350;&#21463;&#21046;&#65292;&#26159;&#20027;&#38431;&#21487;&#25511;&#20840;&#23616;&#20294;&#19981;&#33021;&#24573;&#30053;&#38450;&#24179;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#32447;&#30475; " + $score + "&#65292;&#20919;&#38376;&#21482;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#30340;&#27668;&#21475;&#26356;&#20687;&#20808;&#35835;&#23616;&#12289;&#20877;&#25552;&#33410;&#22863;&#65292;&#25152;&#20197;&#21322;&#20840;&#22330;&#26368;&#39034;&#30340;&#36335;&#24452;&#26159;&#24179;/&#32988;&#25110;&#32988;/&#32988;&#65292;&#32780;&#19981;&#26159;&#19968;&#24320;&#22330;&#23601;&#31435;&#21051;&#25289;&#24320;&#24046;&#36317;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#20559;&#20027;&#26041;&#25915;&#21183;&#23467;&#65292;&#29983;&#38376;&#33021;&#25509;&#19978;&#21518;&#31243;&#65292;&#24847;&#21619;&#30528;&#24471;&#21183;&#26041;&#21482;&#35201;&#20808;&#30772;&#23616;&#65292;&#27604;&#36187;&#23601;&#20250;&#39034;&#30528;2:0 / 2:1 / 3:1 &#36825;&#31867;&#24378;&#38431;&#25511;&#33410;&#22863;&#33050;&#26412;&#21457;&#23637;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>" + $homeTeam + "&#27668;&#22330;&#26356;&#24448;&#21069;&#21387;&#65292;" + $awayTeam + "&#27668;&#21475;&#20559;&#20110;&#20808;&#23432;&#21518;&#31561;&#21453;&#20987;&#65292;&#26131;&#24418;&#25104;&#8220;&#20027;&#38431;&#38271;&#26102;&#38388;&#25511;&#29699;&#65292;&#23458;&#38431;&#29992;&#23567;&#27425;&#25968;&#21147;&#22270;&#25250;&#20998;&#21449;&#8221;&#30340;&#32047;&#35745;&#30424;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#20808;&#31283;&#21518;&#24320;&#8221;&#65292;&#22612;&#32599;&#22826;&#38451;+&#30343;&#24093;&#21516;&#21521;&#65292;&#24378;&#32988;&#20027;&#32447;&#28165;&#26224;&#65292;&#29572;&#23398;&#21516;&#26102;&#25903;&#25345;&#21322;&#22330;&#38264;&#20303;&#21518;&#19979;&#21322;&#22330;&#25289;&#24320;&#20928;&#32988;&#12290;"
    }
    "042" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#24471;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#26377;&#25269;&#65292;&#26159;&#20027;&#38431;&#33021;&#36194;&#20294;&#19981;&#23452;&#25226;&#31359;&#30424;&#30475;&#24471;&#36807;&#28909;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#32447;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#26356;&#21033;&#20110;&#24378;&#38431;&#20808;&#25511;&#22330;&#12289;&#20877;&#31561;&#23545;&#25163;&#20986;&#38169;&#65292;&#21322;&#20840;&#22330;&#26368;&#39034;&#30340;&#26159;&#24179;/&#32988;&#25110;&#32988;/&#32988;&#65292;&#20294;&#22914;&#26524;&#19978;&#21322;&#22330;&#20037;&#25915;&#19981;&#19979;&#65292;&#24179;&#23616;&#20445;&#25252;&#20250;&#26126;&#26174;&#21464;&#37325;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#33853;&#20027;&#26041;&#65292;&#24778;&#38376;&#21387;&#22312;&#23458;&#38431;&#23450;&#20301;&#29699;&#19982;&#21453;&#20987;&#32447;&#19978;&#65292;&#34920;&#31034;&#20027;&#32988;&#26041;&#21521;&#21487;&#20197;&#30475;&#65292;&#20294;&#23545;&#25163;&#20173;&#26377;&#25226;&#27604;&#20998;&#25289;&#25104;2:1 &#25110;1:1 &#30340;&#31354;&#38388;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>" + $homeTeam + "&#26356;&#20559;&#21521;&#25511;&#29699;&#21644;&#38271;&#26102;&#38388;&#22312;&#21069;&#22330;&#26045;&#21387;&#65292;" + $awayTeam + "&#21017;&#26356;&#20381;&#36182;&#21453;&#20987;&#25928;&#29575;&#19982;&#23450;&#20301;&#29699;&#36136;&#37327;&#65292;&#26131;&#24418;&#25104;&#8220;&#20027;&#38431;&#25511;&#22330;&#65292;&#23458;&#38431;&#25250;&#20960;&#27425;&#39640;&#36136;&#37327;&#20998;&#21449;&#8221;&#30340;&#21457;&#23637;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#20808;&#25511;&#21518;&#23450;&#8221;&#65292;&#22612;&#32599;&#30343;&#24093;+&#33410;&#21046;&#65292;&#20027;&#32988;&#20027;&#32447;&#28165;&#26224;&#65292;&#20851;&#38190;&#23601;&#22312;&#21322;&#22330;&#33021;&#19981;&#33021;&#25552;&#21069;&#30772;&#23616;&#12290;"
    }
    "043" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $homeTeam + "&#20307;&#21350;&#24471;&#26106;&#65292;" + $awayTeam + "&#29992;&#21350;&#21487;&#25269;&#65292;&#26159;&#21487;&#32988;&#20294;&#22810;&#21322;&#34987;&#38145;&#22312;&#23567;&#27604;&#20998;&#21306;&#38388;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#32447;&#30475; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#30340;&#27668;&#21475;&#23545;&#25239;&#24847;&#21619;&#37325;&#65292;&#26356;&#20687;&#20808;&#32905;&#25615;&#12289;&#20877;&#20915;&#32988;&#30340;&#26102;&#28857;&#65292;&#21322;&#20840;&#22330;&#26368;&#39034;&#30340;&#36335;&#24452;&#26159;&#24179;/&#32988;&#65292;&#22914;&#26524;&#20027;&#38431;&#26089;&#30772;&#23616;&#65292;&#25165;&#20250;&#39034;&#25512;&#21040;&#32988;/&#32988;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#20559;&#20027;&#65292;&#20294;&#29983;&#38376;&#26410;&#33073;&#31163;&#20013;&#36335;&#32422;&#26463;&#65292;&#24847;&#21619;&#30528;&#27604;&#36187;&#22823;&#37096;&#20998;&#26102;&#38388;&#20250;&#38145;&#22312;1:0 / 2:0 / 1:1 &#36825;&#31181;&#31364;&#21475;&#65292;&#19981;&#26159;&#21551;&#21160;&#39640;&#27604;&#20998;&#30340;&#30424;&#38754;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>" + $homeTeam + "&#27668;&#21475;&#26356;&#31283;&#65292;" + $awayTeam + "&#21017;&#26356;&#20559;&#20110;&#25226;&#27604;&#36187;&#25289;&#25104;&#30772;&#30862;&#23545;&#25239;&#12290;&#25152;&#20197;&#25972;&#20307;&#21457;&#23637;&#26356;&#20687;&#8220;&#20027;&#38431;&#20808;&#31283;&#20303;&#23545;&#25239;&#65292;&#28982;&#21518;&#38752;&#32454;&#33410;&#25343;&#36208;&#27604;&#36187;&#8221;&#30340;&#36208;&#27861;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#35265;&#8220;&#31283;&#25171;&#31283;&#25910;&#8221;&#65292;&#22612;&#32599;&#27491;&#20041;+&#21147;&#37327;&#65292;&#20027;&#32988;&#26377;&#24213;&#65292;&#20294;1:1 &#20173;&#26159;&#38656;&#30041;&#30524;&#30340;&#20919;&#38376;&#21453;&#25169;&#12290;"
    }
    "044" {
      return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $awayTeam + "&#29992;&#21350;&#24471;&#26106;&#65292;" + $homeTeam + "&#20307;&#21350;&#21463;&#21046;&#65292;&#26159;&#23458;&#24378;&#19988;&#33410;&#22863;&#20559;&#31283;&#30340;&#30424;&#12290;&#27604;&#20998;&#20027;&#32447;&#25351;&#21521; " + $score + "&#65292;&#20919;&#38376;&#39035;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#30340;&#27668;&#21475;&#26356;&#21033;&#20110;&#38453;&#22411;&#23436;&#25972;&#12289;&#25511;&#33410;&#22863;&#33021;&#21147;&#26356;&#22909;&#30340;&#19968;&#26041;&#65292;&#21322;&#20840;&#22330;&#26368;&#39034;&#30340;&#36335;&#24452;&#26159;&#24179;/&#36127;&#25110;&#36127;/&#36127;&#65292;&#27604;&#36187;&#24448;&#24448;&#35201;&#31561;&#21040;&#20013;&#21518;&#27573;&#25165;&#20250;&#23436;&#20840;&#20542;&#21521;&#23458;&#38431;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#22312;&#23458;&#26041;&#65292;&#26223;&#38376;&#24182;&#19981;&#22815;&#24378;&#65292;&#34920;&#31034;&#24471;&#21183;&#26041;&#26356;&#20687;&#29992;0:1 / 0:2 &#21435;&#25511;&#21046;&#27604;&#36187;&#65292;&#32780;&#19981;&#26159;&#25226;&#33410;&#22863;&#25289;&#25104;&#22823;&#24320;&#22823;&#21512;&#12290;<br><strong>&#24178;&#25903;&#20116;&#34892;/&#39134;&#26143;&#65306;</strong>" + $awayTeam + "&#27668;&#22330;&#26356;&#31283;&#65292;" + $homeTeam + "&#21017;&#26356;&#20559;&#20110;&#38450;&#23432;&#21453;&#25169;&#12290;&#25152;&#20197;&#25972;&#20307;&#26356;&#20687;&#8220;&#23458;&#38431;&#20808;&#25511;&#25163;&#37324;&#30340;&#33410;&#22863;&#65292;&#20027;&#38431;&#31561;&#20320;&#20986;&#38169;&#8221;&#30340;&#20272;&#26412;&#12290;<br><strong>&#35832;&#33883;&#31070;&#25968;/&#22612;&#32599;&#65306;</strong>&#31614;&#24847;&#20026;&#8220;&#20808;&#31364;&#21518;&#31361;&#30772;&#8221;&#65292;&#22612;&#32599;&#38544;&#22763;+&#25112;&#36710;&#36870;&#20301;&#65292;&#23458;&#32988;&#20027;&#32447;&#28165;&#26224;&#65292;&#24179;&#23616;&#26159;&#21807;&#19968;&#38656;&#30041;&#24847;&#30340;&#21345;&#28857;&#12290;"
    }
  }

  return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $team + " &#24471;&#20307;&#29992;&#29983;&#25206;&#65292;&#20027;&#32447;&#27604;&#20998;&#25351;&#21521; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#32043;&#24494;&#27969;&#26102;&#65306;</strong>" + $mysticTime + " &#30340;&#27668;&#21475;&#20808;&#30475;&#21322;&#22330;&#33021;&#21542;&#30772;&#23616;&#65292;&#33410;&#22863;&#19968;&#26086;&#34987;&#24471;&#21183;&#26041;&#25511;&#22312;&#25163;&#37324;&#65292;&#21322;&#20840;&#22330;&#23601;&#20250;&#39034;&#30528;&#20027;&#32447;&#24310;&#23637;&#12290;<br><strong>&#22855;&#38376;&#36929;&#30002;&#65306;</strong>&#24320;&#38376;&#19982;&#24778;&#38376;&#30340;&#36317;&#31163;&#20915;&#23450;&#27604;&#20998;&#26159;&#32487;&#32493;&#25910;&#31364;&#65292;&#36824;&#26159;&#34987;&#20919;&#38376;&#25289;&#22238;&#12290;<br><strong>&#29572;&#23398;&#32508;&#21512;&#65306;</strong>&#29699;&#36335;&#30475; " + $goal + "&#65292;&#24471;&#21183;&#26041;&#39034;&#65292;&#20294;&#20173;&#35201;&#20445;&#30041;&#19968;&#26465;&#20919;&#38376;&#38450;&#32447;&#65292;&#29305;&#21035;&#26159;1:1 &#25110;&#19968;&#29699;&#23567;&#32988;&#30340;&#21453;&#25289;&#33050;&#26412;&#12290;"
}

function ModelFlow() {
  return @"
<section id="model" class="section"><h2>&#26681;&#25454;&#20170;&#26085;&#27604;&#36187;&#25645;&#24314;&#30340;&#20116;&#23618;&#39044;&#27979;&#27169;&#22411;</h2><div class="modelFlow">
<div class="layer l1"><h3>&#31532;&#19968;&#23618;&#65306;&#25968;&#25454;&#36755;&#20837;</h3><div class="nodes"><span>FIFA&#25490;&#21517;/&#21160;&#24577;&#26435;&#37325;</span><span>&#27604;&#36187;&#32479;&#35745; xG/xGA</span><span>&#29699;&#21592;&#29366;&#24577;/&#20260;&#20572;</span><span>&#36187;&#20107;&#24773;&#22659;/&#22825;&#27668;</span><span>&#36180;&#29575;/&#24066;&#22330;&#20449;&#21495;</span></div></div>
<div class="arrow">&#8595;</div>
<div class="layer l2"><h3>&#31532;&#20108;&#23618;&#65306;&#29305;&#24449;&#24037;&#31243;</h3><div class="nodes"><span>Elo&#35780;&#20998;&#31995;&#32479;</span><span>&#27850;&#26494;&#36827;&#29699;&#27169;&#22411;</span><span>&#23545;&#38453;&#21382;&#21490;&#32534;&#30721;</span><span>&#38544;&#21547;&#27010;&#29575;&#21435;&#27700;</span><span>&#20020;&#22330;&#29366;&#24577;&#21521;&#37327;</span></div></div>
<div class="arrow">&#8595;</div>
<div class="layer l3"><h3>&#31532;&#19977;&#23618;&#65306;&#38598;&#25104;&#27169;&#22411;</h3><div class="nodes"><span>&#36125;&#21494;&#26031;&#23618;&#32423;&#27169;&#22411;</span><span>XGBoost / RF</span><span>LSTM&#24207;&#21015;&#27169;&#22411;</span><span>&#24066;&#22330;&#26657;&#20934;&#22120;</span><span>&#24322;&#24120;&#20919;&#38376;&#26816;&#27979;</span></div></div>
<div class="arrow">&#8595;</div>
<div class="layer l4"><h3>&#31532;&#22235;&#23618;&#65306;&#33945;&#29305;&#21345;&#27931;&#36187;&#31243;&#27169;&#25311;</h3><div class="nodes"><span>10&#19975;&#27425;&#27169;&#25311;</span><span>&#28857;&#29699;&#19987;&#39033;&#27169;&#22359;</span><span>&#21160;&#24577;&#20301;&#32622;&#26356;&#26032;</span><span>80%/95%&#32622;&#20449;&#21306;&#38388;</span><span>&#32452;&#21512;&#39118;&#38505;&#22238;&#25764;</span></div></div>
<div class="arrow">&#8595;</div>
<div class="layer l5"><h3>&#31532;&#20116;&#23618;&#65306;&#20170;&#26085;&#39044;&#27979;&#36755;&#20986;</h3><div class="nodes"><span>&#24635;&#36827;&#29699;&#20998;&#24067;</span><span>&#32988;&#24179;&#36127;&#27010;&#29575;</span><span>&#31283;&#32966;&#27604;&#20998;</span><span>&#20919;&#38376;&#33050;&#26412;</span><span>&#29572;&#23398;&#34701;&#21512;&#32467;&#35770;</span></div></div>
</div></section>
"@
}

function Quick($Match, $Lean) {
  return "&#21333;&#22330;&#31616;&#35780;&#65306;&#20808;&#30475; " + (GoalLabel $Match.prediction.totalGoals) + "&#65292;&#27604;&#20998;&#20248;&#20808; " + (HE ($Match.prediction.scores -join " / ")) + "&#65292;&#21516;&#26102;&#29992; " + (HE $Match.prediction.upset) + " &#20570;&#20919;&#38376;&#38450;&#23432;&#12290;"
}

function MysticBrief($Match, $Lean) {
  if ($Lean.code -eq "draw") {
    return "平局保护优先，球路看 " + (GoalLabel $Match.prediction.totalGoals) + "，冷门防 " + (HE $Match.prediction.upset)
  }
  return (HE $Lean.team) + "&#24471;&#21183;&#65292;&#29699;&#36335;&#30475; " + (GoalLabel $Match.prediction.totalGoals) + "&#65292;&#20919;&#38376;&#38450; " + (HE $Match.prediction.upset)
}

function Clamp([double]$Value, [double]$Min, [double]$Max) {
  return [math]::Min($Max, [math]::Max($Min, $Value))
}

function ToDouble($Value, [double]$Default = 0) {
  try { return [double]$Value } catch { return $Default }
}

function NormalizeGroupName([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
  if ($Value -match "^Group\s+([A-Z])$") { return "$($Matches[1])组" }
  return $Value.Trim()
}

function InferGroupName($Match) {
  if ($null -eq $Match) { return "" }

  foreach ($prop in @("group", "groupName")) {
    if ($Match.PSObject.Properties.Name -contains $prop) {
      $direct = NormalizeGroupName ([string]$Match.$prop)
      if ($direct) { return $direct }
    }
  }

  foreach ($prop in @("homeRank", "awayRank")) {
    if ($Match.PSObject.Properties.Name -contains $prop) {
      $rankText = [string]$Match.$prop
      if ($rankText -match "([A-Z]组)") {
        return $Matches[1]
      }
    }
  }

  return ""
}

function InferGroupSeed($Match, [string]$TeamName) {
  if ($null -eq $Match -or [string]::IsNullOrWhiteSpace($TeamName)) { return 99 }
  $teamKey = TeamKey $TeamName
  foreach ($side in @("home", "away")) {
    $nameProp = $side
    $rankProp = $side + "Rank"
    if (($Match.PSObject.Properties.Name -contains $nameProp) -and ($Match.PSObject.Properties.Name -contains $rankProp)) {
      if ((TeamKey ([string]$Match.$nameProp)) -eq $teamKey) {
        $rankText = [string]$Match.$rankProp
        if ($rankText -match "\[(?:[A-Z]组)(\d+)\]") {
          return [int]$Matches[1]
        }
      }
    }
  }
  return 99
}

function TeamKey([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
  $trimmed = $Value.Trim()
  if ($script:teamAliasMap.ContainsKey($trimmed)) {
    return [string]$script:teamAliasMap[$trimmed]
  }
  return $trimmed
}

function GetHadProbabilities($Match) {
  if ($Match.odds -and $Match.odds.had) {
    $homeOdd = ToDouble $Match.odds.had.home
    $drawOdd = ToDouble $Match.odds.had.draw
    $awayOdd = ToDouble $Match.odds.had.away
    if ($homeOdd -gt 0 -and $drawOdd -gt 0 -and $awayOdd -gt 0) {
      $rawHome = 1 / $homeOdd
      $rawDraw = 1 / $drawOdd
      $rawAway = 1 / $awayOdd
      $sum = $rawHome + $rawDraw + $rawAway
      return [pscustomobject]@{
        home = $rawHome / $sum
        draw = $rawDraw / $sum
        away = $rawAway / $sum
      }
    }
  }

  if ($Match.odds -and $Match.odds.hhad) {
    $homeHhadOdd = ToDouble $Match.odds.hhad.home
    $awayHhadOdd = ToDouble $Match.odds.hhad.away
    if ($homeHhadOdd -gt 0 -and $awayHhadOdd -gt 0) {
      if ($homeHhadOdd -le $awayHhadOdd) {
        return [pscustomobject]@{ home = 0.60; draw = 0.23; away = 0.17 }
      }
      return [pscustomobject]@{ home = 0.21; draw = 0.24; away = 0.55 }
    }
  }

  return [pscustomobject]@{ home = 0.45; draw = 0.27; away = 0.28 }
}

function GetScoreKeyFromText([string]$Score) {
  if ([string]::IsNullOrWhiteSpace($Score)) { return "" }
  $parts = $Score.Split(":")
  if ($parts.Count -ne 2) { return "" }
  return ("{0:00}{1:00}" -f ([int]$parts[0]), ([int]$parts[1]))
}

function GetScoreOdd($Match, [string]$Score) {
  if (-not $Match.odds -or -not $Match.odds.crs) { return 0 }
  $key = GetScoreKeyFromText $Score
  if (-not $key) { return 0 }
  if ($Match.odds.crs.PSObject.Properties.Name -contains $key) {
    return ToDouble $Match.odds.crs.$key
  }
  return 0
}

function Factorial([int]$N) {
  if ($N -le 1) { return 1.0 }
  $value = 1.0
  for ($i = 2; $i -le $N; $i++) {
    $value *= $i
  }
  return $value
}

function PoissonProb([double]$Lambda, [int]$Goals) {
  if ($Lambda -le 0) { return 0 }
  return ([math]::Exp(-$Lambda) * [math]::Pow($Lambda, $Goals)) / (Factorial $Goals)
}

function GetExpectedGoals($Match, $Lean, $HadProbs) {
  $total = ToDouble $Match.prediction.totalGoals 2.4
  if ($total -lt 1.2) { $total = 2.4 }
  $homeForm = GetRecentTeamSummary ([string]$Match.home)
  $awayForm = GetRecentTeamSummary ([string]$Match.away)
  $weather = GetKickoffWeatherScore $Match
  $dataCompleteness = GetDataCompletenessScore $Match
  $favoriteProb = [math]::Max($HadProbs.home, $HadProbs.away)
  $balancedMatch = [math]::Abs($HadProbs.home - $HadProbs.away) -le 0.12
  $drawBalanceSignal = $HadProbs.draw -ge 0.28 -and $balancedMatch
  $homeRank = if ($Match.external -and $Match.external.fifaRanking -and $Match.external.fifaRanking.home) { ToDouble $Match.external.fifaRanking.home.rank 0 } else { 0 }
  $awayRank = if ($Match.external -and $Match.external.fifaRanking -and $Match.external.fifaRanking.away) { ToDouble $Match.external.fifaRanking.away.rank 0 } else { 0 }
  $rankGap = if ($homeRank -gt 0 -and $awayRank -gt 0) { [math]::Abs($homeRank - $awayRank) } else { 0 }

  $share = 0.5
  $sided = $HadProbs.home + $HadProbs.away
  if ($sided -gt 0) {
    $share = $HadProbs.home / $sided
  }

  if ($Lean.code -eq "home" -and $Lean.strong) {
    $share = [math]::Max($share, 0.66)
  }
  elseif ($Lean.code -eq "away" -and $Lean.strong) {
    $share = [math]::Min($share, 0.34)
  }
  elseif ($Lean.code -eq "home") {
    $share = [math]::Max($share, 0.58)
  }
  elseif ($Lean.code -eq "away") {
    $share = [math]::Min($share, 0.42)
  }

  $goal2Odd = 0
  $goal3Odd = 0
  $goal4Odd = 0
  if ($Match.odds -and $Match.odds.ttg) {
    $goal2Odd = ToDouble $Match.odds.ttg.s2 0
    $goal3Odd = ToDouble $Match.odds.ttg.s3 0
    $goal4Odd = ToDouble $Match.odds.ttg.s4 0
  }

  $zeroZeroOdd = GetScoreOdd $Match "0:0"
  $oneOneOdd = GetScoreOdd $Match "1:1"
  $tightDrawSignal = $zeroZeroOdd -gt 0 -and $zeroZeroOdd -le 12 -and $oneOneOdd -gt 0 -and $oneOneOdd -le 8.5
  if ($tightDrawSignal) {
    $total -= 0.15
    $share = 0.5 + (($share - 0.5) * 0.65)
  }
  if ($drawBalanceSignal) {
    $total -= 0.18
    $share = 0.5 + (($share - 0.5) * 0.45)
  }

  $recentOpen = (($homeForm.gf + $homeForm.ga + $awayForm.gf + $awayForm.ga) / [math]::Max(2, ($homeForm.played + $awayForm.played)))
  if ($recentOpen -ge 1.35) {
    $total += 0.18
  }
  elseif ($recentOpen -le 0.75) {
    $total -= 0.12
  }

  $total += (($weather.score - 6.0) * 0.08)

  if ($Lean.strong -and $goal3Odd -gt 0 -and $goal4Odd -gt 0 -and $goal4Odd -le ($goal3Odd + 1.4)) {
    $total += 0.35
  }
  elseif ($Lean.strong -and $goal2Odd -gt 0 -and $goal3Odd -gt 0 -and [math]::Abs($goal2Odd - $goal3Odd) -le 0.25) {
    $total += 0.15
  }
  elseif (-not $Lean.strong -and $goal2Odd -gt 0 -and $goal3Odd -gt 0 -and [math]::Abs($goal2Odd - $goal3Odd) -le 0.18 -and ($tightDrawSignal -or $drawBalanceSignal)) {
    $total -= 0.10
  }

  if ($Lean.code -eq "away" -and $Lean.strong -and $goal3Odd -gt 0 -and $goal3Odd -le 3.7) {
    $total += 0.15
    $share = [math]::Min($share, 0.38)
  }
  if ($favoriteProb -ge 0.62 -and $HadProbs.draw -le 0.23 -and ($Lean.code -eq "home" -or $Lean.code -eq "away")) {
    $total += 0.10
  }
  if ($rankGap -ge 25 -and $Lean.code -ne "draw") {
    if ($goal3Odd -gt 0 -and $goal4Odd -gt 0 -and $goal4Odd -le ($goal3Odd + 1.8)) {
      $total += 0.22
    }
    $share = if ($Lean.code -eq "home") { [math]::Max($share, 0.68) } else { [math]::Min($share, 0.32) }
  }
  if ($Lean.code -eq "draw" -and $balancedMatch) {
    $total -= 0.18
    $share = 0.5 + (($share - 0.5) * 0.35)
  }

  if ($Match.PSObject.Properties.Name -contains "external" -and $Match.external -and $Match.external.injuries -and $Match.external.injuries.source -eq "api-sports") {
    $homeInjuryCount = @($Match.external.injuries.home).Count
    $awayInjuryCount = @($Match.external.injuries.away).Count
    $total -= (($homeInjuryCount + $awayInjuryCount) * 0.04)
    if ($homeInjuryCount -ge 2) {
      $share -= 0.03
    }
    if ($awayInjuryCount -ge 2) {
      $share += 0.03
    }
  }

  if ($dataCompleteness.score -le 5.4) {
    $total -= 0.10
    $share = 0.5 + (($share - 0.5) * 0.72)
  }
  elseif ($dataCompleteness.score -ge 7.4 -and $Lean.strong -and $favoriteProb -ge 0.60) {
    $total += 0.06
  }

  $total = Clamp $total 1.4 4.8
  $share = Clamp $share 0.28 0.72
  $homeLambda = [math]::Max(0.15, $total * $share)
  $awayLambda = [math]::Max(0.15, $total - $homeLambda)
  return [pscustomobject]@{ home = $homeLambda; away = $awayLambda; total = $total }
}

function GetHistoricalMatches() {
  $items = New-Object System.Collections.Generic.List[object]
  Get-ChildItem -Path (Join-Path $root "data") -Filter "*.json" | Sort-Object Name | ForEach-Object {
    $content = Get-Content -Raw -Encoding UTF8 $_.FullName | ConvertFrom-Json
    foreach ($match in @($content.matches)) {
      $group = ""
      $group = InferGroupName $match

      $items.Add([pscustomobject]@{
        id = [string]$match.id
        date = [string]$content.date
        kickoff = [string]$match.kickoff
        group = $group
        home = [string]$match.home
        homeKey = TeamKey ([string]$match.home)
        away = [string]$match.away
        awayKey = TeamKey ([string]$match.away)
        result = $match.result
      })
    }
  }
  return $items
}

function GetRecentTeamSummary([string]$Team) {
  $teamKey = TeamKey $Team
  $matches = @($script:historicalMatches | Where-Object { $_.result -and ($_.homeKey -eq $teamKey -or $_.awayKey -eq $teamKey) } | Sort-Object kickoff -Descending | Select-Object -First 10)
  $played = $matches.Count
  if ($played -eq 0) {
    return [pscustomobject]@{ played = 0; wins = 0; draws = 0; losses = 0; gf = 0; ga = 0; ppg = 1.0; score = 5.0 }
  }

  $wins = 0; $draws = 0; $losses = 0; $gf = 0; $ga = 0
  foreach ($m in $matches) {
    $homeGoals = [int]$m.result.homeGoals
    $awayGoals = [int]$m.result.awayGoals
    if ($m.homeKey -eq $teamKey) {
      $gf += $homeGoals
      $ga += $awayGoals
      if ($homeGoals -gt $awayGoals) { $wins += 1 } elseif ($homeGoals -eq $awayGoals) { $draws += 1 } else { $losses += 1 }
    }
    else {
      $gf += $awayGoals
      $ga += $homeGoals
      if ($awayGoals -gt $homeGoals) { $wins += 1 } elseif ($awayGoals -eq $homeGoals) { $draws += 1 } else { $losses += 1 }
    }
  }

  $ppg = (($wins * 3) + $draws) / $played
  $score = Clamp (5 + (($ppg - 1.2) * 2.1) + ((($gf - $ga) / $played) * 0.9)) 2 9.5
  return [pscustomobject]@{ played = $played; wins = $wins; draws = $draws; losses = $losses; gf = $gf; ga = $ga; ppg = $ppg; score = $score }
}

function GetKickoffWeatherScore($Match) {
  $raw = MatchKickoffBeijingFull $Match
  $score = 6.2
  $note = "按开球时段估算为中性天气节奏。"
  try {
    $dt = [datetime]$raw
    if ($dt.Hour -ge 11 -and $dt.Hour -le 16) {
      $score = 4.8
      $note = "北京时间午场偏热，节奏和射门质量通常会被压低。"
    }
    elseif ($dt.Hour -ge 0 -and $dt.Hour -le 5) {
      $score = 5.9
      $note = "北京时间凌晨场更容易先谨慎，前段节奏偏收。"
    }
    elseif ($dt.Hour -ge 6 -and $dt.Hour -le 10) {
      $score = 6.4
      $note = "北京时间早场更接近正常比赛节奏，但仍保留慢热风险。"
    }
    else {
      $score = 6.8
      $note = "北京时间晚场体能与比赛强度更平衡，利于主线兑现。"
    }
  }
  catch {}

  $venueText = ""
  if ($Match.PSObject.Properties.Name -contains "venue" -and $Match.venue) {
    $venueText = [string]$Match.venue
  }
  if ($venueText -match "午场|高温|炎热") {
    $score -= 0.8
    $note = "赛地描述偏午场/高温，进一步压低比赛节奏。"
  }
  elseif ($venueText -match "清晨|湿热|大风|降雨") {
    $score -= 0.5
    $note = "赛地描述提示清晨或天气扰动，稳定性下降。"
  }
  elseif ($venueText -match "深夜|夜场") {
    $score += 0.2
  }

  return [pscustomobject]@{
    score = [math]::Round((Clamp $score 3.8 8.4), 2)
    note = $note
  }
}

function GetHistoryStyleSignal($HomeForm, $AwayForm) {
  $homePlayed = [math]::Max(1, [int]$HomeForm.played)
  $awayPlayed = [math]::Max(1, [int]$AwayForm.played)
  $homeOpen = ($HomeForm.gf + $HomeForm.ga) / $homePlayed
  $awayOpen = ($AwayForm.gf + $AwayForm.ga) / $awayPlayed
  $drawBias = (($HomeForm.draws + $AwayForm.draws) / [math]::Max(1, ($homePlayed + $awayPlayed)))
  $styleScore = 5.4 + (($homeOpen + $awayOpen - 4.2) * 0.65) - ($drawBias * 1.2)
  return [pscustomobject]@{
    score = [math]::Round((Clamp $styleScore 3.8 8.8), 2)
    openness = [math]::Round((($homeOpen + $awayOpen) / 2), 2)
    drawBias = [math]::Round($drawBias, 2)
  }
}

function GetDataCompletenessScore($Match) {
  $score = 4.6
  $notes = New-Object System.Collections.Generic.List[string]

  if ($Match.odds) {
    if ($Match.odds.had -and $Match.odds.had.home -and $Match.odds.had.draw -and $Match.odds.had.away) {
      $score += 1.2
      $notes.Add("胜平负完整")
    }
    if ($Match.odds.ttg -and $Match.odds.ttg.s2 -and $Match.odds.ttg.s3) {
      $score += 0.7
      $notes.Add("总进球完整")
    }
    if ($Match.odds.hhad -and $Match.odds.hhad.home -and $Match.odds.hhad.away) {
      $score += 0.4
      $notes.Add("让球结构可用")
    }
    if ($Match.odds.hafu -and ($Match.odds.hafu.aa -or $Match.odds.hafu.hh -or $Match.odds.hafu.ha)) {
      $score += 0.25
      $notes.Add("半全场可用")
    }
    if ($Match.odds.crs -and $Match.odds.crs.updatedAt) {
      $score += 0.25
      $notes.Add("波胆快照可用")
    }
  }

  if ($Match.external) {
    if ($Match.external.teamMeta -and $Match.external.teamMeta.home -and $Match.external.teamMeta.home.status -eq "ok") {
      $score += 0.35
    }
    if ($Match.external.teamMeta -and $Match.external.teamMeta.away -and $Match.external.teamMeta.away.status -eq "ok") {
      $score += 0.35
    }
    if ($Match.external.fifaRanking -and $Match.external.fifaRanking.home -and $Match.external.fifaRanking.home.rank) {
      $score += 0.35
    }
    if ($Match.external.fifaRanking -and $Match.external.fifaRanking.away -and $Match.external.fifaRanking.away.rank) {
      $score += 0.35
    }
    if ($Match.external.injuries -and $Match.external.injuries.status -eq "ok") {
      $score += 0.45
      $notes.Add("伤停源可用")
    }
    if ($Match.external.h2h -and $Match.external.h2h.status -eq "ok" -and @($Match.external.h2h.matches).Count -gt 0) {
      $score += 0.55
      $notes.Add("交锋样本可用")
    }
  }

  $groupGuess = InferGroupName $Match
  if ($groupGuess) {
    $score += 0.3
  }

  return [pscustomobject]@{
    score = [math]::Round((Clamp $score 3.8 8.9), 2)
    summary = if ($notes.Count -gt 0) { $notes -join " / " } else { "核心数据待补" }
  }
}

function BuildContextSignals($Match, $Lean, $StandingsBundle, $HomeForm, $AwayForm) {
  $homeRow = $StandingsBundle.teamLookup[(TeamKey ([string]$Match.home))]
  $awayRow = $StandingsBundle.teamLookup[(TeamKey ([string]$Match.away))]
  $weather = GetKickoffWeatherScore $Match
  $history = GetHistoryStyleSignal $HomeForm $AwayForm
  $dataCompleteness = GetDataCompletenessScore $Match

  $homeNeed = 5.2
  $awayNeed = 5.2
  $drawAccept = 4.8
  $rotationRisk = 3.8
  if ($homeRow -and $awayRow) {
    $homeNeed = Clamp (4.2 + ($homeRow.remaining * 0.8) + ((2 - [math]::Min($homeRow.points, 2)) * 1.1)) 4 9.6
    $awayNeed = Clamp (4.2 + ($awayRow.remaining * 0.8) + ((2 - [math]::Min($awayRow.points, 2)) * 1.1)) 4 9.6
    $drawAccept = Clamp (4.5 + (([math]::Abs($homeRow.points - $awayRow.points) - 1) * -0.4) + (([math]::Min($homeRow.points, $awayRow.points) - 1) * 0.6)) 3.6 8.8
    if (($homeRow.rank -le 2 -and $homeRow.points -ge 4 -and $homeRow.remaining -le 1) -or ($awayRow.rank -le 2 -and $awayRow.points -ge 4 -and $awayRow.remaining -le 1)) {
      $rotationRisk = 7.2
    }
  }

  $injuryCountHome = 0
  $injuryCountAway = 0
  if ($Match.PSObject.Properties.Name -contains "external" -and $Match.external -and $Match.external.injuries -and $Match.external.injuries.source -eq "api-sports") {
    $injuryCountHome = @($Match.external.injuries.home).Count
    $injuryCountAway = @($Match.external.injuries.away).Count
  }
  $injuryRisk = Clamp (5.0 - (($injuryCountHome + $injuryCountAway) * 0.35)) 3.5 8.2
  $needSide = if ($Lean.code -eq "away") { $awayNeed } elseif ($Lean.code -eq "home") { $homeNeed } else { ($homeNeed + $awayNeed) / 2 }

  return [pscustomobject]@{
    weather = $weather
    history = $history
    homeNeed = [math]::Round($homeNeed, 2)
    awayNeed = [math]::Round($awayNeed, 2)
    needSide = [math]::Round($needSide, 2)
    drawAccept = [math]::Round($drawAccept, 2)
    rotationRisk = [math]::Round($rotationRisk, 2)
    injuryRisk = [math]::Round($injuryRisk, 2)
    dataCompleteness = $dataCompleteness
  }
}

function BuildStandingsBundle($Matches, $Snapshot = $null) {
  $groups = @{}
  $allMatches = New-Object System.Collections.Generic.List[object]
  $seedLookup = @{}
  $snapshotGroups = @{}

  foreach ($item in @($script:historicalMatches)) {
    $allMatches.Add($item)
  }

  foreach ($match in @($Matches)) {
    $matchGroup = InferGroupName $match
    foreach ($side in @("home", "away")) {
      $teamName = [string]$match.$side
      $teamKey = TeamKey $teamName
      if (-not $teamKey) { continue }
      $seed = InferGroupSeed $match $teamName
      if (-not $seedLookup.ContainsKey($teamKey) -or $seed -lt [int]$seedLookup[$teamKey].seed) {
        $seedLookup[$teamKey] = [pscustomobject]@{
          group = $matchGroup
          seed = $seed
        }
      }
    }

    $allMatches.Add([pscustomobject]@{
      id = [string]$match.id
      date = [string]$payload.date
      kickoff = MatchKickoffLocal $match
      group = $matchGroup
      home = [string]$match.home
      homeKey = TeamKey ([string]$match.home)
      away = [string]$match.away
      awayKey = TeamKey ([string]$match.away)
      result = $match.result
    })
  }

  foreach ($snapshotGroup in @($Snapshot)) {
    $groupName = NormalizeGroupName ([string]$snapshotGroup.group)
    if (-not $groupName) { continue }
    $snapshotGroups[$groupName] = $true
    if (-not $groups.ContainsKey($groupName)) {
      $groups[$groupName] = [ordered]@{}
    }

    foreach ($snapshotRow in @($snapshotGroup.rows)) {
      $teamName = DisplayTeamName ([string]$snapshotRow.team)
      $teamKey = TeamKey $teamName
      if (-not $teamKey) { continue }
      $seed = if ($seedLookup.ContainsKey($teamKey)) { [int]$seedLookup[$teamKey].seed } else { 99 }
      $groups[$groupName][$teamKey] = [ordered]@{
        team = $teamName
        teamKey = $teamKey
        seed = $seed
        played = [int](ToDouble $snapshotRow.played 0)
        wins = [int](ToDouble $snapshotRow.wins 0)
        draws = [int](ToDouble $snapshotRow.draws 0)
        losses = [int](ToDouble $snapshotRow.losses 0)
        gf = [int](ToDouble $snapshotRow.gf 0)
        ga = [int](ToDouble $snapshotRow.ga 0)
        gd = [int](ToDouble $snapshotRow.gd 0)
        points = [int](ToDouble $snapshotRow.points 0)
      }
    }
  }

  foreach ($item in $allMatches) {
    $group = NormalizeGroupName ([string]$item.group)
    if (-not $group) { continue }
    if (-not $groups.ContainsKey($group)) {
      $groups[$group] = [ordered]@{}
    }
    foreach ($team in @([string]$item.home, [string]$item.away)) {
      $teamKey = TeamKey $team
      if (-not $groups[$group].Contains($teamKey)) {
        $groups[$group][$teamKey] = [ordered]@{
          team = (DisplayTeamName $team)
          teamKey = $teamKey
          seed = if ($seedLookup.ContainsKey($teamKey)) { [int]$seedLookup[$teamKey].seed } else { 99 }
          played = 0
          wins = 0
          draws = 0
          losses = 0
          gf = 0
          ga = 0
          gd = 0
          points = 0
        }
      }
    }
  }

  foreach ($item in ($allMatches | Where-Object { $_.result -and $null -ne $_.result.homeGoals -and $null -ne $_.result.awayGoals })) {
    $group = NormalizeGroupName ([string]$item.group)
    if (-not $group -or -not $groups.ContainsKey($group)) { continue }
    if ($snapshotGroups.ContainsKey($group)) { continue }
    if (-not $groups[$group].Contains($item.homeKey) -or -not $groups[$group].Contains($item.awayKey)) { continue }

    $homeRowState = $groups[$group][$item.homeKey]
    $awayRowState = $groups[$group][$item.awayKey]
    $hg = [int](ToDouble $item.result.homeGoals 0)
    $ag = [int](ToDouble $item.result.awayGoals 0)

    $homeRowState.played += 1
    $awayRowState.played += 1
    $homeRowState.gf += $hg
    $homeRowState.ga += $ag
    $awayRowState.gf += $ag
    $awayRowState.ga += $hg

    if ($hg -gt $ag) {
      $homeRowState.wins += 1
      $awayRowState.losses += 1
      $homeRowState.points += 3
    }
    elseif ($hg -lt $ag) {
      $awayRowState.wins += 1
      $homeRowState.losses += 1
      $awayRowState.points += 3
    }
    else {
      $homeRowState.draws += 1
      $awayRowState.draws += 1
      $homeRowState.points += 1
      $awayRowState.points += 1
    }
  }

  $groupRows = New-Object System.Collections.Generic.List[object]
  $teamLookup = @{}
  $impactLookup = @{}

  foreach ($groupName in ($groups.Keys | Sort-Object)) {
    $rows = @($groups[$groupName].Values | ForEach-Object {
      $_.gd = $_.gf - $_.ga
      [pscustomobject]$_
    } | Sort-Object @{Expression='points';Descending=$true}, @{Expression='gd';Descending=$true}, @{Expression='gf';Descending=$true}, @{Expression='seed';Descending=$false}, team)

    for ($idx = 0; $idx -lt $rows.Count; $idx++) {
      $row = $rows[$idx]
      $played = [int](ToDouble $row.played 0)
      $points = [int](ToDouble $row.points 0)
      $remaining = [math]::Max(0, 3 - $played)
      $status = "🔵 理论可能"
      if ($remaining -eq 0 -and $idx -lt 2) {
        $status = "🟢 已晋级"
      }
      elseif ($remaining -eq 0 -and $idx -eq 2 -and $points -ge 3) {
        $status = "🟡 第三名待比较"
      }
      elseif ($remaining -eq 0) {
        $status = "⚪ 已淘汰"
      }
      elseif ($played -eq 0 -and $points -eq 0) {
        $status = "⚪ 首轮未开赛"
      }
      elseif ($idx -lt 2 -and $played -ge 2 -and $points -ge 4) {
        $status = "🟡 出线主动权"
      }
      elseif ($remaining -le 1 -and $points -le 1) {
        $status = "🟠 生死战"
      }

      $pointsBonus = [double]($points * 20)
      $rankBonus = [double]((2 - [math]::Min([int]$idx, 2)) * 12)
      $remainingBonus = [double]((3 - [int]$remaining) * 6)
      $qualScore = Clamp ($pointsBonus + $rankBonus + $remainingBonus) 5 98
      $row | Add-Member -NotePropertyName remaining -NotePropertyValue $remaining -Force
      $row | Add-Member -NotePropertyName status -NotePropertyValue $status -Force
      $row | Add-Member -NotePropertyName qualScore -NotePropertyValue ([math]::Round($qualScore)) -Force
      $row | Add-Member -NotePropertyName rank -NotePropertyValue ($idx + 1) -Force
      $row | Add-Member -NotePropertyName group -NotePropertyValue $groupName -Force
      $teamLookup[$row.teamKey] = $row
    }

    $groupRows.Add([pscustomobject]@{
      group = $groupName
      rows = $rows
    })
  }

  foreach ($match in @($Matches)) {
    $group = InferGroupName $match
    if (-not $group -or -not ($groups.ContainsKey($group))) { continue }
    $homeRow = $teamLookup[(TeamKey ([string]$match.home))]
    $awayRow = $teamLookup[(TeamKey ([string]$match.away))]
    if (-not $homeRow -or -not $awayRow) { continue }

    $homePoints = [int](ToDouble $homeRow.points 0)
    $awayPoints = [int](ToDouble $awayRow.points 0)
    $remainingHome = [math]::Max(0, 3 - [int](ToDouble $homeRow.played 0))
    $remainingAway = [math]::Max(0, 3 - [int](ToDouble $awayRow.played 0))
    $homeWin = [math]::Round((Clamp ((($homePoints + 3) * 18) + (($remainingHome - 1) * 4)) 8 96))
    $draw = [math]::Round((Clamp ((($homePoints + $awayPoints + 2) * 8)) 6 78))
    $awayWin = [math]::Round((Clamp ((($awayPoints + 3) * 18) + (($remainingAway - 1) * 4)) 8 96))
    $impactLookup[[string]$match.id] = "$($match.home)胜→出线主动权估值 $homeWin%；平→局势估值 $draw%；$($match.away)胜→出线主动权估值 $awayWin%。"
  }

  return [pscustomobject]@{
    groups = $groupRows
    teamLookup = $teamLookup
    impactLookup = $impactLookup
  }
}

function BuildScoreCard($Match, $Lean, $StandingsBundle) {
  $probs = GetHadProbabilities $Match
  $homeForm = GetRecentTeamSummary ([string]$Match.home)
  $awayForm = GetRecentTeamSummary ([string]$Match.away)
  $teamRow = if ($Lean.code -eq "away") { $StandingsBundle.teamLookup[(TeamKey ([string]$Match.away))] } elseif ($Lean.code -eq "home") { $StandingsBundle.teamLookup[(TeamKey ([string]$Match.home))] } else { $StandingsBundle.teamLookup[(TeamKey ([string]$Match.home))] }
  $external = if ($Match.PSObject.Properties.Name -contains "external") { $Match.external } else { $null }
  $context = BuildContextSignals $Match $Lean $StandingsBundle $homeForm $awayForm

  $leanProb = if ($Lean.code -eq "away") { $probs.away } elseif ($Lean.code -eq "draw") { $probs.draw } else { $probs.home }
  $marketGap = if ($Lean.code -eq "draw") { 1 - [math]::Abs($probs.home - $probs.away) } else { [math]::Abs($probs.home - $probs.away) }
  $drawPressureSignal = $probs.draw -ge 0.28 -and [math]::Abs($probs.home - $probs.away) -le 0.12
  $formDelta = $homeForm.score - $awayForm.score
  if ($Lean.code -eq "away") { $formDelta *= -1 }

  $basic = Clamp (4.8 + ($formDelta * 0.55) + (($leanProb - 0.43) * 7.2)) 2 9.4
  $lineup = Clamp (5 + (($leanProb - 0.40) * 10)) 3 9.0
  $elo = Clamp (($leanProb / 0.70) * 10) 2 9.6
  $odds = Clamp (4.2 + ($marketGap * 6.5) + (($leanProb - 0.40) * 4.5)) 2 9.7
  $trend = 5.2
  if ($Match.odds -and $Match.odds.hhad) {
    $hHome = ToDouble $Match.odds.hhad.home
    $hAway = ToDouble $Match.odds.hhad.away
    if ($hHome -gt 0 -and $hAway -gt 0) {
      $trend = if (($Lean.code -eq "home" -and $hHome -lt $hAway) -or ($Lean.code -eq "away" -and $hAway -lt $hHome)) { 7.1 } else { 4.8 }
    }
  }
  if ($drawPressureSignal -and $Lean.code -ne "draw") {
    $trend = [math]::Min($trend, 4.7)
  }
  $h2h = 5.0
  $motivation = $context.needSide
  $pressure = Clamp (4.2 + ((8.6 - $context.drawAccept) * 0.55)) 4 9.6
  $weather = $context.weather.score
  $historyStyle = $context.history.score
  $injuryRisk = $context.injuryRisk
  $rotationRisk = 10 - $context.rotationRisk
  $dataCompleteness = $context.dataCompleteness.score

  if ($external -and $external.injuries -and $external.injuries.source -eq "api-sports") {
    $injuryCount = if ($Lean.code -eq "away") { @($external.injuries.away).Count } else { @($external.injuries.home).Count }
    $lineup = Clamp ($lineup - ($injuryCount * 0.45)) 2.6 9.0
  }

  if ($external -and $external.h2h -and $external.h2h.status -eq "ok") {
    $h2hLeanWins = 0
    $homeAlias = if ($Match.PSObject.Properties.Name -contains "homeEn" -and $Match.homeEn) { [string]$Match.homeEn } else { [string]$Match.home }
    $awayAlias = if ($Match.PSObject.Properties.Name -contains "awayEn" -and $Match.awayEn) { [string]$Match.awayEn } else { [string]$Match.away }
    foreach ($item in @($external.h2h.matches)) {
      if (-not $item.score) { continue }
      $parts = [string]$item.score -split ":"
      if ($parts.Count -ne 2) { continue }
      $hg = [int](ToDouble $parts[0] 0)
      $ag = [int](ToDouble $parts[1] 0)
      $homeName = [string]$item.home
      $awayName = [string]$item.away
      if ($Lean.code -eq "home") {
        if ($homeName -eq $homeAlias -and $hg -gt $ag) { $h2hLeanWins += 1 }
        elseif ($awayName -eq $homeAlias -and $ag -gt $hg) { $h2hLeanWins += 1 }
      }
      elseif ($Lean.code -eq "away") {
        if ($homeName -eq $awayAlias -and $hg -gt $ag) { $h2hLeanWins += 1 }
        elseif ($awayName -eq $awayAlias -and $ag -gt $hg) { $h2hLeanWins += 1 }
      }
    }
    if (@($external.h2h.matches).Count -gt 0) {
      $h2h = Clamp (4.6 + ($h2hLeanWins * 0.9)) 3.5 8.8
    }
  }

  if ($teamRow) {
    $motivation = Clamp (4.5 + ($teamRow.remaining * 0.8) + ((2 - [math]::Min($teamRow.points, 2)) * 0.9)) 4 9.5
    $pressure = Clamp (4.0 + ((3 - [math]::Min($teamRow.remaining, 3)) * 0.7) + ((2 - [math]::Min($teamRow.points, 2)) * 1.2) - (($context.drawAccept - 5) * 0.25)) 4 9.8
  }
  if ($drawPressureSignal -and $Lean.code -ne "draw") {
    $basic = [math]::Max(2.0, $basic - 0.35)
    $odds = [math]::Max(2.0, $odds - 0.30)
  }
  if ($dataCompleteness -le 5.4) {
    $lineup = [math]::Max(2.4, $lineup - 0.45)
    $trend = [math]::Max(3.8, $trend - 0.35)
    $h2h = [math]::Max(3.8, $h2h - 0.25)
  }
  if ($context.rotationRisk -ge 6.8 -and $Lean.strong) {
    $lineup = [math]::Max(2.5, $lineup - 0.30)
    $rotationRisk = [math]::Max(2.0, $rotationRisk - 0.60)
  }

  $weights = [ordered]@{
    basic = 0.13
    lineup = 0.11
    elo = 0.11
    odds = 0.12
    trend = 0.09
    h2h = 0.07
    motivation = 0.13
    pressure = 0.09
    weather = 0.04
    historyStyle = 0.05
    injuryRisk = 0.03
    rotationRisk = 0.03
    dataCompleteness = 0.10
  }

  $dims = [ordered]@{
    basic = [math]::Round($basic, 2)
    lineup = [math]::Round($lineup, 2)
    elo = [math]::Round($elo, 2)
    odds = [math]::Round($odds, 2)
    trend = [math]::Round($trend, 2)
    h2h = [math]::Round($h2h, 2)
    motivation = [math]::Round($motivation, 2)
    pressure = [math]::Round($pressure, 2)
    weather = [math]::Round($weather, 2)
    historyStyle = [math]::Round($historyStyle, 2)
    injuryRisk = [math]::Round($injuryRisk, 2)
    rotationRisk = [math]::Round($rotationRisk, 2)
    dataCompleteness = [math]::Round($dataCompleteness, 2)
  }

  $composite = 0.0
  foreach ($key in $dims.Keys) {
    $composite += $dims[$key] * $weights[$key]
  }
  $composite = [math]::Round($composite, 2)
  $stars = if ($composite -ge 8.5) { "★★★★★" } elseif ($composite -ge 7.0) { "★★★★☆" } elseif ($composite -ge 5.0) { "★★★☆☆" } else { "★★☆☆☆" }

  return [pscustomobject]@{
    lean = $Lean.code
    probabilities = $probs
    dimensions = $dims
    weights = $weights
    composite = $composite
    stars = $stars
    recent = [pscustomobject]@{
      home = $homeForm
      away = $awayForm
    }
    context = $context
  }
}

function BuildEvArtifact($Match, $Lean, $ScoreCard) {
  $probs = GetHadProbabilities $Match
  $lambdas = GetExpectedGoals $Match $Lean $probs
  $candidates = @()
  foreach ($s in @($Match.prediction.scores[0], $Match.prediction.scores[1], $Match.prediction.upset)) {
    if ($s -and ($candidates -notcontains $s)) { $candidates += $s }
  }

  if ($Match.odds -and $Match.odds.crs) {
    foreach ($prop in $Match.odds.crs.PSObject.Properties | Sort-Object Name | Select-Object -First 2) {
      if ($prop.Name.Length -eq 4) {
        $extra = ("{0}:{1}" -f [int]$prop.Name.Substring(0, 2), [int]$prop.Name.Substring(2, 2))
        if ($candidates -notcontains $extra) { $candidates += $extra }
      }
    }
  }

  $rows = New-Object System.Collections.Generic.List[object]
  foreach ($score in $candidates) {
    $parts = $score.Split(":")
    if ($parts.Count -ne 2) { continue }
    $hg = [int]$parts[0]
    $ag = [int]$parts[1]
    $prob = PoissonProb $lambdas.home $hg
    $prob *= PoissonProb $lambdas.away $ag
    $odd = GetScoreOdd $Match $score
    if ($odd -le 0) {
      $odd = 6 + (($hg + $ag) * 0.8)
    }
    $ev = ($odd * $prob) - 1
    $mark = if ($ev -gt 0) { "✅ 正EV推荐" } elseif ($score -eq $Match.prediction.upset) { "🔮 冷门低EV" } else { "⚪ 负EV观望" }
    $rows.Add([pscustomobject]@{
      score = $score
      odds = [math]::Round($odd, 2)
      probability = [math]::Round($prob, 4)
      ev = [math]::Round($ev, 2)
      mark = $mark
    })
  }

  $best = $rows | Sort-Object ev -Descending | Select-Object -First 1
  return [pscustomobject]@{
    lambdaHome = [math]::Round($lambdas.home, 2)
    lambdaAway = [math]::Round($lambdas.away, 2)
    totalLambda = [math]::Round($lambdas.total, 2)
    rows = $rows
    best = $best
  }
}

function BuildHalfFullArtifact($Match, $Lean, $EvArtifact) {
  $total = ToDouble $Match.prediction.totalGoals 2.5
  $homeLambda = ToDouble $EvArtifact.lambdaHome 1.2
  $awayLambda = ToDouble $EvArtifact.lambdaAway 1.0
  $firstHalfShare = 0.46
  $fhHome = $homeLambda * $firstHalfShare
  $fhAway = $awayLambda * $firstHalfShare

  $ht = "平"
  if ($fhHome - $fhAway -ge 0.22) {
    $ht = "胜"
  }
  elseif ($fhAway - $fhHome -ge 0.22) {
    $ht = "负"
  }

  $zeroZeroOdd = GetScoreOdd $Match "0:0"
  $oneOneOdd = GetScoreOdd $Match "1:1"
  $drawPressure = $zeroZeroOdd -gt 0 -and $zeroZeroOdd -le 12 -and $oneOneOdd -gt 0 -and $oneOneOdd -le 8.5
  if ($drawPressure -and [math]::Abs($fhHome - $fhAway) -lt 0.35) {
    $ht = "平"
  }

  $ft = switch ($Lean.code) {
    "home" { "胜" }
    "away" { "负" }
    default { "平" }
  }

  if ($drawPressure -and -not $Lean.strong -and $ft -ne "平") {
    $primary = "平/$ft"
  }
  else {
    $primary = "$ht/$ft"
  }

  if ($ft -eq "平" -and $ht -ne "平") {
    $secondary = "平/平"
  }
  elseif ($ft -eq "胜" -and $ht -eq "负") {
    $secondary = "平/胜"
  }
  elseif ($ft -eq "负" -and $ht -eq "胜") {
    $secondary = "平/负"
  }
  else {
    $secondary = "$ht/$ft"
  }

  if ($drawPressure -and $secondary -eq $primary) {
    $secondary = "平/平"
  }
  $goalBand = if ($total -le 2.2) {
    "1-2球"
  }
  elseif ($total -le 3.2) {
    "2-3球"
  }
  elseif ($total -le 4.2) {
    "3-4球"
  }
  else {
    "4-5球"
  }

  $pace = if ($fhHome + $fhAway -ge 1.3) {
    "上半场节奏偏快，早球概率较高。"
  }
  elseif ($fhHome + $fhAway -le 0.95) {
    "上半场更像试探局，后程决胜概率更高。"
  }
  else {
    "比赛大概率分段展开，上半场试探、下半场提速。"
  }

  return [pscustomobject]@{
    primary = $primary
    secondary = $secondary
    totalBand = $goalBand
    firstHalfLean = $ht
    fullTimeLean = $ft
    note = $pace
  }
}

function ScoreCardHtml($ScoreCard) {
  $labels = [ordered]@{
    basic = "基本面"
    lineup = "阵容伤停"
    elo = "Elo"
    odds = "赔率隐含"
    trend = "赔率趋势"
    h2h = "历史交锋"
    motivation = "小组动机"
    pressure = "出线压力"
    weather = "天气节奏"
    historyStyle = "历史风格"
    injuryRisk = "伤停风险"
    rotationRisk = "轮换稳定"
    dataCompleteness = "数据完整度"
  }
  $items = foreach ($key in $labels.Keys) {
    $val = [double]$ScoreCard.dimensions[$key]
    $pct = [math]::Round(($val / 10) * 100)
    "<div class=""metric""><span>$($labels[$key])</span><div class=""bar""><i style=""width:${pct}%""></i></div><strong>$('{0:N1}' -f $val)</strong></div>"
  }
  return "<div class=""scorecard""><div class=""scorehead""><span>综合信心分</span><strong>$('{0:N2}' -f $ScoreCard.composite)</strong><em>$($ScoreCard.stars)</em></div>" + ($items -join "") + "</div>"
}

function EvTableHtml($Artifact) {
  $rows = foreach ($r in $Artifact.rows) {
    $probPct = [math]::Round($r.probability * 100, 1)
    $evClass = if ($r.ev -gt 0) { "pos" } else { "neg" }
    "<tr><td>$($r.score)</td><td>$('{0:N2}' -f $r.odds)x</td><td>$probPct%</td><td class=""$evClass"">$('{0:N2}' -f $r.ev)</td><td>$($r.mark)</td></tr>"
  }
  return "<table class=""evTable""><thead><tr><th>比分</th><th>竞彩赔率</th><th>预测概率</th><th>EV</th><th>建议</th></tr></thead><tbody>" + ($rows -join "") + "</tbody></table>"
}

function HalfFullHtml($Artifact) {
  return "<div class=""hf""><div><span>半全场主推</span><strong>" + (HE $Artifact.primary) + "</strong></div><div><span>备选</span><strong>" + (HE $Artifact.secondary) + "</strong></div><div><span>总进球区间</span><strong>" + (HE $Artifact.totalBand) + "</strong></div><p>" + (HE $Artifact.note) + "</p></div>"
}

function StandingsSectionHtml($Bundle, $Matches) {
  $sections = New-Object System.Collections.Generic.List[string]
  $groupsToShow = @($Matches | ForEach-Object { InferGroupName $_ } | Where-Object { $_ } | Select-Object -Unique)
  foreach ($groupItem in @($Bundle.groups | Where-Object { $groupsToShow -contains $_.group })) {
    $highlightTeams = @($Matches | Where-Object { (InferGroupName $_) -eq $groupItem.group } | ForEach-Object { $_.home; $_.away })
    $rows = foreach ($row in $groupItem.rows) {
      $cls = if ($highlightTeams -contains $row.team) { " class=""hl""" } else { "" }
      "<tr$cls><td>$($row.team)</td><td>$($row.played)</td><td>$($row.wins)</td><td>$($row.draws)</td><td>$($row.losses)</td><td>$($row.gf)</td><td>$($row.ga)</td><td>$($row.gd)</td><td>$($row.points)</td><td>$($row.status)</td></tr>"
    }

    $impact = @($Matches | Where-Object { (InferGroupName $_) -eq $groupItem.group } | ForEach-Object {
      "<p><strong>$($_.home) vs $($_.away)</strong>：$(HE $Bundle.impactLookup[[string]$_.id])</p>"
    }) -join ""

    $sections.Add("<div class=""combo standingsCard""><h3>$($groupItem.group) 小组积分榜</h3><table><thead><tr><th>球队</th><th>已赛</th><th>胜</th><th>平</th><th>负</th><th>进</th><th>失</th><th>净胜</th><th>积分</th><th>出线状态</th></tr></thead><tbody>$rows</tbody></table><div class=""impact"">$impact</div></div>")
  }
  return ($sections -join "")
}

function KnockoutStatusText($Row) {
  $played = [int](ToDouble $Row.played 0)
  $rank = [int](ToDouble $Row.rank 99)
  $points = [int](ToDouble $Row.points 0)

  if ($played -lt 3) {
    if ($rank -le 2) { return "小组前二在手，末轮优先守住净胜球与不败线。" }
    if ($rank -eq 3) { return "第三名边缘位，末轮必须先拿分，再看净胜球。" }
    return "仍有理论机会，剧本必须从先抢开局和提高进球数开始。"
  }

  if ($rank -le 2) { return "直通淘汰赛。淘汰赛首轮应降低开放对攻权重，优先评估体能、轮换和一球胜负脚本。" }
  if ($rank -eq 3 -and $points -ge 4) { return "第三名高分待比较，晋级概率偏高；若入围淘汰赛，定位为防反和低比分拉扯型。" }
  if ($rank -eq 3 -and $points -eq 3) { return "第三名压线待比较，需要看其他组净胜球；淘汰赛剧本以逆风开局和必须提速为主。" }
  return "小组出局或基本出局，后续只保留复盘样本价值。"
}

function KnockoutScenarioSectionHtml($Bundle) {
  $rows = New-Object System.Collections.Generic.List[string]
  foreach ($groupItem in $Bundle.groups) {
    foreach ($row in $groupItem.rows) {
      $tag = if ([int](ToDouble $row.rank 99) -le 2) {
        "直通区"
      }
      elseif ([int](ToDouble $row.rank 99) -eq 3) {
        "第三名池"
      }
      else {
        "淘汰区"
      }
      $rows.Add("<tr><td>$($groupItem.group)</td><td>$($row.rank)</td><td>$($row.team)</td><td>$($row.points)</td><td>$($row.gd)</td><td>" + (HE $tag) + "</td><td>" + (HE (KnockoutStatusText $row)) + "</td></tr>")
    }
  }

  return "<section id=""knockoutScenario"" class=""section""><h2>淘汰赛阶段剧本分析</h2><div class=""recommend""><p class=""modelNote"">按当前小组积分榜覆盖全部球队，先区分直通区、第三名池和淘汰区，再给出淘汰赛首轮的节奏脚本。该模块随每日赛果自动重算。</p><div class=""tableWrap""><table><thead><tr><th>小组</th><th>排名</th><th>球队</th><th>积分</th><th>净胜</th><th>分层</th><th>淘汰赛剧本</th></tr></thead><tbody>" + ($rows -join "") + "</tbody></table></div></div></section>"
}

function RootStandingsCompactHtml($Bundle) {
  $sections = New-Object System.Collections.Generic.List[string]
  foreach ($groupItem in $Bundle.groups) {
    $rows = foreach ($row in $groupItem.rows) {
      $cls = if ($row.rank -eq 1) { " class=""top1""" } elseif ($row.rank -eq 2) { " class=""top2""" } else { "" }
      "<tr$cls><td>$($row.rank)</td><td>$($row.team)</td><td>$($row.points)</td></tr>"
    }
    $sections.Add("<div class=""miniGroupCard""><h3>$($groupItem.group)</h3><table><thead><tr><th>排</th><th>球队</th><th>分</th></tr></thead><tbody>$rows</tbody></table></div>")
  }
  return ($sections -join "")
}

function RootStandingsSectionHtml($Bundle) {
  $sections = New-Object System.Collections.Generic.List[string]
  foreach ($groupItem in $Bundle.groups) {
    $rows = foreach ($row in $groupItem.rows) {
      $cls = if ($row.rank -eq 1) { " class=""top1""" } elseif ($row.rank -eq 2) { " class=""top2""" } else { "" }
      "<tr$cls><td>$($row.rank)</td><td>$($row.team)</td><td>$($row.played)</td><td>$($row.gf)</td><td>$($row.ga)</td><td>$($row.gd)</td><td>$($row.points)</td><td>$($row.status)</td></tr>"
    }
    $sections.Add("<div class=""groupCard""><h3>$($groupItem.group) 组</h3><div class=""tableWrap""><table><thead><tr><th>排名</th><th>球队</th><th>已赛</th><th>进球</th><th>失球</th><th>净胜</th><th>积分</th><th>状态</th></tr></thead><tbody>$rows</tbody></table></div></div>")
  }
  return ($sections -join "")
}

function BeijingTomorrowSectionHtml([string]$DateText) {
  $rows = foreach ($match in @($script:homePageMatches | Sort-Object kickoff)) {
    "<tr><td>" + (HE (MatchKickoffBeijing $match)) + "</td><td>" + (HE ([string]$match.matchNumStr)) + "</td><td>" + (HE "$($match.home) vs $($match.away)") + "</td><td>" + (HE (InferGroupName $match)) + "</td></tr>"
  }

  if (-not $rows -or @($rows).Count -eq 0) {
    return "<div class=""fixtureCard""><h3>下一天北京时间赛程</h3><p>下一天赛程数据待补。</p></div>"
  }

  return "<div class=""fixtureCard""><h3>下一天北京时间赛程</h3><p>全部按北京时间展示，格式统一为 MM-DD HH:mm，首页可以直接扫一眼次日赛程。</p><div class=""tableWrap""><table><thead><tr><th>北京时间</th><th>场次</th><th>对阵</th><th>小组</th></tr></thead><tbody>" + ($rows -join "") + "</tbody></table></div></div>"
}

function BuildStandingsPageHtml($Bundle, [string]$LatestDate, [string]$DateText, [string]$UpdateTime) {
  $groupTables = RootStandingsSectionHtml $Bundle
  return @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 世界杯小组赛积分榜</title>
<style>
:root{--line:#1f4a43;--text:#e9fff8;--muted:#9bb8b0;--green:#33e28a;--blue:#7dd3fc}
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:"Microsoft YaHei",Arial,sans-serif;background:radial-gradient(circle at 18% 8%,rgba(51,226,138,.16),transparent 24%),linear-gradient(135deg,#020807,#071b2a);color:var(--text)}
main{max-width:1240px;margin:0 auto;padding:40px 18px 52px}.hero,.groupCard,.shortcut{border:1px solid var(--line);border-radius:8px;background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));box-shadow:0 16px 36px rgba(0,0,0,.22)}.hero{padding:22px;margin-bottom:22px}.heroTop{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.hero h1{margin:0 0 10px;font-size:clamp(28px,5vw,46px)}.hero p{margin:0;color:var(--muted);line-height:1.8}.heroMeta{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px}.heroMeta span{display:inline-flex;padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:#0b201d;color:#8fffd0}.heroLink,.shortcut a{display:inline-flex;align-items:center;justify-content:center;padding:10px 16px;border-radius:8px;background:#12362f;border:1px solid #2f8766;color:#a8ffd6;text-decoration:none;font-weight:800;white-space:nowrap}.shortcut{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 20px;margin-bottom:22px}.shortcut strong{display:block;font-size:20px;color:var(--blue)}.shortcut p{margin:6px 0 0;color:var(--muted)}.sectionTitle{font-size:24px;color:var(--blue);margin:0 0 16px}.groups{display:grid;gap:18px}.groupCard{padding:18px}.groupCard h3{margin:0 0 12px}.tableWrap{overflow-x:auto}table{width:100%;min-width:720px;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid var(--line);text-align:left}th{color:#8fffd0;background:#09211e}.top1 td{background:rgba(51,226,138,.12)}.top2 td{background:rgba(125,211,252,.10)}footer{margin-top:36px;color:#8ea8a1;font-size:13px}@media(max-width:720px){.heroTop,.shortcut{align-items:flex-start;flex-direction:column}}
</style>
</head>
<body>
<main>
<section class="hero">
<div class="heroTop">
<div>
<h1>2026 世界杯小组赛积分榜</h1>
<p>按组别汇总当前积分、进球、净胜球与出线状态，头名和次名已高亮，便于快速查看每组晋级区。</p>
<div class="heroMeta"><span>最新更新时间：$(HE $UpdateTime)</span><span>对应预测日：$(DateTitle $DateText)</span></div>
</div>
<a class="heroLink" href="./index.html">返回主页</a>
</div>
</section>
<section class="shortcut">
<div><strong>快捷入口</strong><p>直接跳转到最新的每日预测页，继续查看当日四场推荐与复盘修正。</p></div>
<a href="./$LatestDate/">进入 $LatestDate 页面</a>
</section>
<section>
<h2 class="sectionTitle">全部小组排名</h2>
<div class="groups">
$groupTables
</div>
</section>
<footer>仅供公开信息分析参考，不构成投注建议。</footer>
</main>
</body>
</html>
"@
}

function BuildRootIndexHtml($RootPath, $Bundle, [string]$LatestDate, [string]$DateText, [string]$UpdateTime) {
  $cards = New-Object System.Collections.Generic.List[string]
  $dirs = @(Get-ChildItem -LiteralPath $RootPath -Directory | Where-Object {
    $_.Name -match '^\d{8}$' -and (Test-Path (Join-Path $_.FullName 'index.html'))
  } | Sort-Object Name -Descending)

  foreach ($dir in $dirs) {
    $cards.Add("<a class=""card"" href=""./$($dir.Name)/""><div><div class=""date"">$($dir.Name)</div><div class=""meta"">&#39044;&#27979;&#30475;&#26495;&#19982;&#36187;&#21518;&#22797;&#30424;</div></div><div class=""go"">&#36827;&#20837; &#8594;</div></a>")
  }

  $compactStandings = RootStandingsCompactHtml $Bundle
  $tomorrowFixtures = BeijingTomorrowSectionHtml $DateText

  return @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 世界杯预测中心</title>
<style>
:root{--line:#1f4a43;--text:#e9fff8;--muted:#9bb8b0;--green:#33e28a;--blue:#7dd3fc}
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:"Microsoft YaHei",Arial,sans-serif;background:radial-gradient(circle at 20% 10%,rgba(51,226,138,.18),transparent 26%),linear-gradient(135deg,#020807,#071b2a);color:var(--text)}
main{max-width:1180px;margin:0 auto;padding:44px 18px}.hero{display:grid;gap:12px;margin-bottom:26px}.heroTop{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}h1{font-size:clamp(28px,5vw,48px);margin:0}p{color:var(--muted);line-height:1.8;margin:0}.heroMeta{display:flex;gap:12px;flex-wrap:wrap}.heroMeta span{display:inline-flex;padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:#0b201d;color:#8fffd0}.list{display:grid;gap:14px;margin-top:20px;margin-bottom:34px}.card,.groupCard,.fixtureCard,.miniGroupCard{border:1px solid var(--line);border-radius:8px;background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));box-shadow:0 16px 36px rgba(0,0,0,.22)}.card{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:18px;text-decoration:none;color:var(--text);transition:.22s}.card:hover,.heroLink:hover{transform:translateY(-3px);border-color:var(--green)}.date{font-size:24px;font-weight:800;color:var(--blue)}.meta{color:var(--muted);margin-top:6px}.go{color:var(--green);font-weight:800;white-space:nowrap}.heroLink{display:inline-flex;align-items:center;justify-content:center;padding:10px 16px;border-radius:8px;background:#12362f;border:1px solid #2f8766;color:#a8ffd6;text-decoration:none;font-weight:800;white-space:nowrap}.sectionTitle{font-size:24px;color:var(--blue);margin:0 0 16px}.groups{display:grid;gap:18px}.groupCard{padding:18px}.groupCard h3{margin:0 0 12px}.tableWrap{overflow-x:auto}table{width:100%;min-width:720px;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid var(--line);text-align:left}th{color:#8fffd0;background:#09211e}.top1 td{background:rgba(51,226,138,.12)}.top2 td{background:rgba(125,211,252,.10)}.homeGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;align-items:stretch;margin-bottom:28px}.fixtureCard{padding:18px;min-height:560px;display:flex;flex-direction:column}.fixtureCard h3,.miniGroupCard h3{margin:0 0 12px}.miniStandings{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;max-height:440px;overflow:auto;padding-right:4px}.miniStandings table{min-width:0}.miniStandings th,.miniStandings td{padding:6px 8px;font-size:12px}.miniStandings th{white-space:nowrap}.miniGroupCard{padding:10px}.miniGroupCard h3{font-size:14px;position:sticky;top:0;background:linear-gradient(180deg,rgba(16,37,40,.98),rgba(9,26,29,.98));padding-bottom:6px}.fixtureCard table{min-width:0}.fixtureCard td:first-child,.fixtureCard th:first-child{white-space:nowrap}footer{margin-top:40px;color:#8ea8a1;font-size:13px}@media(max-width:920px){.homeGrid{grid-template-columns:1fr}.fixtureCard{min-height:auto}.miniStandings{grid-template-columns:repeat(2,minmax(0,1fr));max-height:420px}}@media(max-width:620px){.heroTop,.card{align-items:flex-start;flex-direction:column}.go{white-space:normal}.miniStandings{grid-template-columns:1fr;max-height:420px}}
</style>
</head>
<body>
<main>
<section class="hero">
<div class="heroTop">
<div>
<h1>2026 世界杯预测中心</h1>
<p>这里汇总每日预测看板、赛果复盘和模型校准记录，页面基于公开赔率与公开赛果持续更新。</p>
<div class="heroMeta"><span>最新更新时间：$(HE $UpdateTime)</span><span>当前主推页面：$(DateTitle $DateText)</span></div>
</div>
<a class="heroLink" href="./standings.html">全部小组积分榜</a>
</div>
</section>
<section class="homeGrid">
$tomorrowFixtures
<div class="fixtureCard"><h3>首页小组排行榜</h3><p>首页只保留各组排名和积分，作为快速扫榜入口，完整数据请从右上角入口进入。</p><div class="miniStandings">$compactStandings</div></div>
</section>
<section class="list">
$($cards -join "`n")
</section>
<footer>仅供公开信息分析参考，不构成投注建议。</footer>
</main>
</body>
</html>
"@
}

function ResultLean($Result) {
  $homeGoals = [int]$Result.homeGoals
  $awayGoals = [int]$Result.awayGoals
  if ($homeGoals -gt $awayGoals) { return "home" }
  if ($awayGoals -gt $homeGoals) { return "away" }
  return "draw"
}

function BuildReviewModelNote($Settled, $GoalHits, $SideHits) {
  if ($Settled -le 0) {
    return "昨日赛果仍在等待完整回填，今日模型先维持赔率主线，但底层已经改成三件事：强热盘不再机械深穿，0:0/1:1低位盘自动补平局保护，积分榜统一按全部已录入赛果实时重算。"
  }

  $goalMisses = $Settled - $GoalHits
  $sideMisses = $Settled - $SideHits
  $goalTone = if ($GoalHits -eq 0) {
    "总进球全部偏离，说明模型不能只盯最低总进球赔率，需要给尾部进球和补时波动更高权重。"
  } elseif ($GoalHits -lt $goalMisses) {
    "总进球命中一般，说明热门低赔的稳定性不足，今日继续保留 3-4 球尾部和偷一球脚本。"
  } else {
    "总进球命中尚可，说明主线区间判断有效，今日主要修正胜负方向的容错。"
  }

  $sideTone = if ($SideHits -eq 0) {
    "胜平负方向也全部跑偏，今日必须降低单边热度，更多保留平局与一球冷门。"
  } elseif ($SideHits -lt $sideMisses) {
    "胜平负方向稳定性一般，今日不做机械站边，重点看强队小胜与均衡盘平局保护。"
  } else {
    "胜平负方向相对稳定，今日仍以赔率最强侧为锚，但减少深穿预设。"
  }

  return "$goalTone $sideTone 结合6月24日复盘，今日额外强调两类小组赛剧本：像英格兰 0比0 加纳这种同组卡位战，优先判断先不输而不是先冲穿盘；像葡萄牙 5比0 乌兹别克斯坦这种强弱分明首轮，净胜球价值会显著抬高，强队领先后仍可能继续前压。今日已把底层逻辑直接改掉：一，强队热盘若让球没有同步深压，不再默认大胜，比分和半全场都会保留一球胜与平局回撤；二，0:0、1:1赔率同时偏低的比赛，半全场优先补平/平、平/胜或平/负脚本；三，3球与4球赔率挤在一起的强势盘，Poisson 总进球自动上修 0.15-0.35，避免再次把尾部进球压扁。全部小组积分榜也已改成按历史赛果实时重算，不再依赖静态快照。"
}

function BuildPreviousReview() {
  $previousFile = ""
  try {
    $dt = [datetime]::ParseExact($payload.dateText, "yyyy-MM-dd", [System.Globalization.CultureInfo]::InvariantCulture)
    $candidateFiles = Get-ChildItem -Path (Join-Path $root "data") -Filter "*.json" |
      Where-Object {
        $_.BaseName -match "^\d{8}$" -and
        [datetime]::ParseExact($_.BaseName, "yyyyMMdd", [System.Globalization.CultureInfo]::InvariantCulture) -lt $dt
      } |
      Sort-Object BaseName -Descending

    foreach ($candidate in @($candidateFiles)) {
      $candidatePayload = Get-Content -Raw -Encoding UTF8 $candidate.FullName | ConvertFrom-Json
      $worldCupMatches = @($candidatePayload.matches | Where-Object { [string]$_.league -eq "世界杯" })
      $settledWorldCupMatches = @(
        $worldCupMatches | Where-Object {
          $_.result -and $null -ne $_.result.homeGoals -and $null -ne $_.result.awayGoals
        }
      )
      if ($settledWorldCupMatches.Count -gt 0) {
        $previousFile = $candidate.FullName
        break
      }
    }
  }
  catch {
    return ""
  }

  if (-not (Test-Path $previousFile)) {
    return ""
  }

  $previous = Get-Content -Raw -Encoding UTF8 $previousFile | ConvertFrom-Json
  $reviewRows = New-Object System.Collections.Generic.List[string]
  $settled = 0
  $goalHits = 0
  $sideHits = 0

  foreach ($pm in @($previous.matches)) {
    if (-not $pm.result -or $null -eq $pm.result.homeGoals -or $null -eq $pm.result.awayGoals) {
      $predictedScores = if ($pm.prediction -and $pm.prediction.scores) { HE (@($pm.prediction.scores) -join " / ") } else { "-" }
      $reviewRows.Add("<tr><td>" + (HE $pm.matchNumStr) + "</td><td>" + (HE "$($pm.home) vs $($pm.away)") + "</td><td>" + (GoalLabel $pm.prediction.totalGoals) + "</td><td>" + $predictedScores + "</td><td>&#24453;&#22238;&#22635;</td><td>&#24453;&#23450;</td><td>&#31561;&#24453;&#36187;&#26524;&#22238;&#22635;</td></tr>")
      continue
    }

    $settled += 1
    $actualTotal = [int]$pm.result.homeGoals + [int]$pm.result.awayGoals
    $goalHit = ([string]$actualTotal -eq [string]$pm.prediction.totalGoals)
    if ($goalHit) { $goalHits += 1 }

    $predLean = GetLean $pm
    $actualLean = ResultLean $pm.result
    $sideHit = ($predLean.code -eq $actualLean)
    if ($sideHit) { $sideHits += 1 }

    $goalVerdict = if ($goalHit) { "&#21629;&#20013;" } else { "&#26410;&#20013;" }
    $sideVerdict = if ($sideHit) { "&#26041;&#21521;&#21629;&#20013;" } else { "&#26041;&#21521;&#20559;&#31163;" }
    $predictedScores = if ($pm.prediction -and $pm.prediction.scores) { HE (@($pm.prediction.scores) -join " / ") } else { "-" }
    $scoreText = (HE "$($pm.result.homeGoals):$($pm.result.awayGoals)")
    $why = if (-not $sideHit -and $actualLean -eq "draw") {
      "平局保护不足，已补强 0:0 / 1:1 低位盘的平局脚本。"
    }
    elseif (-not $goalHit -and $actualTotal -ge ([int](ToDouble $pm.prediction.totalGoals 0) + 2)) {
      "尾部进球被低估，已上修强势盘的 3-4 球分布。"
    }
    elseif (-not $goalHit -and $actualTotal -lt [int](ToDouble $pm.prediction.totalGoals 0)) {
      "比赛节奏被压住，已抬高低总进球盘的试探局与慢热权重。"
    }
    elseif (-not $sideHit) {
      "热门方向过热，已降低机械站边权重。"
    }
    else {
      "主线判断仍有效，本次主要用于校正比分尾部。"
    }
    $note = "&#23454;&#38469;&#24635;&#36827;&#29699; $actualTotal&#65292;&#39044;&#27979;" + $goalVerdict + "&#65307;" + $sideVerdict + "&#12290;" + (HE $why)
    $reviewRows.Add("<tr><td>" + (HE $pm.matchNumStr) + "</td><td>" + (HE "$($pm.home) vs $($pm.away)") + "</td><td>" + (GoalLabel $pm.prediction.totalGoals) + "</td><td>" + $predictedScores + "</td><td>" + $scoreText + "</td><td>" + $goalVerdict + " / " + $sideVerdict + "</td><td>" + $note + "</td></tr>")
  }

  $goalRate = if ($settled -gt 0) { [math]::Round(($goalHits / $settled) * 100, 1).ToString() + "%" } else { "&#24453;&#23450;" }
  $sideRate = if ($settled -gt 0) { [math]::Round(($sideHits / $settled) * 100, 1).ToString() + "%" } else { "&#24453;&#23450;" }

  $modelNote = BuildReviewModelNote -Settled $settled -GoalHits $goalHits -SideHits $sideHits
  return "<section id=""reviewModel"" class=""section""><h2>&#26152;&#26085;&#22797;&#30424;&#19982;&#20170;&#26085;&#27169;&#22411;&#20462;&#27491;</h2><div class=""recommend""><div class=""kv""><div><strong>&#24050;&#32467;&#31639;</strong>$settled &#22330;</div><div><strong>&#24635;&#36827;&#29699;&#21629;&#20013;</strong>$goalHits / $settled ($goalRate)</div><div><strong>&#32988;&#24179;&#36127;&#26041;&#21521;</strong>$sideHits / $settled ($sideRate)</div><div><strong>&#20170;&#26085;&#20462;&#27491;</strong>&#24179;&#23616;&#20445;&#25252; + &#24378;&#30424;&#23614;&#37096;&#19978;&#20462; + &#20840;&#37327;&#31215;&#20998;&#27036;&#23454;&#26102;&#37325;&#31639;</div></div><table><thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#39044;&#27979;&#24635;&#36827;&#29699;</th><th>&#39044;&#27979;&#27604;&#20998;</th><th>&#26368;&#32456;&#27604;&#20998;</th><th>&#21629;&#20013;</th><th>&#22797;&#30424;&#32467;&#35770;</th></tr></thead><tbody>" + ($reviewRows -join "") + "</tbody></table><p class=""modelNote"">&#27169;&#22411;&#21453;&#39304;&#65306;" + (HE $modelNote) + "</p></div></section>"
}

$script:historicalMatches = GetHistoricalMatches
$standingsSnapshot = if ($payload.PSObject.Properties.Name -contains "standingsSnapshot") { $payload.standingsSnapshot } else { $null }
$standingsBundle = BuildStandingsBundle $payload.matches $standingsSnapshot

$summaryCards = New-Object System.Collections.Generic.List[string]
$detailCards = New-Object System.Collections.Generic.List[string]
$navLinks = New-Object System.Collections.Generic.List[string]
$resultRows = New-Object System.Collections.Generic.List[string]
$buyRows = New-Object System.Collections.Generic.List[string]
$goalComboRows = New-Object System.Collections.Generic.List[string]
$scoreComboRows = New-Object System.Collections.Generic.List[string]
$scoreArtifacts = New-Object System.Collections.Generic.List[object]
$evArtifacts = New-Object System.Collections.Generic.List[object]
$rows = @()

$i = 0
foreach ($m in $payload.matches) {
  $i += 1
  $lean = GetLean $m
  $scoreCard = BuildScoreCard $m $lean $standingsBundle
  $evArtifact = BuildEvArtifact $m $lean $scoreCard
  $halfFull = BuildHalfFullArtifact $m $lean $evArtifact
  $hot = HotLabel $m $lean
  $tagClass = if ($hot -eq (C "cold")) { "tag hot" } else { "tag" }
  $goalOdd = GoalOdd $m
  $impactText = $standingsBundle.impactLookup[[string]$m.id]
  $groupStandingBrief = MatchGroupStandingBrief $m $standingsBundle
  $buyText = if ($lean.strong) { "&#24635;&#36827;&#29699; " + (GoalLabel $m.prediction.totalGoals) } elseif ($lean.code -eq "away") { $lean.text + " + &#24635;&#36827;&#29699; " + (GoalLabel $m.prediction.totalGoals) } else { "&#38450;&#24179; + &#24635;&#36827;&#29699; " + (GoalLabel $m.prediction.totalGoals) }
  $buyReason = if ($lean.strong) { "&#36180;&#29575;&#24378;&#20542;&#21521; + &#27604;&#20998;&#20027;&#32447;&#38598;&#20013;" } elseif ($lean.code -eq "away") { "&#23458;&#32988;&#21387;&#21046;&#26126;&#26174;&#65292;&#20998;&#25903;&#36335;&#24452;&#28165;&#26224;" } else { "&#24179;&#34913;&#23616;&#38656;&#35201;&#25226;&#38450;&#23432;&#25569;&#22312;&#25163;&#37324;" }
  $resultRows.Add("<tr><td>" + (HE $m.matchNumStr) + "</td><td>" + (HE "$($m.home) vs $($m.away)") + "</td><td>" + (HE $groupStandingBrief) + "</td><td>" + $lean.text + "</td><td>" + (HE $halfFull.primary) + "</td><td>" + (GoalLabel $m.prediction.totalGoals) + " / " + (HE $halfFull.totalBand) + "</td><td>" + (HE ($m.prediction.scores -join " / ")) + "</td><td>" + (HE $m.prediction.upset) + "</td><td>" + (MysticBrief $m $lean) + "</td><td>" + (Conf $m.prediction.confidence) + " / " + $scoreCard.stars + "</td></tr>")
  $buyRows.Add("<tr><td>" + (HE $m.matchNumStr) + "</td><td>" + (HE "$($m.home) vs $($m.away)") + "</td><td>" + $buyText + "</td><td>" + (HE $goalOdd) + "</td><td>" + $buyReason + "</td></tr>")
  $summaryCards.Add("<div class=""mini""><span class=""" + $tagClass + """>" + (HE $m.matchNumStr) + " " + $hot + "</span><div class=""teams"">" + (HE $m.home) + " vs " + (HE $m.away) + "</div><small>" + (Overview $m $lean) + "</small></div>")
  $matchTitle = (HE "$($m.home) vs $($m.away)")
  $navLinks.Add("<a href=""#m$i"">" + $matchTitle + "</a>")
  $matchOpen = if ($i -eq 1) { " open" } else { "" }
  $detailCards.Add("<section id=""m$i"" class=""card matchCard""><details class=""matchShell""" + $matchOpen + "><summary><div class=""matchHead""><div><span class=""tagLine"">" + (HE $m.matchNumStr) + " | " + $matchTitle + "</span><h3>" + (HE $m.home) + " vs " + (HE $m.away) + "</h3><p class=""matchSub"">&#27604;&#36187;&#26102;&#38388;&#65288;&#21271;&#20140;&#26102;&#38388;&#65289;&#65306;" + (HE (MatchKickoffBeijingFull $m)) + "</p><p class=""matchSub"">&#25152;&#23646;&#23567;&#32452;&#25490;&#21517;&#65306;" + $groupStandingBrief + "</p></div><div class=""matchQuick""><span><b>&#26041;&#21521;</b>" + $lean.text + "</span><span><b>&#24635;&#36827;&#29699;</b>" + (GoalLabel $m.prediction.totalGoals) + "</span><span><b>&#31283;&#32966;</b>" + (HE ($m.prediction.scores -join " / ")) + "</span><span><b>&#32622;&#20449;</b>" + $scoreCard.stars + "</span></div></div></summary><div class=""matchBody""><div class=""meta"">" + (HE $m.league) + " | " + (HE (MatchWindowSummary $m)) + " | &#20986;&#32447;&#24433;&#21709;&#65306;" + (HE $impactText) + "</div><div class=""panel""><div><details open><summary>" + (C "basic") + "</summary><p>" + (Basic $m $lean) + "</p></details><details><summary>" + (C "tactics") + "</summary><p>" + (Tactics $m $lean) + "</p></details><details><summary>" + (C "external") + "</summary><p>" + (External $m) + "</p></details><details><summary>" + (C "group") + "</summary><p>" + (GroupInfo $m $lean) + "</p></details><details><summary>" + (C "odds") + "</summary><p>" + (OddsText $m $lean) + "</p></details><details><summary>6. 外部实时数据</summary><p>" + (ExternalLiveData $m) + "</p></details></div><div class=""pred""><div class=""box boxWide""><h4>量化评分卡</h4><p>评分方向：" + $lean.text + "，综合星级 " + $scoreCard.stars + "。玄学已独立，不参与综合打分。</p>" + (ScoreCardHtml $scoreCard) + "</div><div class=""box""><h4>" + (C "total") + "</h4><div class=""big"">" + (GoalLabel $m.prediction.totalGoals) + "</div><small>&#31616;&#21270;Poisson λ: " + ("{0:N2}" -f $evArtifact.lambdaHome) + " / " + ("{0:N2}" -f $evArtifact.lambdaAway) + " | &#32622;&#20449;&#35828;&#26126;&#65306;" + (Conf $m.prediction.confidence) + "</small></div><div class=""box""><h4>半全场与进球区间</h4>" + (HalfFullHtml $halfFull) + "</div><div class=""box""><h4>" + (C "steady") + "</h4><span class=""score"">" + (HE $m.prediction.scores[0]) + "</span><span class=""score"">" + (HE $m.prediction.scores[1]) + "</span></div><div class=""box""><h4>" + (C "upset") + "</h4><span class=""score upset"">" + (HE $m.prediction.upset) + "</span></div><div class=""box boxWide""><h4>比分EV明细</h4><div class=""innerTable"">" + (EvTableHtml $evArtifact) + "</div></div><div class=""box boxWide mystic mysticFull""><h4>玄学独立分析</h4><p>" + (Mystic $m $lean) + "</p></div><div class=""box boxWide""><h4>" + (C "brief") + "</h4><p>" + (Quick $m $lean) + "</p></div></div></div></div></details></section>")
  $scoreArtifacts.Add([pscustomobject]@{
    id = $m.id
    match = "$($m.home) vs $($m.away)"
    lean = $lean.code
    stars = $scoreCard.stars
    composite = $scoreCard.composite
    dimensions = $scoreCard.dimensions
    probabilities = $scoreCard.probabilities
    recent = $scoreCard.recent
  })
  $evArtifacts.Add([pscustomobject]@{
    id = $m.id
    match = "$($m.home) vs $($m.away)"
    lambdaHome = $evArtifact.lambdaHome
    lambdaAway = $evArtifact.lambdaAway
    totalLambda = $evArtifact.totalLambda
    halfFull = $halfFull
    rows = $evArtifact.rows
    best = $evArtifact.best
  })
  $rows += [pscustomobject]@{ match = $m; lean = $lean; goalOdd = [decimal](ToDouble (GoalOdd $m) 99); score = $scoreCard; ev = $evArtifact }
}

$bestStrong = $rows | Where-Object { $_.lean.strong } | Select-Object -First 1
if (-not $bestStrong) { $bestStrong = $rows | Select-Object -First 1 }
$bestCold = $rows | Sort-Object { if ($_.lean.strong) { 2 } elseif ($_.lean.code -eq "away") { 0 } else { 1 } } | Select-Object -First 1
$goalRoute = (($rows | ForEach-Object { [int]$_.match.prediction.totalGoals } | Sort-Object | Get-Unique) -join "-") + "&#29699;&#20026;&#20027;"
$dayLuck = if ($bestStrong.lean.code -eq "away") { "&#23458;&#26041;&#26106;&#21183;&#65292;&#39034;&#21183;&#26356;&#33298;&#26381;" } else { "&#28779;&#22303;&#26106;&#65292;&#24378;&#38431;&#20808;&#25163;&#20339;" }

$goalPicks = $rows | Sort-Object goalOdd | Select-Object -First ([Math]::Min(3, $rows.Count))
$goalCombo = 1.0
foreach ($p in $goalPicks) {
  $goalComboRows.Add("<tr><td>" + (HE "$($p.match.home) vs $($p.match.away)") + "</td><td>" + (GoalLabel $p.match.prediction.totalGoals) + "</td><td>" + ("{0:N2}" -f $p.goalOdd) + "</td><td>&#36180;&#29575;&#20027;&#32447;&#19982;&#27169;&#22411;&#21516;&#21521;&#65292;&#35780;&#20998; " + ("{0:N2}" -f $p.score.composite) + "</td></tr>")
  $goalCombo *= [math]::Max([double]$p.goalOdd, 1.01)
}

$scorePicks = @($rows | ForEach-Object {
  $matchRow = $_
  $preferredScores = @($matchRow.match.prediction.scores)
  $preferred = @($matchRow.ev.rows | Where-Object { $preferredScores -contains $_.score } | Sort-Object ev -Descending)
  $pick = if ($preferred.Count -gt 0) { $preferred[0] } else { $_.ev.best }
  [pscustomobject]@{
    id = $matchRow.match.id
    match = "$($matchRow.match.home) vs $($matchRow.match.away)"
    pick = $pick
  }
} | Sort-Object { $_.pick.ev } -Descending | Select-Object -First ([Math]::Min(3, $rows.Count)))
$scoreCombo = 1.0
$scoreComboEv = 1.0
foreach ($p in $scorePicks) {
  $odd = [double]$p.pick.odds
  $scoreCombo *= [math]::Max($odd, 1.01)
  $scoreComboEv *= (1 + [double]$p.pick.ev)
  $evLabel = if ($p.pick.ev -gt 0) { "&#27491;EV" } else { "&#35266;&#26395;" }
  $scoreComboRows.Add("<tr><td>" + (HE $p.match) + "</td><td>" + (HE $p.pick.score) + "</td><td>" + ("{0:N2}" -f $odd) + "</td><td>$evLabel / EV " + ("{0:N2}" -f $p.pick.ev) + "</td></tr>")
}

$reviewLink = ""
if (Test-Path (Join-Path $dayDir "review.html")) {
  $reviewLink = "<a href=""./review.html"">" + (C "review") + "</a>"
}
$previousReviewSection = BuildPreviousReview
$standingsSection = "<section id=""standings"" class=""section""><h2>&#23567;&#32452;&#31215;&#20998;&#27036;&#19982;&#20986;&#32447;&#20998;&#26512;</h2>" + (StandingsSectionHtml $standingsBundle $payload.matches) + "</section>"
$knockoutScenarioSection = KnockoutScenarioSectionHtml $standingsBundle

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
main{max-width:1240px;margin:auto;padding:20px 18px 50px}.section{margin:22px 0 34px}.section h2{font-size:26px;margin:0 0 16px;color:var(--blue)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.tableWrap,.innerTable{overflow-x:auto}.stack{display:grid;gap:18px}@media(max-width:950px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.grid{grid-template-columns:1fr}nav a{flex:1;text-align:center}}
.mini,.card,.combo,.recommend{background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));border:1px solid var(--line);border-radius:8px;box-shadow:0 16px 36px rgba(0,0,0,.28)}.mini{padding:16px;transition:.22s}.mini:hover,.card:hover,.combo:hover,.recommend:hover{transform:translateY(-3px);border-color:#39d98a}
.tag{display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:999px;background:#12362f;color:var(--green);font-size:12px;border:1px solid #246b59}.hot{background:#422018;color:#ffd0a0;border-color:#ff8a38}.teams{font-size:21px;font-weight:800;margin:11px 0 6px}.kv{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}@media(max-width:760px){.kv{grid-template-columns:repeat(2,1fr)}}.kv div{background:#071817;border:1px solid #173b35;border-radius:7px;padding:10px;text-align:center}.kv strong{display:block;color:var(--mint);font-size:18px}
.card{padding:18px;margin-bottom:22px;scroll-margin-top:110px}.card h3{font-size:28px;margin:0 0 6px}.meta{color:var(--muted);margin-bottom:14px}.panel{display:grid;grid-template-columns:1.05fr .95fr;gap:16px}@media(max-width:860px){.panel{grid-template-columns:1fr}}
details{border:1px solid #1b463f;border-radius:8px;margin:9px 0;background:#071817;overflow:hidden}summary{cursor:pointer;padding:12px 14px;color:var(--mint);font-weight:700}details p{margin:0;padding:0 14px 14px;color:#d8eee8;line-height:1.7}.pred{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;align-content:start}.box{border:1px solid #1c5048;background:#071817;border-radius:8px;padding:13px}.boxWide{grid-column:1/-1}.box h4{margin:0 0 8px;color:var(--blue)}.big{font-size:32px;color:var(--green);font-weight:900}.score{display:inline-block;margin:4px 8px 4px 0;padding:8px 12px;border-radius:8px;border:1px solid #2ecf7a;background:#0d3028;color:#a8ffd6;font-weight:800}.upset{border-color:var(--red);background:#331415;color:#ffd2b0}.mystic{background:linear-gradient(135deg,var(--purple),#1c1538);border-color:#8d5cff}.mysticFull{padding:16px 16px 18px}.mysticFull h4{margin-bottom:10px}.mysticFull p{margin:0;color:#f2eaff;line-height:1.92;font-size:15px}.hf{display:grid;gap:10px}.hf div{display:flex;justify-content:space-between;gap:12px;padding:8px 10px;border:1px solid #1f4a43;border-radius:8px;background:#0a1f23}.hf span{color:var(--muted)}.hf strong{color:var(--mint)}.hf p{margin:0;color:#d6ece7;line-height:1.6}
.matchCard{padding:0;overflow:hidden}.matchShell{margin:0;border:none;background:transparent}.matchShell>summary{list-style:none;padding:18px;background:linear-gradient(180deg,rgba(16,37,40,.98),rgba(9,26,29,.98))}.matchShell>summary::-webkit-details-marker{display:none}.matchHead{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.tagLine{display:inline-block;margin-bottom:8px;color:var(--mint);font-size:12px;letter-spacing:.08em;text-transform:uppercase}.matchSub{margin:0;color:var(--muted);padding:0}.matchQuick{display:grid;grid-template-columns:repeat(2,minmax(140px,1fr));gap:8px;min-width:min(100%,380px)}.matchQuick span{display:block;padding:10px 12px;border:1px solid #1f4a43;border-radius:8px;background:#0b201d;color:#dff9f1}.matchQuick b{display:block;color:var(--muted);font-size:12px;margin-bottom:4px}.matchBody{padding:0 18px 18px}@media(max-width:860px){.pred{grid-template-columns:1fr}.matchHead{flex-direction:column}.matchQuick{grid-template-columns:repeat(2,minmax(0,1fr));width:100%}}@media(max-width:520px){.matchQuick{grid-template-columns:1fr}}
.recommend,.combo{padding:18px;margin-bottom:18px}.recommend table,.combo table,.evTable{width:100%;border-collapse:collapse;overflow:hidden;border-radius:8px;min-width:820px}th,td{padding:12px;border-bottom:1px solid #1b463f;text-align:left}th{color:var(--mint);background:#09211e}.scorecard{display:grid;gap:8px}.scorehead{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.scorehead strong{font-size:24px;color:var(--green)}.scorehead em{color:#ffe39c;font-style:normal}.metric{display:grid;grid-template-columns:92px 1fr 42px;align-items:center;gap:8px}.metric span,.metric strong{font-size:13px}.bar{height:9px;border-radius:999px;background:#102528;border:1px solid #1f4a43;overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,#2ecf7a,#7dd3fc)}.pos{color:#8fffd0}.neg{color:#ffb2b8}.standingsCard .impact p{margin:10px 0 0;color:#d6ece7}.hl td{background:rgba(51,226,138,.08)}footer{color:#8ea8a1;text-align:center;border-top:1px solid var(--line);padding:24px 12px;font-size:13px}
</style>
</head>
<body>
<header><div class="hero"><h1>&#127757; 2026&#19990;&#30028;&#26479; &#39044;&#27979;&#30475;&#26495; $(DateTitle $payload.dateText)</h1><nav><a href="#reviewModel">&#22797;&#30424;&#20462;&#27491;</a><a href="#final">$(C "final")</a><a href="#overview">$(C "overview")</a>$($navLinks -join "")<a href="#standings">&#23567;&#32452;&#31215;&#20998;&#27036;</a><a href="#knockoutScenario">&#28120;&#27760;&#36187;&#21095;&#26412;</a><a href="#combo">$(C "combo")</a>$reviewLink<a href="../index.html">$(C "home")</a></nav></div></header>
<main>
$previousReviewSection
<section id="final" class="section"><h2>$(C "final")</h2><div class="recommend"><div class="tableWrap"><table><thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#25152;&#23646;&#23567;&#32452;&#25490;&#21517;</th><th>&#32988;&#24179;&#36127;&#26041;&#21521;</th><th>&#21322;&#20840;&#22330;</th><th>&#24635;&#36827;&#29699;</th><th>&#31283;&#32966;&#27604;&#20998;</th><th>&#20919;&#38376;&#27604;&#20998;</th><th>&#29572;&#23398;&#29420;&#31435;&#32467;&#35770;</th><th>&#32622;&#20449;</th></tr></thead><tbody>$($resultRows -join "")</tbody></table></div></div></section>
<section id="buy" class="section"><h2>$(C "buy")</h2><div class="recommend"><div class="tableWrap"><table><thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#25512;&#33616;&#20080;&#27861;</th><th>&#21442;&#32771;&#36180;&#29575;</th><th>$(C "reason")</th></tr></thead><tbody>$($buyRows -join "")</tbody></table></div></div></section>
<section id="overview" class="section"><h2>$(C "summary")</h2><div class="grid">$($summaryCards -join "")</div><div class="kv"><div><strong>$(C "best")</strong>$(HE $bestStrong.match.home) vs $(HE $bestStrong.match.away) / $(GoalLabel $bestStrong.match.prediction.totalGoals)</div><div><strong>$(C "biggestCold")</strong>$(HE $bestCold.match.home) vs $(HE $bestCold.match.away) / $(HE $bestCold.match.prediction.upset)</div><div><strong>$(C "route")</strong>$goalRoute</div><div><strong>$(C "luck")</strong>$dayLuck</div></div></section>
$($detailCards -join "")
$standingsSection
$knockoutScenarioSection
<section id="combo" class="section"><h2>$(C "combo")</h2><div class="combo"><h3>&#19977;&#20018;&#19968; &#24635;&#36827;&#29699;&#25968;</h3><div class="tableWrap"><table><thead><tr><th>&#22330;&#27425;</th><th>&#25512;&#33616;&#24635;&#36827;&#29699;</th><th>&#21333;&#39033;&#36180;&#29575;</th><th>&#27169;&#22411;&#29702;&#30001;</th></tr></thead><tbody>$($goalComboRows -join "")</tbody></table></div><p><strong>&#32452;&#21512;&#36180;&#29575;&#20272;&#31639;&#65306;</strong>&#8776; <span class="big">$(('{0:N2}' -f $goalCombo))</span></p></div><div class="combo"><h3>&#19977;&#20018;&#19968; &#27604;&#20998;</h3><div class="tableWrap"><table><thead><tr><th>&#22330;&#27425;</th><th>&#25512;&#33616;&#31283;&#32966;&#27604;&#20998;</th><th>&#20272;&#31639;&#36180;&#29575;</th><th>&#27169;&#22411;&#29702;&#30001;</th></tr></thead><tbody>$($scoreComboRows -join "")</tbody></table></div><p><strong>&#32452;&#21512;&#36180;&#29575;&#20272;&#31639;&#65306;</strong>&#8776; <span class="big">$(('{0:N2}' -f $scoreCombo))</span></p><p><strong>&#32452;&#21512;EV&#20272;&#31639;&#65306;</strong>&#8776; <span class="big">$(('{0:N2}' -f ($scoreComboEv - 1)))</span></p></div><div class="combo"><h3>$(C "risk")</h3><p>&#32452;&#21512;&#20165;&#20026;&#23089;&#20048;&#21442;&#32771;&#65292;&#19981;&#20445;&#35777;&#21629;&#20013;&#12290;&#33509;&#25152;&#26377;&#27604;&#20998;EV&#37117;&#20026;&#36127;&#65292;&#20248;&#20808;&#20445;&#30041;&#24635;&#36827;&#29699;&#20027;&#32447;&#25110;&#32988;&#24179;&#36127;&#26041;&#21521;&#65292;&#27604;&#20998;&#24314;&#35758;&#38477;&#19968;&#26723;&#22788;&#29702;&#12290;</p></div></section>
</main>
<footer>&#9888;&#65039; &#20165;&#20379;&#23089;&#20048;&#20998;&#26512;&#21442;&#32771;&#65292;&#19981;&#26500;&#25104;&#20219;&#20309;&#36141;&#24425;&#24314;&#35758;&#65292;&#35831;&#29702;&#24615;&#36141;&#24425;&#65281;</footer>
</body>
</html>
"@

$html = [string][System.Net.WebUtility]::HtmlDecode([string]$html)
Set-Content -LiteralPath $dayIndex -Encoding UTF8 -Value @($html)
Set-Content -LiteralPath $predictFile -Encoding UTF8 -Value @($html)

$script:homePageMatches = @($payload.matches)
$rootHtml = BuildRootIndexHtml $root $standingsBundle $Date $payload.dateText $payload.lastUpdateTime
$rootHtml = [string][System.Net.WebUtility]::HtmlDecode([string]$rootHtml)
Set-Content -LiteralPath $rootIndex -Encoding UTF8 -Value @($rootHtml)

$standingsHtml = BuildStandingsPageHtml $standingsBundle $Date $payload.dateText $payload.lastUpdateTime
$standingsHtml = [string][System.Net.WebUtility]::HtmlDecode([string]$standingsHtml)
Set-Content -LiteralPath $rootStandingsPage -Encoding UTF8 -Value @($standingsHtml)

$scoreJsonFile = Join-Path $dayDir ("scores_" + $Date + ".json")
$evJsonFile = Join-Path $dayDir ("ev_" + $Date + ".json")
$standingsJsonFile = Join-Path $dayDir ("standings_" + $Date + ".json")

Set-Content -LiteralPath $scoreJsonFile -Encoding UTF8 -Value ($scoreArtifacts | ConvertTo-Json -Depth 10)
Set-Content -LiteralPath $evJsonFile -Encoding UTF8 -Value ($evArtifacts | ConvertTo-Json -Depth 10)
Set-Content -LiteralPath $standingsJsonFile -Encoding UTF8 -Value (
  @($standingsBundle.groups | ForEach-Object {
    [pscustomobject]@{
      group = $_.group
      rows = $_.rows
    }
  }) | ConvertTo-Json -Depth 10
)

Write-Host "Generated daily board: $dayIndex"


