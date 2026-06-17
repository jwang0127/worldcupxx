param(
  [string]$Date = (Get-Date -Format "yyyyMMdd"),
  [string]$OutFile = "",
  [string]$PoolCode = "ttg,had",
  [switch]$Force,
  [switch]$MergeExisting
)

$ErrorActionPreference = "Stop"

function Get-RootDir {
  return (Split-Path -Parent $PSScriptRoot)
}

function Get-TargetDateText {
  param([string]$CompactDate)
  return ([datetime]::ParseExact($CompactDate, "yyyyMMdd", $null)).ToString("yyyy-MM-dd")
}

function Get-ExistingMatchMap {
  param([string]$Path)

  $map = @{}
  if (-not (Test-Path $Path)) {
    return $map
  }

  $existingPayload = Get-Content -Raw $Path | ConvertFrom-Json
  foreach ($existingMatch in @($existingPayload.matches)) {
    if ($existingMatch.matchId) {
      $map[[string]$existingMatch.matchId] = $existingMatch
    }
  }

  return $map
}

function Get-TopGoalsPrediction {
  param($Ttg)

  $pairs = @(
    @{ label = "0"; value = $Ttg.s0 },
    @{ label = "1"; value = $Ttg.s1 },
    @{ label = "2"; value = $Ttg.s2 },
    @{ label = "3"; value = $Ttg.s3 },
    @{ label = "4"; value = $Ttg.s4 },
    @{ label = "5"; value = $Ttg.s5 },
    @{ label = "6"; value = $Ttg.s6 },
    @{ label = "7+"; value = $Ttg.s7 }
  ) | Where-Object { $_.value }

  if (-not $pairs) {
    return @{
      totalGoals = "2"
      candidates = @("2", "3", "1")
      confidence = "low"
    }
  }

  $sorted = $pairs | Sort-Object { [decimal]$_.value }
  $gap = 0
  if ($sorted.Count -gt 1) {
    $gap = [math]::Round(([decimal]$sorted[1].value - [decimal]$sorted[0].value), 2)
  }

  $confidence = "medium"
  if ($gap -ge 0.6) {
    $confidence = "high"
  }
  elseif ($gap -lt 0.2) {
    $confidence = "low"
  }

  return @{
    totalGoals = $sorted[0].label
    candidates = @($sorted | Select-Object -First ([Math]::Min(3, $sorted.Count)) | ForEach-Object { $_.label })
    confidence = $confidence
  }
}

function Get-ResultLean {
  param($Had)

  if (-not $Had) {
    return "home"
  }

  $items = @(
    @{ code = "home"; value = $Had.h },
    @{ code = "draw"; value = $Had.d },
    @{ code = "away"; value = $Had.a }
  ) | Where-Object { $_.value }

  if (-not $items) {
    return "home"
  }

  return ($items | Sort-Object { [decimal]$_.value } | Select-Object -First 1).code
}

function Convert-ToIntGoals {
  param([string]$Label)

  if ($Label -eq "7+") {
    return 7
  }

  return [int]$Label
}

function Get-ScorePrediction {
  param(
    [string]$GoalLabel,
    [string]$Lean
  )

  $goals = Convert-ToIntGoals $GoalLabel

  switch ($Lean) {
    "draw" {
      switch ($goals) {
        0 { return @{ scores = @("0:0", "1:1"); upset = "1:0" } }
        1 { return @{ scores = @("1:1", "0:0"); upset = "1:0" } }
        2 { return @{ scores = @("1:1", "0:0"); upset = "2:1" } }
        3 { return @{ scores = @("2:2", "1:1"); upset = "2:1" } }
        4 { return @{ scores = @("2:2", "1:1"); upset = "3:1" } }
        default { return @{ scores = @("2:2", "3:3"); upset = "3:2" } }
      }
    }
    "away" {
      switch ($goals) {
        0 { return @{ scores = @("0:0", "0:1"); upset = "1:0" } }
        1 { return @{ scores = @("0:1", "1:0"); upset = "1:1" } }
        2 { return @{ scores = @("0:2", "1:1"); upset = "1:0" } }
        3 { return @{ scores = @("1:2", "0:3"); upset = "2:1" } }
        4 { return @{ scores = @("1:3", "0:4"); upset = "2:2" } }
        default { return @{ scores = @("2:3", "1:4"); upset = "2:2" } }
      }
    }
    default {
      switch ($goals) {
        0 { return @{ scores = @("0:0", "1:0"); upset = "0:1" } }
        1 { return @{ scores = @("1:0", "0:1"); upset = "1:1" } }
        2 { return @{ scores = @("2:0", "1:1"); upset = "0:1" } }
        3 { return @{ scores = @("2:1", "3:0"); upset = "1:2" } }
        4 { return @{ scores = @("3:1", "2:2"); upset = "1:2" } }
        default { return @{ scores = @("3:2", "4:1"); upset = "2:2" } }
      }
    }
  }
}

function Get-FirstNonEmptyValue {
  param(
    $Source,
    [string[]]$Names
  )

  if (-not $Source) {
    return $null
  }

  foreach ($name in $Names) {
    try {
      $value = $Source.PSObject.Properties[$name].Value
    }
    catch {
      $value = $null
    }

    if ($null -ne $value -and [string]$value -ne "") {
      return $value
    }
  }

  return $null
}

function Get-LiveResultFromMatch {
  param($Match)

  $homeGoals = Get-FirstNonEmptyValue $Match @("homeScore", "homeGoals", "homeGoal", "fullHomeScore", "homeTeamScore")
  $awayGoals = Get-FirstNonEmptyValue $Match @("awayScore", "awayGoals", "awayGoal", "fullAwayScore", "awayTeamScore")
  $status = [string](Get-FirstNonEmptyValue $Match @("matchStatus", "status"))

  if ($Match.result) {
    if ($null -eq $homeGoals) { $homeGoals = Get-FirstNonEmptyValue $Match.result @("homeGoals", "homeScore", "home") }
    if ($null -eq $awayGoals) { $awayGoals = Get-FirstNonEmptyValue $Match.result @("awayGoals", "awayScore", "away") }
    if (-not $status) { $status = [string](Get-FirstNonEmptyValue $Match.result @("status", "matchStatus")) }
  }

  if ($null -eq $homeGoals -or $null -eq $awayGoals) {
    return $null
  }

  return [pscustomobject]@{
    homeGoals = [int]$homeGoals
    awayGoals = [int]$awayGoals
    status = if ($status) { $status } else { "Finished" }
    source = "sporttery-live-api"
  }
}

if (-not $OutFile) {
  $OutFile = Join-Path (Get-RootDir) ("data\" + $Date + ".json")
}

if ((Test-Path $OutFile) -and -not $Force -and -not $MergeExisting) {
  Write-Host "Data file already exists, keeping current file: $OutFile"
  exit 0
}

$targetDate = Get-TargetDateText $Date
$headers = @{
  "User-Agent" = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
  "Referer" = "https://m.sporttery.cn/mjc/jsq/zqzjq/"
  "Origin" = "https://m.sporttery.cn"
  "Accept" = "application/json, text/plain, */*"
  "Accept-Language" = "zh-CN,zh;q=0.9,en;q=0.8"
}
$apiUrl = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c&poolCode=$PoolCode"

Write-Host "Fetching Sporttery API: $apiUrl"
$response = Invoke-WebRequest -UseBasicParsing -Uri $apiUrl -Headers $headers
$payload = $response.Content | ConvertFrom-Json

if ([string]$payload.errorCode -ne "0" -or -not $payload.value.matchInfoList) {
  throw "Sporttery API returned no usable match data."
}

$existingMatchMap = Get-ExistingMatchMap $OutFile
$matchList = New-Object System.Collections.Generic.List[object]

foreach ($group in $payload.value.matchInfoList) {
  foreach ($match in $group.subMatchList) {
    if ($match.matchDate -ne $targetDate) {
      continue
    }

    $goalPick = Get-TopGoalsPrediction $match.ttg
    $lean = Get-ResultLean $match.had
    $scorePick = Get-ScorePrediction -GoalLabel $goalPick.totalGoals -Lean $lean

    $matchCode = [string]$match.matchNum
    $matchCodeMatch = [regex]::Match([string]$match.matchNumStr, "(\d{3})$")
    if ($matchCodeMatch.Success) {
      $matchCode = $matchCodeMatch.Groups[1].Value
    }

    $existingMatch = $null
    if ($existingMatchMap.ContainsKey([string]$match.matchId)) {
      $existingMatch = $existingMatchMap[[string]$match.matchId]
    }

    $leanText = switch ($lean) {
      "home" { "主胜" }
      "draw" { "平局" }
      "away" { "客胜" }
      default { $lean }
    }
    $review = "基于体彩实时赔率自动生成：总进球低位倾向 $($goalPick.totalGoals) 球，胜平负倾向 $leanText。"
    if ($existingMatch -and $existingMatch.review -and ($existingMatch.review -notmatch '^Auto-generated from Sporttery live odds\.')) {
      $review = $existingMatch.review
    }

    $resultData = Get-LiveResultFromMatch $match
    if (-not $resultData -and $existingMatch -and $existingMatch.result) {
      $resultData = $existingMatch.result
    }

    $matchList.Add([pscustomobject]@{
      id = $matchCode
      matchNumStr = $match.matchNumStr
      matchId = [string]$match.matchId
      businessDate = $match.businessDate
      league = $match.leagueAllName
      leagueCode = $match.leagueCode
      leagueId = $match.leagueId
      groupName = $match.groupName
      kickoff = "$($match.matchDate) $($match.matchTime)"
      matchDate = $match.matchDate
      matchTime = $match.matchTime
      matchStatus = $match.matchStatus
      sellStatus = $match.sellStatus
      taxDateNo = $match.taxDateNo
      isHot = [bool]$match.isHot
      home = $match.homeTeamAllName
      homeCode = $match.homeTeamCode
      homeAbbr = $match.homeTeamAbbName
      homeRank = $match.homeRank
      away = $match.awayTeamAllName
      awayCode = $match.awayTeamCode
      awayAbbr = $match.awayTeamAbbName
      awayRank = $match.awayRank
      venue = $match.remark
      prediction = [pscustomobject]@{
        totalGoals = if ($existingMatch -and $existingMatch.prediction.totalGoals) { $existingMatch.prediction.totalGoals } else { $goalPick.totalGoals }
        scores = if ($existingMatch -and $existingMatch.prediction.scores) { @($existingMatch.prediction.scores) } else { @($scorePick.scores) }
        upset = if ($existingMatch -and $existingMatch.prediction.upset) { $existingMatch.prediction.upset } else { $scorePick.upset }
        confidence = if ($existingMatch -and $existingMatch.prediction.confidence) { $existingMatch.prediction.confidence } else { $goalPick.confidence }
        candidates = @($goalPick.candidates)
      }
      result = $resultData
      review = $review
      postReview = if ($existingMatch -and $existingMatch.postReview) { $existingMatch.postReview } else { $null }
      odds = [pscustomobject]@{
        had = if ($match.had) {
          [pscustomobject]@{
            home = $match.had.h
            draw = $match.had.d
            away = $match.had.a
            updatedAt = "$($match.had.updateDate) $($match.had.updateTime)"
          }
        } else {
          $null
        }
        ttg = if ($match.ttg) {
          [pscustomobject]@{
            s0 = $match.ttg.s0
            s1 = $match.ttg.s1
            s2 = $match.ttg.s2
            s3 = $match.ttg.s3
            s4 = $match.ttg.s4
            s5 = $match.ttg.s5
            s6 = $match.ttg.s6
            s7 = $match.ttg.s7
            updatedAt = "$($match.ttg.updateDate) $($match.ttg.updateTime)"
          }
        } else {
          $null
        }
      }
    })
  }
}

if ($matchList.Count -eq 0) {
  throw "No Sporttery matches found for $targetDate."
}

$output = [ordered]@{
  date = $Date
  dateText = $targetDate
  source = "sporttery-live-api"
  fetchedAt = (Get-Date).ToString("s")
  lastUpdateTime = $payload.value.lastUpdateTime
  apiPoolCode = $PoolCode
  matches = @($matchList.ToArray())
}

$outDir = Split-Path -Parent $OutFile
if (-not (Test-Path $outDir)) {
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

[pscustomobject]$output | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $OutFile
Write-Host "Saved Sporttery data to $OutFile"
