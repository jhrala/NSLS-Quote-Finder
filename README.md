# NSLS Speaker Broadcast Quote Search

Search 3,600+ quotes from NSLS Speaker Broadcasts — right inside Claude Code.

```
/find-quotes quotes that talk positively about the NSLS
/find-quotes something inspiring about overcoming failure
/find-quotes anything from Jim Cramer about investing
/find-quotes something I could use in a fundraising email
/find-quotes Kevin Hart quotes about resilience
```

---

## How It Works

One slash command powers the search:

| Command | What it does |
|---|---|
| `/find-quotes [query]` | Searches the quote database by meaning and theme, not just keywords |

Quotes are stored in `quotes.json` in this repo — committed to git so the whole team shares one library. Claude reads the file and ranks results by relevance to your query.

New quotes are added by the repo maintainer using the included Python scripts (no API calls, no AI, near-zero cost). The maintainer commits the updated `quotes.json` and the team gets new quotes with a `git pull`.

> **New installs:** `quotes.json` comes pre-loaded with 3,600+ quotes from 65 speakers. You can start searching immediately — no extra setup needed.

---

## Prerequisites

1. **Claude Code** — [claude.ai/code](https://claude.ai/code)
2. **Git** — to clone the repo
3. **Python 3.9+** — only needed by the maintainer to add new quotes

---

## Installation

**Mac / Linux:**
```bash
git clone https://github.com/jhrala/NSLS-Quote-Finder.git && cd NSLS-Quote-Finder && chmod +x install.sh && ./install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/jhrala/NSLS-Quote-Finder.git; cd NSLS-Quote-Finder; .\install.ps1
```

> **Windows note:** If you see a security error, run this first, then re-run the one-liner above:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

The installer copies the `/find-quotes` command into `~/.claude/commands/` and wires it up to the `quotes.json` file in your cloned repo.

**After installing, restart Claude Code** to pick up the new command, then search:

```
/find-quotes [your query]
```

---

## Usage

### Searching for quotes

Type `/find-quotes` followed by any natural-language query:

```
/find-quotes quotes about leadership and resilience
/find-quotes something I could use in a fundraising email
/find-quotes quotes that mention the NSLS by name
/find-quotes anything about failure and learning from mistakes
/find-quotes Jim Cramer quotes about the stock market
/find-quotes something funny from Kevin Hart
/find-quotes Oprah Winfrey on finding your purpose
```

Claude returns up to 8 ranked results, each with:
- Speaker name and episode
- Video timestamp (to find the moment in the footage)
- The full quote text
- A one-sentence explanation of why it matches

### How matching works

Search matches on **meaning and intent**, not just keywords. A quote about "bouncing back from setbacks" will match a query about "resilience" even if the word resilience never appears in the quote.

---

## Getting Updates

When the maintainer adds new quotes and pushes to the repo, pull to get them:

```bash
git pull
```

No need to re-run the installer — the command reads `quotes.json` directly from your cloned repo.

---

## Re-installing / Updating the Command

If a new version of the `/find-quotes` command is released:

**Mac / Linux:**
```bash
git pull
./install.sh
```

**Windows:**
```powershell
git pull
.\install.ps1
```

Then restart Claude Code.

---

## Troubleshooting

**`/find-quotes` doesn't appear after installing**
→ Restart Claude Code completely (quit and reopen).

**`/find-quotes` returns no results or says the database is empty**
→ Run `git pull` to make sure you have the latest `quotes.json`. If the file is still empty, contact the maintainer.

**A quote has wrong attribution or garbled text**
→ Let the maintainer know so they can fix it in `quotes.json` and push a correction.

---

---

# Maintainer Guide

> Everything below is for the person maintaining the quote database. Teammates only need the sections above.

---

## Adding New Speaker Broadcast Transcripts

### Single file

1. Download the `.txt` transcript from Google Drive
2. Place it in `srt_downloads/`
3. Run `bulk_ingest.py` (see below) — it will pick up any new files automatically

### Bulk processing (`bulk_ingest.py` — recommended)

`bulk_ingest.py` processes every `.txt` file in `srt_downloads/` in one pass. Files already in the database are automatically skipped.

```bash
# Mac / Linux
python3 bulk_ingest.py

# Windows
python bulk_ingest.py

# Preview what would be added without writing anything
python3 bulk_ingest.py --dry-run
```

Speaker metadata (full name, year) is looked up from the `SPEAKER_META` dictionary at the top of `bulk_ingest.py`. If a new speaker isn't in that dict, add them before running.

After running, commit and push:

```bash
git add quotes.json
git commit -m "Add quotes from [Speaker Name] broadcast"
git push
```

### Single file with `extract_quotes.py` (manual)

For a one-off file outside the `srt_downloads/` folder:

**Mac / Linux:**
```bash
python3 extract_quotes.py "path/to/NSLS_Speaker Broadcast_Name.srt" \
  --speaker "Full Name" \
  --episode "NSLS Speaker Broadcast — Full Name" \
  --date 2024 \
  --speaker-type speaker-broadcast
```

**Windows:**
```powershell
python extract_quotes.py "path\to\NSLS_Speaker Broadcast_Name.srt" `
  --speaker "Full Name" `
  --episode "NSLS Speaker Broadcast — Full Name" `
  --date 2024 `
  --speaker-type speaker-broadcast
```

### Adding student, advisor, or member quotes

```bash
python3 extract_quotes.py student_testimonial.srt \
  --speaker "Jane Smith" \
  --episode "Chapter Spotlight — Jane Smith" \
  --date 2024 \
  --speaker-type student
```

Valid `--speaker-type` values: `speaker-broadcast`, `student`, `advisor`, `member`

---

## extract_quotes.py Reference

```
python3 extract_quotes.py <path> [options]

Arguments:
  path                    SRT/TXT file or directory of files

Options:
  --speaker "Full Name"   Guest speaker name (skips interactive prompt)
  --episode "..."         Episode name (default: "NSLS Speaker Broadcast — {speaker}")
  --date "2024"           Broadcast year
  --speaker-type TYPE     One of: speaker-broadcast, student, advisor, member
                          (default: speaker-broadcast)
  --min-words N           Minimum words per quote (default: 30)
  --max-words N           Maximum words per quote before splitting (default: 200)
  --dry-run               Preview quotes without writing to database
```

---

## bulk_ingest.py Reference

```
python3 bulk_ingest.py [options]

Processes all .txt files in srt_downloads/ and adds new quotes to quotes.json.
Files whose sourceFile already exists in the database are skipped automatically.

Options:
  --dry-run               Preview without writing to database
  --min-words N           Minimum words per quote (default: 30)
  --max-words N           Maximum words per quote (default: 200)
```

---

## Manually Editing Quotes

`quotes.json` is a plain JSON array. Open it in any editor to fix a quote, update a speaker name, or remove an entry. Each entry looks like:

```json
{
  "id": "2026-04-30-001",
  "speaker": "Jim Cramer",
  "speakerType": "speaker-broadcast",
  "text": "You have to be willing to fail...",
  "episode": "NSLS Speaker Broadcast — Jim Cramer",
  "date": "2014",
  "timestamp": "00:15:32",
  "sourceFile": "NSLS_Speaker Broadcast_Jim Cramer.txt",
  "themes": ["failure", "investing", "resilience"],
  "addedDate": "2026-04-30"
}
```

See `quotes.schema.json` for a full description of every field.

---

## Maintainer Troubleshooting

**The script skips lines I expect it to catch**
→ Check if the host name appears as a speaker label in the transcript (e.g., `BRACY:`). Add it to `HOST_LABELS` in `extract_quotes.py` if missing.

**Need to re-process a file that was already ingested**
→ Remove all entries with that `sourceFile` from `quotes.json`, then re-run the script.

**A speaker's name is coming out wrong**
→ Check `SPEAKER_META` in `bulk_ingest.py`. The key must match the lowercase speaker portion of the filename exactly.
