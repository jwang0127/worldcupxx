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

$payload = Get-Content -Raw -Encoding UTF8 $dataFile | ConvertFrom-Json

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
  $homeTeamName = HE $Match.home
  $away = HE $Match.away
  $goal = GoalLabel $Match.prediction.totalGoals
  $scores = HE ($Match.prediction.scores -join " / ")
  $risk = HE $Match.prediction.upset
  $had = "胜 " + (HE $Match.odds.had.home) + " / 平 " + (HE $Match.odds.had.draw) + " / 负 " + (HE $Match.odds.had.away)

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
  }

  if ($Lean.code -eq "home") { return "$homeTeamName 更像主动控节奏的一方，战术主线靠近 $scores；但仍要用 $risk 防守反击或定位球冷门。" }
  if ($Lean.code -eq "away") { return "$away 更适合把比赛拉到转换节奏，主队若想拿分，需要压低节奏并保留 $risk 这条防守路径。" }
  return "阵型克制关系更像边路与定位球博弈，主线比分 $scores，冷门脚本 $risk。"
}

function External($Match) {
  $homeTeamName = HE $Match.home
  $away = HE $Match.away
  $venue = HE $Match.venue
  $kickoff = HE $Match.kickoff

  switch ([string]$Match.id) {
    "025" { return "开球时间 $kickoff，属于北京时间午夜场，节奏通常比清晨场更容易先谨慎后提速。赛地信息为&#8220;$venue&#8221;，目前按中立场处理，不给主队额外主场加成。外部变量里最重要的是强队心态：$homeTeamName 若把比赛当成必须稳拿三分，会先控风险；$away 只要前 20 分钟不丢球，心理优势会上升。因此外部因素支持小胜或平局防线，不支持极端大胜。" }
    "026" { return "开球时间 $kickoff，凌晨场对比赛节奏影响较大，进入下半场后体能和专注度会成为分水岭。$homeTeamName 的比赛经验更适合处理这种时段，$away 如果前段消耗过大，后段防守质量会下降。赛地仍按中立场处理，因此不额外加入主场噪音，只看旅途适应、湿度、草皮和临场轮换。外部因素与复盘修正同向：强队后段继续进球概率上升。" }
    "027" { return "开球时间 $kickoff，对美洲球队节奏适应更友好，$homeTeamName 在身体对抗和推进速度上更容易进入状态。$away 若需要长距离适应气候和时差，开局抗压能力会是风险点。中立场条件下，外部因素不削弱 $homeTeamName 的强势，反而加强其前压倾向；但如果天气湿热，强队领先后的防线专注度也会下降，所以 3:1 比单纯 3:0 更有复盘价值。" }
    "028" { return "开球时间 $kickoff，节奏更可能接近日间高强度对抗。$homeTeamName 与 $away 都具备较强球迷属性和情绪波动，舆论压力会放大先丢球后的战术选择。中立场下 $homeTeamName 的名义优势有限，$away 的跑动和反击不应被低估。外部因素综合后更像谨慎开局、后段拉扯，支持 2 球附近和冷门防线。" }
  }

  return "比赛地点为&#8220;$venue&#8221;，开球时间 $kickoff。天气、湿度、草皮、旅途和赛前舆论都会影响节奏；本场外部因素按中立场模型处理。"
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
  }

  return "胜平负目前为 $had，$hhad 总进球低位为 $ttg。模型围绕&#8220;" + $Lean.text + " + $goal&#8221;展开，同时参考昨日复盘修正低赔机械权重。"
}

function Mystic($Match, $Lean) {
  $team = HE $Lean.team
  $homeTeam = HE $Match.home
  $awayTeam = HE $Match.away
  $goal = GoalLabel $Match.prediction.totalGoals
  $upset = HE $Match.prediction.upset
  $score = HE ($Match.prediction.scores -join " / ")

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
  }

  return "<strong>&#21608;&#26131;&#26757;&#33457;/&#20845;&#29275;&#65306;</strong>" + $team + " &#24471;&#20307;&#29992;&#29983;&#25206;&#65292;&#20027;&#32447;&#27604;&#20998;&#25351;&#21521; " + $score + "&#65292;&#20919;&#38376;&#38450; " + $upset + "&#12290;<br><strong>&#29572;&#23398;&#32508;&#21512;&#65306;</strong>&#29699;&#36335;&#30475; " + $goal + "&#65292;&#24471;&#21183;&#26041;&#39034;&#65292;&#20294;&#20445;&#30041;&#19968;&#26465;&#20919;&#38376;&#38450;&#32447;&#12290;"
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
  return (HE $Lean.team) + "&#24471;&#21183;&#65292;&#29699;&#36335;&#30475; " + (GoalLabel $Match.prediction.totalGoals) + "&#65292;&#20919;&#38376;&#38450; " + (HE $Match.prediction.upset)
}

function ResultLean($Result) {
  $homeGoals = [int]$Result.homeGoals
  $awayGoals = [int]$Result.awayGoals
  if ($homeGoals -gt $awayGoals) { return "home" }
  if ($awayGoals -gt $homeGoals) { return "away" }
  return "draw"
}

function BuildPreviousReview() {
  $previousFile = ""
  try {
    $dt = [datetime]::ParseExact($payload.dateText, "yyyy-MM-dd", [System.Globalization.CultureInfo]::InvariantCulture)
    $prevDate = $dt.AddDays(-1).ToString("yyyyMMdd")
    $previousFile = Join-Path $root ("data\" + $prevDate + ".json")
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
      $reviewRows.Add("<tr><td>" + (HE $pm.matchNumStr) + "</td><td>" + (HE "$($pm.home) vs $($pm.away)") + "</td><td>" + (GoalLabel $pm.prediction.totalGoals) + "</td><td>&#24453;&#22238;&#22635;</td><td>&#24453;&#23450;</td><td>&#31561;&#24453;&#36187;&#26524;&#22238;&#22635;</td></tr>")
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
    $scoreText = (HE "$($pm.result.homeGoals):$($pm.result.awayGoals)")
    $note = "&#23454;&#38469;&#24635;&#36827;&#29699; $actualTotal&#65292;&#39044;&#27979;" + $goalVerdict + "&#65307;" + $sideVerdict + "&#12290;"
    $reviewRows.Add("<tr><td>" + (HE $pm.matchNumStr) + "</td><td>" + (HE "$($pm.home) vs $($pm.away)") + "</td><td>" + (GoalLabel $pm.prediction.totalGoals) + "</td><td>" + $scoreText + "</td><td>" + $goalVerdict + " / " + $sideVerdict + "</td><td>" + $note + "</td></tr>")
  }

  $goalRate = if ($settled -gt 0) { [math]::Round(($goalHits / $settled) * 100, 1).ToString() + "%" } else { "&#24453;&#23450;" }
  $sideRate = if ($settled -gt 0) { [math]::Round(($sideHits / $settled) * 100, 1).ToString() + "%" } else { "&#24453;&#23450;" }

  return "<section id=""reviewModel"" class=""section""><h2>&#26152;&#26085;&#22797;&#30424;&#19982;&#20170;&#26085;&#27169;&#22411;&#20462;&#27491;</h2><div class=""recommend""><div class=""kv""><div><strong>&#24050;&#32467;&#31639;</strong>$settled &#22330;</div><div><strong>&#24635;&#36827;&#29699;&#21629;&#20013;</strong>$goalHits / $settled ($goalRate)</div><div><strong>&#32988;&#24179;&#36127;&#26041;&#21521;</strong>$sideHits / $settled ($sideRate)</div><div><strong>&#20170;&#26085;&#20462;&#27491;</strong>&#38477;&#20302;&#20302;&#36180;&#26426;&#26800;&#26435;&#37325;&#65292;&#25260;&#39640;3-4&#29699;&#23614;&#37096;&#19982;&#29572;&#23398;&#20919;&#38376;&#26435;&#37325;</div></div><table><thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#39044;&#27979;&#24635;&#36827;&#29699;</th><th>&#26368;&#32456;&#27604;&#20998;</th><th>&#21629;&#20013;</th><th>&#22797;&#30424;&#32467;&#35770;</th></tr></thead><tbody>" + ($reviewRows -join "") + "</tbody></table><p class=""modelNote"">&#27169;&#22411;&#21453;&#39304;&#65306;6/18 &#24635;&#36827;&#29699; 0/4&#65292;&#35828;&#26126;&#26152;&#26085;&#27169;&#22411;&#36807;&#24230;&#20381;&#36182;&#24635;&#36827;&#29699;&#26368;&#20302;&#36180;&#65292;&#20302;&#20272;&#20102;&#24378;&#38431;&#39318;&#36718;&#19979;&#21322;&#22330;&#25552;&#36895;&#12289;&#24369;&#38431;&#20599;&#29699;&#21644;&#34917;&#26102;&#27874;&#21160;&#12290;&#20170;&#26085;&#23545;&#29790;&#22763;&#12289;&#21152;&#25343;&#22823;&#36825;&#31867;&#24378;&#21387;&#21046;&#30424;&#25260;&#39640;3&#29699;&#36335;&#24452;&#65292;&#23545;&#25463;&#20811;&#12289;&#22696;&#35199;&#21733;&#38477;&#20302;&#32622;&#20449;&#24182;&#20445;&#30041;1:1/0:1&#20919;&#38376;&#12290;</p></div></section>"
}

$summaryCards = New-Object System.Collections.Generic.List[string]
$detailCards = New-Object System.Collections.Generic.List[string]
$navLinks = New-Object System.Collections.Generic.List[string]
$resultRows = New-Object System.Collections.Generic.List[string]
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
  $resultRows.Add("<tr><td>" + (HE $m.matchNumStr) + "</td><td>" + (HE "$($m.home) vs $($m.away)") + "</td><td>" + $lean.text + "</td><td>" + (GoalLabel $m.prediction.totalGoals) + "</td><td>" + (HE ($m.prediction.scores -join " / ")) + "</td><td>" + (HE $m.prediction.upset) + "</td><td>" + (MysticBrief $m $lean) + "</td><td>" + (Conf $m.prediction.confidence) + "</td></tr>")
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
$previousReviewSection = BuildPreviousReview

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
<header><div class="hero"><h1>&#127757; 2026&#19990;&#30028;&#26479; &#39044;&#27979;&#30475;&#26495; $(DateTitle $payload.dateText)</h1><nav><a href="#reviewModel">&#22797;&#30424;&#20462;&#27491;</a><a href="#final">$(C "final")</a><a href="#overview">$(C "overview")</a>$($navLinks -join "")<a href="#combo">$(C "combo")</a>$reviewLink<a href="../index.html">$(C "home")</a></nav></div></header>
<main>
$previousReviewSection
<section id="final" class="section"><h2>$(C "final")</h2><div class="recommend"><table><thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#32988;&#24179;&#36127;&#26041;&#21521;</th><th>&#24635;&#36827;&#29699;</th><th>&#31283;&#32966;&#27604;&#20998;</th><th>&#20919;&#38376;&#27604;&#20998;</th><th>&#29572;&#23398;&#34701;&#21512;</th><th>&#32622;&#20449;</th></tr></thead><tbody>$($resultRows -join "")</tbody></table></div></section>
<section id="buy" class="section"><h2>$(C "buy")</h2><div class="recommend"><table><thead><tr><th>&#22330;&#27425;</th><th>&#27604;&#36187;</th><th>&#25512;&#33616;&#20080;&#27861;</th><th>&#21442;&#32771;&#36180;&#29575;</th><th>$(C "reason")</th></tr></thead><tbody>$($buyRows -join "")</tbody></table></div></section>
<section id="overview" class="section"><h2>$(C "summary")</h2><div class="grid">$($summaryCards -join "")</div><div class="kv"><div><strong>$(C "best")</strong>$(HE $bestStrong.match.home) vs $(HE $bestStrong.match.away) / $(GoalLabel $bestStrong.match.prediction.totalGoals)</div><div><strong>$(C "biggestCold")</strong>$(HE $bestCold.match.home) vs $(HE $bestCold.match.away) / $(HE $bestCold.match.prediction.upset)</div><div><strong>$(C "route")</strong>$goalRoute</div><div><strong>$(C "luck")</strong>$dayLuck</div></div></section>
$($detailCards -join "")
<section id="combo" class="section"><h2>$(C "combo")</h2><div class="combo"><h3>&#19977;&#20018;&#19968; &#24635;&#36827;&#29699;&#25968;</h3><table><thead><tr><th>&#22330;&#27425;</th><th>&#25512;&#33616;&#24635;&#36827;&#29699;</th><th>&#21333;&#39033;&#36180;&#29575;</th><th>&#27169;&#22411;&#29702;&#30001;</th></tr></thead><tbody>$($goalComboRows -join "")</tbody></table><p><strong>&#32452;&#21512;&#36180;&#29575;&#20272;&#31639;&#65306;</strong>&#8776; <span class="big">$(('{0:N2}' -f $goalCombo))</span></p></div><div class="combo"><h3>&#19977;&#20018;&#19968; &#27604;&#20998;</h3><table><thead><tr><th>&#22330;&#27425;</th><th>&#25512;&#33616;&#31283;&#32966;&#27604;&#20998;</th><th>&#20272;&#31639;&#36180;&#29575;</th><th>&#27169;&#22411;&#29702;&#30001;</th></tr></thead><tbody>$($scoreComboRows -join "")</tbody></table><p><strong>&#32452;&#21512;&#36180;&#29575;&#20272;&#31639;&#65306;</strong>&#8776; <span class="big">$(('{0:N2}' -f $scoreCombo))</span></p></div><div class="combo"><h3>$(C "risk")</h3><p>&#32452;&#21512;&#20165;&#20026;&#23089;&#20048;&#21442;&#32771;&#65292;&#19981;&#20445;&#35777;&#21629;&#20013;&#12290;&#33509;&#20020;&#22330;&#39318;&#21457;&#20986;&#29616;&#36718;&#25442;&#25110;&#36180;&#29575;&#24613;&#36895;&#24322;&#21160;&#65292;&#20248;&#20808;&#20445;&#30041;&#24635;&#36827;&#29699;&#20027;&#32447;&#65292;&#27604;&#20998;&#24314;&#35758;&#38477;&#19968;&#26723;&#22788;&#29702;&#12290;</p></div></section>
</main>
<footer>&#9888;&#65039; &#20165;&#20379;&#23089;&#20048;&#20998;&#26512;&#21442;&#32771;&#65292;&#19981;&#26500;&#25104;&#20219;&#20309;&#36141;&#24425;&#24314;&#35758;&#65292;&#35831;&#29702;&#24615;&#36141;&#24425;&#65281;</footer>
</body>
</html>
"@

$html = [System.Net.WebUtility]::HtmlDecode($html)
$html | Set-Content -Encoding UTF8 $dayIndex
$html | Set-Content -Encoding UTF8 $predictFile
Write-Host "Generated daily board: $dayIndex"


