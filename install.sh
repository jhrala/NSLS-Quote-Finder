#!/usr/bin/env bash
# NSLS Speaker Broadcast Quote Search — Installer (Mac/Linux)
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUOTES_DB="$REPO_DIR/quotes.json"
COMMANDS_DIR="$HOME/.claude/commands"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  NSLS Speaker Broadcast Quote Search — Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Repo:          $REPO_DIR"
echo "  Quotes DB:     $QUOTES_DB"
echo "  Commands dir:  $COMMANDS_DIR"
echo ""

# Check for existing commands and warn
if [ -f "$COMMANDS_DIR/find-quotes.md" ]; then
    echo -e "${YELLOW}⚠️  Existing /find-quotes command found. It will be overwritten.${NC}"
    echo ""
fi

# Remove old /update-quotes command if present from a previous install
if [ -f "$COMMANDS_DIR/update-quotes.md" ]; then
    rm "$COMMANDS_DIR/update-quotes.md"
    echo -e "${YELLOW}ℹ️  Removed old /update-quotes command (replaced by extract_quotes.py).${NC}"
    echo ""
fi

# Create ~/.claude/commands if it doesn't exist
mkdir -p "$COMMANDS_DIR"

# Install commands — substitute {{QUOTES_DB_PATH}} with the real path
sed "s|{{QUOTES_DB_PATH}}|$QUOTES_DB|g" "$REPO_DIR/commands/find-quotes.md" > "$COMMANDS_DIR/find-quotes.md"

echo -e "${GREEN}✓ Installed /find-quotes${NC}"

# Create empty quotes.json if it doesn't exist yet
if [ ! -f "$QUOTES_DB" ]; then
    echo "[]" > "$QUOTES_DB"
    echo -e "${GREEN}✓ Created empty quotes database at $QUOTES_DB${NC}"
else
    QUOTE_COUNT=$(python3 -c "import json,sys; data=json.load(open('$QUOTES_DB')); print(len(data))" 2>/dev/null || echo "?")
    echo -e "${GREEN}✓ Quotes database already exists ($QUOTE_COUNT quotes)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}  Installation complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Commands installed:"
echo "    /find-quotes [query]   — Search quotes by topic or theme"
echo ""
echo "  To add new quotes:"
echo "    python3 extract_quotes.py path/to/file.srt --speaker \"Name\" --date 2024"
echo "    python3 extract_quotes.py transcripts/     (batch process a folder)"
echo ""
echo "  Prerequisites:"
echo "    • Claude Code (claude.ai/code)"
echo "    • Python 3.9+ (for extract_quotes.py)"
echo ""
echo "  ⚡  Restart Claude Code to pick up the new commands."
echo ""
