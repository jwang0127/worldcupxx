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

$payload = Get-Content -Raw $DataFile | ConvertFrom-Json
$updated = $false
$backfillSummary = New-Object System.Collections.Generic.List[string]

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
