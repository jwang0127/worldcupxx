param(
  [string]$Date = (Get-Date -Format "yyyyMMdd")
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dataFile = Join-Path $root ("data\" + $Date + ".json")

if (-not (Test-Path $dataFile)) {
  throw "Missing data file: $dataFile"
}

function Get-TopGoalsPrediction {
  param(
    $Ttg,
    $Had = $null,
    $Hhad = $null
  )

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
  $topLabel = [string]$sorted[0].label
  $topOdd = [decimal]$sorted[0].value
  $gap = 0
  if ($sorted.Count -gt 1) {
    $gap = [math]::Round(([decimal]$sorted[1].value - [decimal]$sorted[0].value), 2)
  }

  $homeProb = 0.45
  $drawProb = 0.27
  $awayProb = 0.28
  if ($Had -and $Had.home -and $Had.draw -and $Had.away) {
    $rawHome = 1 / [decimal]$Had.home
    $rawDraw = 1 / [decimal]$Had.draw
    $rawAway = 1 / [decimal]$Had.away
    $sum = $rawHome + $rawDraw + $rawAway
    if ($sum -gt 0) {
      $homeProb = [double]($rawHome / $sum)
      $drawProb = [double]($rawDraw / $sum)
      $awayProb = [double]($rawAway / $sum)
    }
  }

  $favoriteProb = [math]::Max($homeProb, $awayProb)
  $favoriteStrong = $favoriteProb -ge 0.56
  $balancedMatch = [math]::Abs($homeProb - $awayProb) -le 0.12
  $drawPressure = $drawProb -ge 0.27
  if ($Hhad -and $Hhad.handicap) {
    $handicap = [string]$Hhad.handicap
    if ($handicap -match "^-2" -or $handicap -match "^\+2") {
      $favoriteStrong = $true
    }
  }

  if ($topLabel -eq "2" -and $sorted.Count -gt 1 -and [string]$sorted[1].label -eq "3" -and $gap -le 0.28 -and $favoriteStrong) {
    $topLabel = "3"
  }
  elseif ($topLabel -eq "3" -and $sorted.Count -gt 1 -and [string]$sorted[1].label -eq "2" -and $gap -le 0.22 -and ($balancedMatch -or $drawPressure)) {
    $topLabel = "2"
  }
  elseif ($topLabel -eq "1" -and $favoriteStrong -and $topOdd -le 4.9) {
    $topLabel = "2"
  }
  elseif ($topLabel -eq "4" -and $balancedMatch -and $drawPressure) {
    $topLabel = "3"
  }

  $confidence = "medium"
  if ($gap -ge 0.6) {
    $confidence = "high"
  }
  elseif ($gap -lt 0.2) {
    $confidence = "low"
  }
  if ($favoriteStrong -and $confidence -eq "medium" -and ($topLabel -eq "3" -or $topLabel -eq "4")) {
    $confidence = "high"
  }
  if ($balancedMatch -and $drawPressure -and $gap -lt 0.35) {
    $confidence = "low"
  }

  return @{
    totalGoals = $topLabel
    candidates = @($sorted | Select-Object -First ([Math]::Min(3, $sorted.Count)) | ForEach-Object { $_.label })
    confidence = $confidence
  }
}

function Get-ResultLean {
  param(
    $Had,
    $Hhad = $null
  )

  if (-not $Had -or -not $Had.home -or -not $Had.draw -or -not $Had.away) {
    return "home"
  }

  $items = @(
    @{ code = "home"; value = $Had.home },
    @{ code = "draw"; value = $Had.draw },
    @{ code = "away"; value = $Had.away }
  )
  $pick = ($items | Sort-Object { [decimal]$_.value } | Select-Object -First 1).code

  $rawHome = 1 / [decimal]$Had.home
  $rawDraw = 1 / [decimal]$Had.draw
  $rawAway = 1 / [decimal]$Had.away
  $sum = $rawHome + $rawDraw + $rawAway
  if ($sum -le 0) {
    return $pick
  }

  $homeProb = [double]($rawHome / $sum)
  $drawProb = [double]($rawDraw / $sum)
  $awayProb = [double]($rawAway / $sum)
  if ([math]::Abs($homeProb - $awayProb) -le 0.10 -and $drawProb -ge 0.28) {
    return "draw"
  }

  if ($Hhad -and $Hhad.home -and $Hhad.away) {
    $handicap = [string]$Hhad.handicap
    $hHome = [decimal]$Hhad.home
    $hAway = [decimal]$Hhad.away
    if ($handicap -match "^-1" -and $pick -eq "home" -and $hAway -lt $hHome -and $drawProb -ge 0.24) {
      return "home"
    }
    if ($handicap -match "^\+1" -and $pick -eq "away" -and $hHome -lt $hAway -and $drawProb -ge 0.24) {
      return "away"
    }
  }

  return $pick
}

function Convert-ToIntGoals {
  param([string]$Label)
  if ($Label -eq "7+") { return 7 }
  return [int]$Label
}

function Get-ScorePrediction {
  param(
    [string]$GoalLabel,
    [string]$Lean,
    $Had = $null,
    $Hhad = $null
  )

  $goals = Convert-ToIntGoals $GoalLabel
  $homeProb = 0.45
  $drawProb = 0.27
  $awayProb = 0.28
  if ($Had -and $Had.home -and $Had.draw -and $Had.away) {
    $rawHome = 1 / [decimal]$Had.home
    $rawDraw = 1 / [decimal]$Had.draw
    $rawAway = 1 / [decimal]$Had.away
    $sum = $rawHome + $rawDraw + $rawAway
    if ($sum -gt 0) {
      $homeProb = [double]($rawHome / $sum)
      $drawProb = [double]($rawDraw / $sum)
      $awayProb = [double]($rawAway / $sum)
    }
  }

  $favoriteProb = [math]::Max($homeProb, $awayProb)
  $favoriteStrong = $favoriteProb -ge 0.56
  $balancedMatch = [math]::Abs($homeProb - $awayProb) -le 0.12
  $drawPressure = $drawProb -ge 0.27
  if ($Hhad -and $Hhad.handicap) {
    $handicap = [string]$Hhad.handicap
    if ($handicap -match "^-2" -or $handicap -match "^\+2") {
      $favoriteStrong = $true
    }
  }

  switch ($Lean) {
    "draw" {
      switch ($goals) {
        0 { return @{ scores = @("0:0", "1:1"); upset = "1:0" } }
        1 { return @{ scores = @("0:0", "1:1"); upset = "1:0" } }
        2 { return @{ scores = @("1:1", "0:0"); upset = "1:0" } }
        3 { return @{ scores = @("2:2", "1:1"); upset = "2:1" } }
        4 { return @{ scores = @("2:2", "1:1"); upset = "3:1" } }
        default { return @{ scores = @("2:2", "3:3"); upset = "3:2" } }
      }
    }
    "away" {
      if ($drawPressure -and $goals -le 2) {
        return @{ scores = @("0:1", "1:1"); upset = "1:0" }
      }
      switch ($goals) {
        0 { return @{ scores = @("0:0", "0:1"); upset = "1:0" } }
        1 { return @{ scores = @("0:1", "1:1"); upset = "1:0" } }
        2 { return @{ scores = @("0:1", "0:2"); upset = "1:1" } }
        3 {
          if ($favoriteStrong) { return @{ scores = @("1:2", "0:3"); upset = "1:1" } }
          return @{ scores = @("0:2", "1:2"); upset = "1:1" }
        }
        4 { return @{ scores = @("1:3", "0:4"); upset = "2:2" } }
        default { return @{ scores = @("2:3", "1:4"); upset = "2:2" } }
      }
    }
    default {
      if ($drawPressure -and $goals -le 2) {
        return @{ scores = @("1:1", "1:0"); upset = "0:1" }
      }
      switch ($goals) {
        0 { return @{ scores = @("0:0", "1:0"); upset = "0:1" } }
        1 { return @{ scores = @("1:0", "1:1"); upset = "0:1" } }
        2 {
          if ($balancedMatch) { return @{ scores = @("1:1", "2:1"); upset = "0:1" } }
          return @{ scores = @("2:0", "2:1"); upset = "1:1" }
        }
        3 {
          if ($favoriteStrong) { return @{ scores = @("2:1", "3:0"); upset = "1:1" } }
          return @{ scores = @("2:1", "2:0"); upset = "1:2" }
        }
        4 { return @{ scores = @("3:1", "2:2"); upset = "1:2" } }
        default { return @{ scores = @("3:2", "4:1"); upset = "2:2" } }
      }
    }
  }
}

function Get-LeanText {
  param([string]$Lean)
  switch ($Lean) {
    "home" { return '主胜' }
    "draw" { return '平局' }
    "away" { return '客胜' }
    default { return $Lean }
  }
}

$payload = Get-Content -Raw -Encoding UTF8 $dataFile | ConvertFrom-Json

foreach ($match in @($payload.matches)) {
  $goalPick = Get-TopGoalsPrediction -Ttg $match.odds.ttg -Had $match.odds.had -Hhad $match.odds.hhad
  $lean = Get-ResultLean -Had $match.odds.had -Hhad $match.odds.hhad
  $scorePick = Get-ScorePrediction -GoalLabel $goalPick.totalGoals -Lean $lean -Had $match.odds.had -Hhad $match.odds.hhad
  $review = ('基于我们的量化规则重算：总进球主线 {0} 球，胜平负倾向 {1}，并加入平局压力、让球盘强弱和尾部修正。' -f $goalPick.totalGoals, (Get-LeanText $lean))

  $match.prediction = [pscustomobject]@{
    totalGoals = $goalPick.totalGoals
    scores = @($scorePick.scores)
    upset = $scorePick.upset
    confidence = $goalPick.confidence
    candidates = @($goalPick.candidates)
  }
  $match.review = $review
}

($payload | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $dataFile -Encoding UTF8
Write-Host ('Recalculated predictions for {0}' -f $Date)
