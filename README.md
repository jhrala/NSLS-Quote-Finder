# NSLS Speaker Broadcast Quote Search

Search hundreds of quotes from NSLS Speaker Broadcasts, student testimonials, and advisor remarks — right inside Claude Code.

```
/find-quotes quotes that talk positively about the NSLS
/find-quotes something inspiring about overcoming failure
/find-quotes anything from Jim Cramer about investing
/find-quotes a student talking positively about leadership
/find-quotes an advisor quote about mentorship
```

---

## How It Works

One slash command powers the search:

| Command | What it does |
|---|---|
| `/find-quotes [query]` | Searches the quote database by meaning and theme, not just keywords |

Quotes are stored in `quotes.json` in this repo — committed to git so the whole team shares one library.

New quotes are added by the repo maintainer using `extract_quotes.py` (a local Python script — no API calls, no AI, near-zero cost). The maintainer commits the updated `quotes.json` and the team gets new quotes with a `git pull`.

> **New installs:** `quotes.json` comes pre-loaded with all existing quotes. You can start searching immediately with `/find-quotes` — no ingestion needed.

---

## Prerequisites

1. **Claude Code** — [claude.ai/code](https://claude.ai/code)
2. **Python 3.9+** — only needed by the maintainer to run `extract_quotes.py`

---

## Installation

### Mac / Linux

```bash
git clone https://github.com/jhrala/NSLS-Quote-Finder.git
cd NSLS-Quote-Finder
chmod +x install.sh
./install.sh
```

### Windows

```powershell
git clone https://github.com/jhrala/NSLS-Quote-Finder.git
cd NSLS-Quote-Finder
.\install.ps1
```

> **Windows note:** If you see a security error running the script, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then re-run `.\install.ps1`.

The installer copies `/find-quotes` into your global `~/.claude/commands/` folder and points it at the `quotes.json` file in your cloned repo.

**After installing, restart Claude Code** to pick up the new command.

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
/find-quotes a student talking about why they joined the NSLS
/find-quotes an advisor quote about supporting students
```

Claude returns up to 8 ranked results, each with the speaker name, episode, timestamp, and an explanation of why it matches your query.

You can filter by speaker type naturally in your query:
- **"a student talking about…"** → searches only student quotes
- **"an advisor quote about…"** → searches only advisor quotes
- **"member quotes on…"** → searches only member quotes
- No type mentioned → searches all quotes

---

## Keeping Quotes Up to Date

**This is maintainer-only — teammates just need to `git pull`.**

### Adding Speaker Broadcast transcripts

1. Download the `.srt` transcript file from Google Drive
2. Run the extractor:

```bash
python3 extract_quotes.py "NSLS_Speaker Broadcast_Name.srt" \
  --speaker "Full Name" \
  --episode "NSLS Speaker Broadcast — Full Name" \
  --date 2024 \
  --speaker-type speaker-broadcast
```

3. Commit and push:

```bash
git add quotes.json
git commit -m "Add quotes from [Speaker Name] broadcast"
git push
```

### Batch processing a folder of SRT files

```bash
python3 extract_quotes.py transcripts/ --speaker-type speaker-broadcast
```

The script will prompt for speaker name, episode, and date for each file. Files already in the database are automatically skipped.

### Adding student, advisor, or member quotes

```bash
python3 extract_quotes.py student_testimonial.srt \
  --speaker "Jane Smith" \
  --episode "Chapter Spotlight — Jane Smith" \
  --date 2024 \
  --speaker-type student
```

Valid `--speaker-type` values: `speaker-broadcast`, `student`, `advisor`, `member`

### Preview without writing

```bash
python3 extract_quotes.py file.srt --speaker "Name" --dry-run
```

---

## extract_quotes.py Reference

```
python3 extract_quotes.py <path> [options]

Arguments:
  path                    SRT file or directory of SRT files

Options:
  --speaker "Full Name"   Guest speaker name (skips interactive prompt)
  --episode "..."         Episode name (default: "NSLS Speaker Broadcast — {speaker}")
  --date "2024"           Broadcast year
  --speaker-type TYPE     One of: speaker-broadcast, student, advisor, member
                          (default: speaker-broadcast)
  --min-words N           Minimum words for a passage to be included (default: 30)
  --dry-run               Preview quotes without writing to database
```

---

## Manually Editing Quotes

`quotes.json` is a plain JSON array. Open it in any editor to fix a quote, update a speaker name, or remove an entry. Each quote looks like:

```json
{
  "id": "2026-04-28-001",
  "speaker": "Jim Cramer",
  "speakerType": "speaker-broadcast",
  "text": "You have to be willing to fail...",
  "episode": "NSLS Speaker Broadcast — Jim Cramer",
  "date": "2024",
  "timestamp": "00:15:32",
  "sourceFile": "NSLS_Speaker Broadcast_Jim Cramer.srt",
  "themes": ["failure", "investing", "resilience"],
  "addedDate": "2026-04-28"
}
```

See `quotes.schema.json` for a full description of each field.

---

## Re-installing / Updating

```bash
git pull
./install.sh        # Mac/Linux
.\install.ps1       # Windows
```

This overwrites the command in `~/.claude/commands/` with the latest version.

---

## Troubleshooting

**`/find-quotes` doesn't appear after installing**
→ Restart Claude Code completely (quit and reopen).

**`/find-quotes` says the database is empty**
→ The `quotes.json` file is empty. Ask the maintainer to add quotes and push, then run `git pull`.

**A quote has wrong attribution or garbled text**
→ Edit `quotes.json` directly, fix the entry, and commit the fix.

**The Python script skips lines I expect it to catch**
→ Check if the host name appears as a speaker label in the SRT (e.g., `BRACY:`). Add it to `HOST_LABELS` in `extract_quotes.py` if missing.

**Need to re-process a file that was already ingested**
→ Remove the entry from `quotes.json` manually (delete lines with that `sourceFile`), then re-run the script.
