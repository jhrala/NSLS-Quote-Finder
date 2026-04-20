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
if [ -f "$COMMANDS_DIR/find-quotes.md" ] || [ -f "$COMMANDS_DIR/update-quotes.md" ]; then
    echo -e "${YELLOW}⚠️  Existing quote search commands found. They will be overwritten.${NC}"
    echo ""
fi

# Create ~/.claude/commands if it doesn't exist
mkdir -p "$COMMANDS_DIR"

# Install commands — substitute {{QUOTES_DB_PATH}} with the real path
sed "s|{{QUOTES_DB_PATH}}|$QUOTES_DB|g" "$REPO_DIR/commands/find-quotes.md" > "$COMMANDS_DIR/find-quotes.md"
sed "s|{{QUOTES_DB_PATH}}|$QUOTES_DB|g" "$REPO_DIR/commands/update-quotes.md" > "$COMMANDS_DIR/update-quotes.md"

echo -e "${GREEN}✓ Installed /find-quotes${NC}"
echo -e "${GREEN}✓ Installed /update-quotes${NC}"

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
echo "    /update-quotes         — Import new broadcasts from Google Drive"
echo ""
echo "  Prerequisites:"
echo "    • Claude Code (claude.ai/code)"
echo "    • Google Drive MCP connected and authenticated"
echo "      → See README.md for setup instructions"
echo ""
echo "  ⚡  Restart Claude Code to pick up the new commands."
echo ""
