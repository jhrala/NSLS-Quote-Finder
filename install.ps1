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

# Warn if /find-quotes already exists
if (Test-Path (Join-Path $CommandsDir "find-quotes.md")) {
    Write-Host "  WARNING: Existing /find-quotes command found. It will be overwritten." -ForegroundColor Yellow
    Write-Host ""
}

# Remove old /update-quotes command if present from a previous install
$OldUpdateCmd = Join-Path $CommandsDir "update-quotes.md"
if (Test-Path $OldUpdateCmd) {
    Remove-Item $OldUpdateCmd -Force
    Write-Host "  INFO: Removed old /update-quotes command (replaced by extract_quotes.py)." -ForegroundColor Yellow
    Write-Host ""
}

# Create ~/.claude/commands if it doesn't exist
New-Item -ItemType Directory -Force -Path $CommandsDir | Out-Null

# Install /find-quotes -- substitute {{QUOTES_DB_PATH}} with the real path
$FindQuotesTemplate = Get-Content (Join-Path $RepoDir "commands\find-quotes.md") -Raw -Encoding utf8
$FindQuotesTemplate = $FindQuotesTemplate -replace [regex]::Escape("{{QUOTES_DB_PATH}}"), $QuotesDb
[System.IO.File]::WriteAllText((Join-Path $CommandsDir "find-quotes.md"), $FindQuotesTemplate, [System.Text.Encoding]::UTF8)
Write-Host "  [OK] Installed /find-quotes" -ForegroundColor Green

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
Write-Host ""
Write-Host "  To add new quotes:"
Write-Host "    python extract_quotes.py path\to\file.srt --speaker `"Name`" --date 2024"
Write-Host "    python extract_quotes.py transcripts\      (batch process a folder)"
Write-Host ""
Write-Host "  Prerequisites:"
Write-Host "    - Claude Code (claude.ai/code)"
Write-Host "    - Python 3.9+ (for extract_quotes.py)"
Write-Host ""
Write-Host "  Restart Claude Code to pick up the new commands."
Write-Host ""
