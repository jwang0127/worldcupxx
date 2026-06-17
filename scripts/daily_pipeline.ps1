param(
  [string]$Date = (Get-Date -Format "yyyyMMdd"),
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "fetch_sporttery.ps1") -Date $Date -Force
& (Join-Path $PSScriptRoot "auto_update.ps1") -Date $Date -RefreshData -NoPush:$NoPush
