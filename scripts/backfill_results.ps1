param(
  [string]$Date = (Get-Date -Format "yyyyMMdd"),
  [string]$DataFile = ""
)

$ErrorActionPreference = "Stop"

function Get-RootDir {
  return (Split-Path -Parent $PSScriptRoot)
}

function Get-ApiHeaders {
  return @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    "Accept" = "application/json, text/plain, */*"
    "Accept-Language" = "zh-CN,zh;q=0.9,en;q=0.8"
  }
}

function Get-ConfiguredResultSources {
  $sources = New-Object System.Collections.Generic.List[object]
  $sources.Add([pscustomobject]@{
    name = "api-football"
    url = "https://www.api-football.com/"
    role = "primary-live-score"
    enabled = [bool]$env:API_FOOTBALL_KEY
    note = "Fixtures/status/events/statistics; requires API_FOOTBALL_KEY."
  })
  $sources.Add([pscustomobject]@{
    name = "football-data"
    url = "https://www.football-data.org/"
    role = "settlement-backup"
    enabled = [bool]$env:FOOTBALL_DATA_TOKEN
    note = "Matches/scores/standings; requires FOOTBALL_DATA_TOKEN."
  })
  $sources.Add([pscustomobject]@{
    name = "serpapi-google"
    url = "https://serpapi.com/search?engine=google"
    role = "google-sports-card-fallback"
    enabled = [bool]$env:SERPAPI_KEY
    note = "Google sports result card fallback; requires SERPAPI_KEY."
  })
  $sources.Add([pscustomobject]@{
    name = "thesportsdb"
    url = "https://www.thesportsdb.com/"
    role = "metadata-and-livescore-fallback"
    enabled = [bool]$env:THESPORTSDB_KEY
    note = "Team/event metadata and premium livescore; requires THESPORTSDB_KEY for keyed access."
  })
  $sources.Add([pscustomobject]@{
    name = "worldcup26-ir"
    url = "https://worldcup26.ir/get/games"
    role = "world-cup-schedule-score-mirror"
    enabled = $true
    note = "World Cup 2026 schedule/score mirror; use only with a second source for settlement."
  })
  return $sources
}

function Write-ResultSourcePlan {
  $sources = Get-ConfiguredResultSources
  Write-Host "Configured result source plan:"
  foreach ($source in $sources) {
    $state = if ($source.enabled) { "enabled" } else { "waiting-for-key" }
    Write-Host " - $($source.name) [$state]: $($source.role) - $($source.url)"
  }
}

function Get-ScoreboardMapFromEspn {
  param([string]$CompactDate)

  $url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=$CompactDate"
  $response = Invoke-RestMethod -Uri $url -Headers (Get-ApiHeaders)
  $map = @{}

  foreach ($event in @($response.events)) {
    $competition = @($event.competitions)[0]
    if (-not $competition) {
      continue
    }

    $statusType = $competition.status.type
    $completed = $false
    if ($statusType) {
      $completed = [bool]$statusType.completed -or [string]$statusType.state -eq "post"
    }

    $homeTeamEntry = $competition.competitors | Where-Object { $_.homeAway -eq "home" } | Select-Object -First 1
    $awayTeamEntry = $competition.competitors | Where-Object { $_.homeAway -eq "away" } | Select-Object -First 1
    if (-not $homeTeamEntry -or -not $awayTeamEntry) {
      continue
    }

    $homeCode = [string]$homeTeamEntry.team.abbreviation
    $awayCode = [string]$awayTeamEntry.team.abbreviation
    if (-not $homeCode -or -not $awayCode) {
      continue
    }

    $item = [pscustomobject]@{
      homeCode = $homeCode
      awayCode = $awayCode
      homeGoals = if ($homeTeamEntry.score -match '^\d+$') { [int]$homeTeamEntry.score } else { $null }
      awayGoals = if ($awayTeamEntry.score -match '^\d+$') { [int]$awayTeamEntry.score } else { $null }
      status = if ($statusType) { [string]$statusType.description } else { "" }
      completed = $completed
      source = "espn-scoreboard"
      eventName = [string]$event.name
    }

    $map["$homeCode|$awayCode"] = $item
  }

  return $map
}

if (-not $DataFile) {
  $DataFile = Join-Path (Get-RootDir) ("data\" + $Date + ".json")
}

if (-not (Test-Path $DataFile)) {
  throw "Missing data file: $DataFile"
}

$payload = Get-Content -Raw -Encoding UTF8 $DataFile | ConvertFrom-Json
$updated = $false
$backfillSummary = New-Object System.Collections.Generic.List[string]

Write-ResultSourcePlan

# First trust any official result fields already present in the stored match objects.
foreach ($match in @($payload.matches)) {
  if ($match.result -and $null -ne $match.result.homeGoals -and $null -ne $match.result.awayGoals) {
    continue
  }
}

try {
  $espnMap = Get-ScoreboardMapFromEspn -CompactDate $Date
  foreach ($match in @($payload.matches)) {
    if ($match.result -and $null -ne $match.result.homeGoals -and $null -ne $match.result.awayGoals) {
      continue
    }

    $key = "$([string]$match.homeCode)|$([string]$match.awayCode)"
    if (-not $espnMap.ContainsKey($key)) {
      continue
    }

    $espnResult = $espnMap[$key]
    if ($null -eq $espnResult.homeGoals -or $null -eq $espnResult.awayGoals) {
      continue
    }

    $match | Add-Member -NotePropertyName result -NotePropertyValue ([pscustomobject]@{
      homeGoals = $espnResult.homeGoals
      awayGoals = $espnResult.awayGoals
      status = if ($espnResult.completed) { "Finished" } else { $espnResult.status }
      source = $espnResult.source
    }) -Force
    $updated = $true
    $backfillSummary.Add("$($match.home) vs $($match.away): $($espnResult.homeGoals):$($espnResult.awayGoals) from $($espnResult.source)")
  }
}
catch {
  Write-Host "ESPN fallback unavailable: $($_.Exception.Message)"
}

if ($updated) {
  $payload | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $DataFile
  Write-Host "Backfilled results:"
  $backfillSummary | ForEach-Object { Write-Host $_ }
}
else {
  Write-Host "No result backfill changes for $Date"
}
