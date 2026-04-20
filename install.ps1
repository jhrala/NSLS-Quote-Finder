# NSLS Speaker Broadcast Quote Search -- Installer (Windows)
# Run from the repo root: .\install.ps1

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$QuotesDb = Join-Path $RepoDir "quotes.json"
$CommandsDir = Join-Path $env:USERPROFILE ".claude\commands"

Write-Host ""
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "  NSLS Speaker Broadcast Quote Search - Installer" -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Repo:          $RepoDir"
Write-Host "  Quotes DB:     $QuotesDb"
Write-Host "  Commands dir:  $CommandsDir"
Write-Host ""

# Warn if commands already exist
if ((Test-Path (Join-Path $CommandsDir "find-quotes.md")) -or (Test-Path (Join-Path $CommandsDir "update-quotes.md"))) {
    Write-Host "  WARNING: Existing quote search commands found. They will be overwritten." -ForegroundColor Yellow
    Write-Host ""
}

# Create ~/.claude/commands if it doesn't exist
New-Item -ItemType Directory -Force -Path $CommandsDir | Out-Null

# Install commands -- substitute {{QUOTES_DB_PATH}} with the real path
$FindQuotesTemplate = Get-Content (Join-Path $RepoDir "commands\find-quotes.md") -Raw -Encoding utf8
$FindQuotesTemplate = $FindQuotesTemplate -replace [regex]::Escape("{{QUOTES_DB_PATH}}"), $QuotesDb
[System.IO.File]::WriteAllText((Join-Path $CommandsDir "find-quotes.md"), $FindQuotesTemplate, [System.Text.Encoding]::UTF8)
Write-Host "  [OK] Installed /find-quotes" -ForegroundColor Green

$UpdateTemplate = Get-Content (Join-Path $RepoDir "commands\update-quotes.md") -Raw -Encoding utf8
$UpdateTemplate = $UpdateTemplate -replace [regex]::Escape("{{QUOTES_DB_PATH}}"), $QuotesDb
[System.IO.File]::WriteAllText((Join-Path $CommandsDir "update-quotes.md"), $UpdateTemplate, [System.Text.Encoding]::UTF8)
Write-Host "  [OK] Installed /update-quotes" -ForegroundColor Green

# Create empty quotes.json if it doesn't already exist
if (-not (Test-Path $QuotesDb)) {
    [System.IO.File]::WriteAllText($QuotesDb, "[]", [System.Text.Encoding]::UTF8)
    Write-Host "  [OK] Created empty quotes database" -ForegroundColor Green
} else {
    try {
        $quotes = Get-Content $QuotesDb -Raw | ConvertFrom-Json
        $count = $quotes.Count
        Write-Host "  [OK] Quotes database already exists ($count quotes)" -ForegroundColor Green
    } catch {
        Write-Host "  [OK] Quotes database already exists" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Commands installed:"
Write-Host "    /find-quotes [query]   - Search quotes by topic or theme"
Write-Host "    /update-quotes         - Import new broadcasts from Google Drive"
Write-Host ""
Write-Host "  Prerequisites:"
Write-Host "    - Claude Code (claude.ai/code)"
Write-Host "    - Google Drive MCP connected and authenticated"
Write-Host "      -> See README.md for setup instructions"
Write-Host ""
Write-Host "  Restart Claude Code to pick up the new commands."
Write-Host ""
