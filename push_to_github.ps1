$ErrorActionPreference = "Stop"

$repo = "https://github.com/jwang0127/worldcupxx.git"
$workTree = $PSScriptRoot
$gitRoot = Join-Path $env:TEMP "worldcupxx-git"
$gitDir = Join-Path $gitRoot ".git"
$git = "C:\Program Files\Git\cmd\git.exe"

if (-not (Test-Path $git)) {
  throw "Git was not found at: $git"
}

if (-not (Test-Path $gitRoot)) {
  New-Item -ItemType Directory -Force -Path $gitRoot | Out-Null
}

if (-not (Test-Path $gitDir)) {
  & $git --git-dir="$gitDir" --work-tree="$workTree" init
}

try {
  & $git --git-dir="$gitDir" --work-tree="$workTree" remote get-url origin | Out-Null
}
catch {
  & $git --git-dir="$gitDir" --work-tree="$workTree" remote add origin $repo
}

& $git --git-dir="$gitDir" --work-tree="$workTree" config user.name "Codex"
& $git --git-dir="$gitDir" --work-tree="$workTree" config user.email "codex@example.local"
& $git --git-dir="$gitDir" --work-tree="$workTree" add index.html
& $git --git-dir="$gitDir" --work-tree="$workTree" add model_state.json
if (Test-Path (Join-Path $workTree "data")) {
  & $git --git-dir="$gitDir" --work-tree="$workTree" add (Join-Path $workTree "data")
}
if (Test-Path (Join-Path $workTree "scripts")) {
  & $git --git-dir="$gitDir" --work-tree="$workTree" add (Join-Path $workTree "scripts")
}
& $git --git-dir="$gitDir" --work-tree="$workTree" rm -r --cached --ignore-unmatch (Join-Path $workTree "scripts\__pycache__")
Get-ChildItem -Path $workTree -Recurse -Filter "*.html" |
  Where-Object { $_.FullName -notmatch "\\.git\\" } |
  ForEach-Object {
    & $git --git-dir="$gitDir" --work-tree="$workTree" add $_.FullName
  }
Get-ChildItem -Path $workTree -Recurse -Filter "*.md" |
  Where-Object { $_.FullName -notmatch "\\.git\\" } |
  ForEach-Object {
    & $git --git-dir="$gitDir" --work-tree="$workTree" add $_.FullName
  }
Get-ChildItem -Path $workTree -Recurse -Filter "*.json" |
  Where-Object { $_.FullName -notmatch "\\.git\\" } |
  ForEach-Object {
    & $git --git-dir="$gitDir" --work-tree="$workTree" add $_.FullName
  }
Get-ChildItem -Path $workTree -Recurse -Filter "*.xlsx" |
  Where-Object { $_.FullName -notmatch "\\.git\\" } |
  ForEach-Object {
    & $git --git-dir="$gitDir" --work-tree="$workTree" add $_.FullName
  }
& $git --git-dir="$gitDir" --work-tree="$workTree" add -u

& $git --git-dir="$gitDir" --work-tree="$workTree" diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
  & $git --git-dir="$gitDir" --work-tree="$workTree" commit -m "Update World Cup prediction pages"
}
else {
  Write-Host "No local changes to commit."
}

& $git --git-dir="$gitDir" --work-tree="$workTree" branch -M main
& $git --git-dir="$gitDir" --work-tree="$workTree" fetch origin main
if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }
& $git --git-dir="$gitDir" --work-tree="$workTree" merge --allow-unrelated-histories --no-edit origin/main
if ($LASTEXITCODE -ne 0) { throw "git merge failed; please resolve conflicts and run this script again" }
& $git --git-dir="$gitDir" --work-tree="$workTree" push -u origin main
if ($LASTEXITCODE -ne 0) { throw "git push failed" }

Write-Host "Done: https://jwang0127.github.io/worldcupxx/"
