param(
  [string]$DataFile,
  [string]$ScheduleFile = "",
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
if (-not $DataFile) {
  throw "DataFile is required."
}

if (-not (Test-Path $DataFile)) {
  throw "Missing data file: $DataFile"
}

if (-not $ScheduleFile) {
  $scheduleCandidate = Get-ChildItem -Path $root -File |
    Where-Object { $_.Extension -eq ".xlsx" -and $_.Name -notlike "~$*" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if ($scheduleCandidate) {
    $ScheduleFile = $scheduleCandidate.FullName
  }
}

if (-not $ScheduleFile -or -not (Test-Path $ScheduleFile)) {
  throw "Missing schedule workbook."
}

$pythonExe = "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path $pythonExe)) {
  throw "Bundled Python not found: $pythonExe"
}

$env:WORLD_CUP_DATA_FILE = (Resolve-Path $DataFile).Path
$env:WORLD_CUP_SCHEDULE_FILE = (Resolve-Path $ScheduleFile).Path

$resultJson = @'
import json
import os
from datetime import datetime
from openpyxl import load_workbook

data_file = os.environ["WORLD_CUP_DATA_FILE"]
schedule_file = os.environ["WORLD_CUP_SCHEDULE_FILE"]

with open(data_file, "r", encoding="utf-8-sig") as f:
    payload = json.load(f)

wb = load_workbook(schedule_file, data_only=True)
ws = wb[wb.sheetnames[0]]
rows = list(ws.iter_rows(values_only=True))

schedule = []
for row in rows[1:]:
    vals = [("" if v is None else str(v).strip()) for v in row[:5]]
    if len(vals) < 5 or not vals[1] or not vals[2]:
        continue
    schedule.append({
        "group": vals[0],
        "home": vals[1],
        "away": vals[2],
        "localKickoff": vals[3],
        "beijingKickoff": vals[4],
    })

def normalize_dt(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    return value[:16]

def parse_dt(value: str):
    normalized = normalize_dt(value)
    if not normalized:
        return None
    try:
        return datetime.strptime(normalized, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

changes = []
unmatched = []

for match in payload.get("matches", []):
    kickoff = normalize_dt(str(match.get("kickoff", "")))
    home = str(match.get("home", "")).strip()
    away = str(match.get("away", "")).strip()

    candidates = [
        item for item in schedule
        if item["home"] == home and normalize_dt(item["beijingKickoff"]) == kickoff
    ]
    basis = "home+kickoff"

    if len(candidates) != 1:
        candidates = [
            item for item in schedule
            if item["home"] == home and item["away"] == away
        ]
        basis = "home+away"

    if len(candidates) != 1 and kickoff:
        candidates = [
            item for item in schedule
            if normalize_dt(item["beijingKickoff"]) == kickoff
        ]
        basis = "kickoff-only"

    if len(candidates) != 1:
        candidates = [
            item for item in schedule
            if item["home"] == home
        ]
        basis = "home-only"

    if len(candidates) > 1 and kickoff:
        kickoff_dt = parse_dt(kickoff)
        if kickoff_dt is not None:
            dated = []
            for item in candidates:
                item_dt = parse_dt(item["beijingKickoff"])
                if item_dt is not None:
                    dated.append((abs((item_dt - kickoff_dt).total_seconds()), item))
            if dated:
                dated.sort(key=lambda x: x[0])
                if len(dated) == 1 or dated[0][0] < dated[1][0]:
                    candidates = [dated[0][1]]
                    basis = "home+nearest-kickoff"

    if len(candidates) != 1:
        unmatched.append({
            "id": match.get("id"),
            "home": home,
            "away": away,
            "kickoff": kickoff,
        })
        match["scheduleCheck"] = {
            "status": "unmatched",
            "checkedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scheduleFile": os.path.basename(schedule_file),
        }
        continue

    picked = candidates[0]
    old = {
        "group": match.get("group", ""),
        "home": match.get("home", ""),
        "away": match.get("away", ""),
        "kickoff": match.get("kickoff", ""),
        "localKickoff": match.get("localKickoff", ""),
    }

    match["group"] = picked["group"]
    match["home"] = picked["home"]
    match["away"] = picked["away"]
    match["kickoff"] = normalize_dt(picked["beijingKickoff"]) + ":00"
    match["localKickoff"] = normalize_dt(picked["localKickoff"]) + ":00"
    match["scheduleSource"] = os.path.basename(schedule_file)
    match["venue"] = picked["group"] + "\u8d5b\u7a0b\u57fa\u51c6\uff0c\u5df2\u6309\u8d5b\u7a0b\u8868\u6821\u9a8c\uff1b\u9875\u9762\u4ecd\u6309\u4e2d\u7acb\u573a\u4e16\u754c\u676f\u5c0f\u7ec4\u8d5b\u6a21\u578b\u5904\u7406"
    match["scheduleCheck"] = {
        "status": "matched",
        "basis": basis,
        "checkedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scheduleFile": os.path.basename(schedule_file),
    }

    new = {
        "group": match.get("group", ""),
        "home": match.get("home", ""),
        "away": match.get("away", ""),
        "kickoff": match.get("kickoff", ""),
        "localKickoff": match.get("localKickoff", ""),
    }

    diff = {k: {"old": old[k], "new": new[k]} for k in old if old[k] != new[k]}
    if diff:
        changes.append({
            "id": match.get("id"),
            "basis": basis,
            "diff": diff,
        })

with open(data_file, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "scheduleFile": os.path.basename(schedule_file),
    "changeCount": len(changes),
    "changes": changes,
    "unmatchedCount": len(unmatched),
    "unmatched": unmatched,
}, ensure_ascii=False))
'@ | & $pythonExe -

if (-not $resultJson) {
  throw "Schedule sync returned no result."
}

$result = $resultJson | ConvertFrom-Json

if (-not $Quiet) {
  Write-Host "Schedule sync file: $($result.scheduleFile)"
  Write-Host "Matched updates: $($result.changeCount)"
  if ($result.changeCount -gt 0) {
    foreach ($item in @($result.changes)) {
      $parts = @()
      foreach ($prop in $item.diff.PSObject.Properties) {
        $parts += ("{0}: {1} -> {2}" -f $prop.Name, $prop.Value.old, $prop.Value.new)
      }
      Write-Host ("  [{0}] {1}" -f $item.id, ($parts -join "; "))
    }
  }
  if ($result.unmatchedCount -gt 0) {
    Write-Host "Unmatched rows: $($result.unmatchedCount)"
  }
}
