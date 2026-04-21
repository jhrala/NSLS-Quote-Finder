Extract quotes from NSLS Speaker Broadcast transcripts in Google Drive and add them to the local quote database.

**Quote database path:** `{{QUOTES_DB_PATH}}`
**Drive Folder ID:** `1M1sRyyyM513RE1gqRA3B7G02eNaA5QB2` (Speaker Broadcast Transcripts)

Follow these steps exactly:

## Step 1 — Load existing quotes
Read `{{QUOTES_DB_PATH}}`. Note all existing `sourceFile` values so you can skip files already ingested.

## Step 2 — Find broadcast files in Drive
Use the Drive MCP `search_files` tool to find files in the broadcast folder. Try this query:
```
title contains 'Speaker Broadcast'
```

List all files found. For each file, check if its `title` already exists in the `sourceFile` field of any quote in the database. Skip already-ingested files and note them in the final report.

## Step 3 — Read and parse each new file
For each new file, use `read_file_content` with the file's ID.

**Important — these files are SRT-format transcripts.** The raw content looks like:
```
1
00:00:10.297 --> 00:00:11.825
WOMAN: Please welcome our host

2
00:00:11.825 --> 00:00:13.957
for tonight's speaker broadcast,

3
00:01:45.210 --> 00:01:48.900
CRAMER: You have to be willing to fail.
```

Parse each SRT block and retain its start timestamp alongside the text. Do NOT discard the timestamps — they are critical for video editing.

For each block, extract:
- **Start time**: the first timecode before `-->` (e.g. `00:01:45.210`)
- **Speaker**: the label before the colon (e.g. `CRAMER`) if present
- **Text**: the spoken words after the speaker label

Join consecutive blocks from the same speaker into complete sentences, keeping the **start time of the first block** in the group as the timestamp for that passage.

## Step 4 — Identify the guest speaker
From the filename and transcript, determine:
- The **guest speaker's name** (the featured speaker, not the host Kevin Bracy)
- The **broadcast episode name** (typically the filename)
- The **approximate date** (from transcript content if mentioned, otherwise the file's creation year)

Focus on extracting quotes from the **guest speaker**.

## Step 5 — Extract quotable quotes
From the cleaned transcript, identify statements that are:
- **Directly quotable** — a complete thought in the speaker's own words
- **Substantive** — a meaningful insight, lesson, or perspective (not filler phrases)
- **Self-contained** — understandable without surrounding context
- **At least ~25 words** — no sentence fragments

Good candidates: advice about career/leadership/success/failure, statements about the NSLS, personal anecdotes with a clear lesson, memorable standalone lines.

Skip: audience applause, announcements, host introductions, questions (not answers), website URLs.

For each quote, assign 2–5 theme tags from:
`leadership`, `success`, `failure`, `resilience`, `NSLS`, `career`, `money`, `investing`, `entrepreneurship`, `education`, `self-belief`, `work ethic`, `community`, `growth mindset`, `perseverance`, `student success`, `mentorship`, `purpose`, `innovation`

## Step 6 — Build new quote entries
```json
{
  "id": "YYYY-MM-DD-NNN",
  "speaker": "Full Speaker Name",
  "text": "Exact reconstructed quote text.",
  "episode": "NSLS Speaker Broadcast — [Speaker Name]",
  "date": "YYYY",
  "timestamp": "HH:MM:SS",
  "sourceFile": "Exact filename from Drive",
  "themes": ["theme1", "theme2"],
  "addedDate": "today's date"
}
```

`timestamp` is the SRT start time of the first subtitle block that makes up this quote, formatted as `HH:MM:SS` (drop the milliseconds). This is what the video editor uses to find the clip. It is required — do not omit it.

For `id`: today's date + 3-digit sequence starting from 001, incrementing from the highest existing ID for today.

## Step 7 — Write to the database
Read `{{QUOTES_DB_PATH}}` again to get the latest state. Merge new quotes into the array. Write the complete updated array back to the same path using the Write tool.

Do not lose any existing quotes.

## Step 8 — Report results
```
Ingestion complete.

Files found in Drive: [N]
Already ingested (skipped): [filenames]
Files processed: [N]
Quotes added: [N]
Total in database: [N]

New quotes by file:
- [Filename]: [N] quotes — Speakers: [names]

Errors: [any files that failed]
```

## If no new files are found
Report: "All files in the Drive folder have already been ingested. Database has [N] quotes. Add new transcripts to the Drive folder and run `/update-quotes` again."
