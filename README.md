# NSLS Speaker Broadcast Quote Search

Search hundreds of Speaker Broadcast quotes using natural language — right inside Claude Code.

```
/find-quotes quotes that talk positively about the NSLS
/find-quotes something inspiring about overcoming failure
/find-quotes anything from Jim Cramer about investing
```

---

## How It Works

Two slash commands power the tool:

| Command | What it does |
|---|---|
| `/find-quotes [query]` | Searches the quote database by meaning and theme, not just keywords |
| `/update-quotes` | Pulls new broadcast transcripts from Google Drive and adds extracted quotes to the database |

Quotes are stored in `quotes.json` in this repo — committed to git so the whole team shares one library.

> **New installs:** `quotes.json` comes pre-loaded with all existing quotes. You can start searching immediately with `/find-quotes` — no ingestion needed.
>
> **`/update-quotes` is only needed** when a new Speaker Broadcast transcript is added to the Drive folder. One person runs it, commits the updated `quotes.json`, and everyone else gets the new quotes with a `git pull`.

---

## Prerequisites

Before installing, you need:

1. **Claude Code** — [claude.ai/code](https://claude.ai/code)
2. **Google Drive MCP** connected and authenticated with a Google account that has access to the NSLS Speaker Broadcast Drive folder

### Setting Up the Google Drive MCP

The Google Drive MCP lets Claude Code read files from your Google Drive. Here's how to connect it:

1. Open Claude Code settings: press `Cmd+,` (Mac) or `Ctrl+,` (Windows)
2. Go to **Extensions** → **MCP Servers**
3. Add the Google Drive MCP — search for it in the MCP marketplace or add it manually:
   ```json
   {
     "mcpServers": {
       "google-drive": {
         "command": "npx",
         "args": ["-y", "@google/mcp-server-gdrive"]
       }
     }
   }
   ```
4. Restart Claude Code and authenticate with your Google account when prompted
5. Make sure you're signed in with an account that has **Viewer access** to the NSLS Speaker Broadcast folder

> **Can't access the Drive folder?** Ask Josh Hrala to share the folder with your Google account.

---

## Installation

### Mac / Linux

Open Terminal and run:

```bash
git clone https://github.com/jhrala/NSLS-Quote-Finder.git
cd NSLS-Quote-Finder
chmod +x install.sh
./install.sh
```

### Windows

Open PowerShell and run:

```powershell
git clone https://github.com/jhrala/NSLS-Quote-Finder.git
cd NSLS-Quote-Finder
.\install.ps1
```

> **Windows note:** If you see a security error running the script, run this first to allow local scripts:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then re-run `.\install.ps1`.

The installer:
- Copies `/find-quotes` and `/update-quotes` into your global `~/.claude/commands/` folder
- Points the commands at the `quotes.json` file in your cloned repo
- Leaves any existing quotes untouched

**After installing, restart Claude Code** to pick up the new commands.

---

## Usage

### Search for quotes

```
/find-quotes [your query]
```

Examples:
```
/find-quotes quotes about leadership and resilience
/find-quotes something I could use in a fundraising email
/find-quotes quotes that mention the NSLS by name
/find-quotes anything about failure and learning from mistakes
/find-quotes Jim Cramer quotes about the stock market
```

Claude will return up to 8 ranked results, each with the speaker name, episode, and an explanation of why it matches your query.

### Add new broadcast transcripts

```
/update-quotes
```

This reads any new `.srt` transcript files from the NSLS Speaker Broadcast Google Drive folder, extracts quotable statements using Claude, and adds them to `quotes.json`. It skips files that have already been ingested.

After ingesting, commit and push `quotes.json` so your teammates get the new quotes:

```bash
git add quotes.json
git commit -m "Add quotes from [Speaker Name] broadcast"
git push
```

---

## Keeping Quotes Up to Date

When a new Speaker Broadcast is recorded:

1. The transcript `.srt` file gets added to the Google Drive folder
2. Any team member runs `/update-quotes` in Claude Code
3. They commit and push the updated `quotes.json`
4. Everyone else runs `git pull` to get the new quotes

---

## Manually Editing Quotes

`quotes.json` is a plain JSON array. You can open it in any text editor to fix a quote, update a speaker name, or remove an entry. Each quote looks like:

```json
{
  "id": "2026-04-20-001",
  "speaker": "Jim Cramer",
  "text": "You have to be willing to fail...",
  "episode": "NSLS Speaker Broadcast — Jim Cramer",
  "date": "2024",
  "sourceFile": "NSLS Speaker Broadcast - Jim Cramer.srt",
  "themes": ["failure", "investing", "resilience"],
  "addedDate": "2026-04-20"
}
```

See `quotes.schema.json` for a full description of each field.

---

## Re-installing / Updating

To update after pulling new changes from the repo, run `git pull` then re-run the installer:

**Mac/Linux:**
```bash
git pull
./install.sh
```

**Windows:**
```powershell
git pull
.\install.ps1
```

This overwrites the commands in `~/.claude/commands/` with the latest versions.

---

## Troubleshooting

**Commands don't appear after installing**
→ Restart Claude Code completely (quit and reopen).

**`/update-quotes` can't find any files**
→ Check that your Google Drive MCP is connected: type `/help` in Claude Code and look for Drive-related tools. If missing, re-add the MCP and authenticate.

**`/update-quotes` skips all files**
→ All transcripts in the Drive folder have already been ingested. Add new `.srt` files to the folder and try again.

**A quote has wrong attribution or garbled text**
→ Edit `quotes.json` directly, fix the entry, and commit the fix.

**Getting a permissions error on the Drive folder**
→ Ask Josh Hrala to share the NSLS Speaker Broadcast Drive folder with your Google account (Viewer access is enough).
