---
title: "feat: Speaker Broadcast Quote Search — Claude Code Slash Commands"
type: feat
status: active
date: 2026-04-17
supersedes: docs/plans/2026-04-17-001-feat-speaker-broadcast-quote-search-webapp-plan.md
---

# feat: Speaker Broadcast Quote Search — Claude Code Slash Commands

## Overview

Instead of a standalone webapp, this delivers two Claude Code slash commands that let NSLS staff search Speaker Broadcast quotes and ingest new ones from Google Drive — entirely inside Claude Code, with no deployment, no API keys, and no infrastructure to maintain.

- **`/find-quotes [query]`** — Semantic search over the quote database. Claude reads the local quote file and returns the most relevant quotes with explanations.
- **`/ingest-quotes`** — Reads Speaker Broadcast Docs and PDFs from Google Drive (via the already-connected Drive MCP), has Claude extract individual quotes, and appends them to the local quote database.

The quote database is a local `quotes.json` file tracked in this repo — simple, portable, and editable by anyone.

## Problem Frame

NSLS hosts Speaker Broadcasts and wants to search the resulting quotes by topic and sentiment. The slash command approach leverages Claude Code's built-in AI and the already-connected Google Drive MCP to deliver this with dramatically less complexity than a webapp: no service accounts, no Netlify deployment, no React frontend. The tradeoff is that users need Claude Code — which is acceptable for the NSLS team's use.

## Requirements Trace

- R1. Staff can run `/find-quotes` with a natural language query and get back ranked, relevant quotes
- R2. Results show speaker name, quote text, episode/date, and a relevance explanation
- R3. Quotes are stored in a local `quotes.json` file (human-readable, git-trackable)
- R4. `/ingest-quotes` reads Google Drive broadcast documents and auto-extracts quotes using Claude
- R5. No external infrastructure — works entirely within Claude Code using the existing Drive MCP

## Scope Boundaries

- Requires Claude Code with the Google Drive MCP connected (already confirmed active)
- Not a web-accessible URL — staff must use Claude Code to search
- No deduplication in MVP — if the same file is ingested twice, duplicates may appear (easy to fix manually in the JSON)
- No quote editing UI — edit `quotes.json` directly or in any text editor

### Deferred to Separate Tasks

- Deduplication logic during ingestion: separate improvement once the base flow works
- Sharing with staff who don't have Claude Code: if needed later, the webapp plan (superseded) is the upgrade path

## Context & Research

### Relevant Code and Patterns

- Claude Code slash commands live in `.claude/commands/` as markdown files
- `$ARGUMENTS` in the command file is replaced with whatever the user types after the command name
- Commands have access to all Claude Code tools including MCP tools
- The Google Drive MCP (already connected) provides: `search_files`, `read_file_content`, `list_recent_files`, `download_file_content`, `create_file`

### External References

- Claude Code slash commands: project-level commands live in `<project>/.claude/commands/`
- Drive MCP `read_file_content` can read Google Docs as text and download PDFs
- Claude's context window comfortably holds hundreds of quotes for semantic search

## Key Technical Decisions

- **Local `quotes.json` as the database**: Simpler than Google Sheets for this use case — no API, no auth, readable in any editor, committable to git. Staff can view/edit it directly.
- **Semantic search happens in-context**: Claude reads all quotes into its context window and semantically ranks them. No embeddings, no vector DB. Works well for hundreds of quotes.
- **Drive MCP for ingestion only**: Drive is read at ingestion time to extract quotes from broadcast documents. It is not read at search time (that would be slow and re-parse everything on every query).
- **Project-level commands**: Slash commands live in `.claude/commands/` inside this repo so they're tied to the project and can be shared with teammates via git.
- **Drive folder ID configured in the ingest command**: Hardcode the NSLS broadcast Drive folder ID directly in the `/ingest-quotes` command file (or reference a `config.json`). No env var setup required.

## Open Questions

### Resolved During Planning

- **Can slash commands use Drive MCP?** Yes — confirmed active in this Claude Code session. Slash commands have access to all connected MCP tools.
- **Where do quotes live?** Local `quotes.json` in the repo. Simpler than Sheets, no API needed for search.
- **How does the Drive MCP read PDFs?** `read_file_content` or `download_file_content` — implementer should test both to confirm which returns extractable text for PDFs vs. Google Docs.

### Deferred to Implementation

- Exact Drive folder ID: Josh should provide the folder ID (or folder name to search for) when building the ingest command
- Whether `read_file_content` or `download_file_content` works better for PDFs in this MCP — test during implementation
- Max results to return in `/find-quotes` — default to 8, easy to adjust in the command file

## Output Structure

```
speaker-broadcast-quote-finder/
├── .claude/
│   └── commands/
│       ├── find-quotes.md        # /find-quotes slash command
│       └── ingest-quotes.md      # /ingest-quotes slash command
├── quotes.json                   # Quote database (starts empty, grows with ingestion)
├── quotes.schema.json            # Schema documentation for the quote format
└── docs/
    └── plans/
        ├── 2026-04-17-001-feat-speaker-broadcast-quote-search-webapp-plan.md  (superseded)
        └── 2026-04-17-002-feat-speaker-broadcast-quote-slash-commands-plan.md
```

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
/find-quotes "quotes about NSLS leadership impact"
    │
    ▼
Claude reads quotes.json
    │
    ▼
Claude semantically ranks all quotes against the query
    │
    ▼
Returns top ~8 results:
  • Speaker name + quote text
  • Episode and date
  • Why it matches the query

─────────────────────────────────────────────

/ingest-quotes
    │
    ▼
Claude calls Drive MCP → search_files / list_recent_files
  (finds Docs + PDFs in the NSLS broadcast folder)
    │
    ▼
For each file:
  Drive MCP → read_file_content
    │
    ▼
Claude extracts individual quotes:
  { speaker, text, episode, date, themes[] }
    │
    ▼
Claude appends new entries to quotes.json (Write tool)
    │
    ▼
Reports: "Added 14 quotes from 3 files"
```

## Implementation Units

- [ ] **Unit 1: Quote database file and schema**

**Goal:** Create the `quotes.json` database file and document its structure.

**Requirements:** R3

**Dependencies:** None

**Files:**
- Create: `quotes.json`
- Create: `quotes.schema.json`

**Approach:**
- `quotes.json` starts as an empty array `[]`
- Each quote entry: `{ "id", "speaker", "text", "episode", "date", "sourceFile", "themes", "addedDate" }`
- `id` is a short unique string (e.g., timestamp + index: `"2026-04-17-001"`)
- `quotes.schema.json` documents each field — its type, purpose, and example — so future maintainers understand the format
- Include 2–3 hand-written sample quotes so the file isn't empty and `/find-quotes` can be tested immediately

**Test scenarios:**
- Test expectation: none — this is a data file with no logic

**Verification:**
- `quotes.json` is valid JSON and matches the schema
- Sample quotes cover at least two different speakers and themes

---

- [ ] **Unit 2: `/find-quotes` slash command**

**Goal:** A slash command that takes a natural language query and returns the most semantically relevant quotes from `quotes.json`.

**Requirements:** R1, R2, R5

**Dependencies:** Unit 1

**Files:**
- Create: `.claude/commands/find-quotes.md`

**Approach:**
The command file instructs Claude to:
1. Read `quotes.json` using the Read tool
2. Analyze all quotes against the query `$ARGUMENTS` — match on meaning, sentiment, and themes, not just keywords
3. Return the top 8 results ranked by relevance, formatted clearly:
   - Speaker name (bold)
   - Quote text (block-quoted)
   - Episode and date
   - One-sentence explanation of why it matches
4. If fewer than 8 quotes match well, return only the genuinely relevant ones with a note
5. If `quotes.json` is empty, tell the user to run `/ingest-quotes` first

The command should work for queries like:
- "quotes that talk positively about the NSLS"
- "something about perseverance or overcoming adversity"
- "quotes I could use in a fundraising email"
- "anything from Dr. Smith about student success"

**Test scenarios:**
- Happy path: query "leadership" against sample quotes returns the most thematically relevant ones with reasons
- Edge case: very specific query with no good matches returns a clear "no strong matches" message rather than forcing irrelevant results
- Edge case: `quotes.json` is empty → helpful message to run `/ingest-quotes`
- Happy path: query by speaker name ("anything from Jane Doe") correctly filters and ranks by that speaker

**Verification:**
- Running `/find-quotes quotes about overcoming challenges` returns ranked results with relevance explanations
- Results feel semantically accurate, not just keyword-matched

---

- [ ] **Unit 3: `/ingest-quotes` slash command**

**Goal:** A slash command that reads Speaker Broadcast files from Google Drive, extracts individual quotes using Claude, and appends them to `quotes.json`.

**Requirements:** R4, R5

**Dependencies:** Unit 1

**Files:**
- Create: `.claude/commands/ingest-quotes.md`

**Approach:**
The command file instructs Claude to:
1. Use the Drive MCP (`search_files` or `list_recent_files`) to find Speaker Broadcast documents in the configured Drive folder — include the folder name or ID directly in the command file
2. For each file found:
   - Call `read_file_content` (or `download_file_content`) to get the text
   - Extract all individually quotable statements — direct quotes with clear speaker attribution, not paraphrases or summaries
   - For each quote, capture: speaker name, quote text, episode/broadcast name (from the filename or document header), date (from filename or document if present), and 2–4 theme tags
3. Read the current `quotes.json`
4. Append new quotes (skipping any where the quote text is identical to an existing entry)
5. Write the updated `quotes.json` using the Write tool
6. Report a summary: how many files processed, how many quotes added, how many skipped as duplicates

Edge case guidance to include in the command:
- If a file has no clear speaker attributions, skip it and note the filename in the report
- If the Drive MCP can't read a file (wrong format, permission issue), log it in the report and continue

**Test scenarios:**
- Happy path: running `/ingest-quotes` against a folder with 2 broadcast documents adds new quotes to `quotes.json` and reports the count
- Edge case: re-running on the same folder — exact-text duplicates are skipped, report shows "X skipped as duplicates"
- Edge case: a file in the folder is a non-broadcast document (e.g., a planning doc) — Claude should use judgment to skip files that don't appear to be broadcast transcripts
- Error path: Drive MCP can't access a file → that file is noted in the report, rest of ingestion continues

**Verification:**
- After running `/ingest-quotes`, `quotes.json` has new entries with correct speaker, text, episode, and theme fields
- Running it a second time without new files in Drive doesn't add duplicates

## System-Wide Impact

- **No external surface**: Both commands run entirely within Claude Code — no network endpoints, no deployed services.
- **`quotes.json` is the shared state**: If multiple team members use this repo, they should commit and pull `quotes.json` to share the quote library. Concurrent ingestion from two people could cause merge conflicts — but this is unlikely in practice.
- **Drive MCP permissions**: The MCP uses whatever Google account is authenticated in Claude Code. Ensure that account has at least Viewer access to the NSLS broadcast Drive folder.
- **Unchanged invariants**: The slash commands never delete from `quotes.json` — they only read and append. Manual cleanup of bad entries is done by editing the file directly.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Drive MCP `read_file_content` may not extract text from PDFs (returns binary or blank) | Test during Unit 3 implementation; fall back to `download_file_content` + instruct Claude to parse visible text |
| Broadcast documents don't have clear speaker attribution | Ingest command instructs Claude to skip ambiguous files and report them so staff can manually add those quotes |
| `quotes.json` grows very large (1,000+ quotes) and search slows | Acceptable for now; note the threshold and revisit with embeddings if needed |
| Two team members ingest simultaneously causing a JSON conflict | Advise in documentation: one person ingests at a time, commit after ingestion |

## Documentation / Operational Notes

- The Drive folder ID (or name to search) must be set in `.claude/commands/ingest-quotes.md` before first use — implementer should leave a clear `CONFIGURE THIS` marker
- Staff need Claude Code with the Google Drive MCP connected and authenticated with an account that has access to the NSLS broadcast Drive folder
- `quotes.json` should be committed to git so the whole team shares one quote library; add a note in the README

## Sources & References

- Claude Code slash commands: project-level commands in `.claude/commands/`
- Google Drive MCP tools confirmed active in this session: `search_files`, `read_file_content`, `list_recent_files`, `download_file_content`, `create_file`
- Supersedes: [docs/plans/2026-04-17-001-feat-speaker-broadcast-quote-search-webapp-plan.md](2026-04-17-001-feat-speaker-broadcast-quote-search-webapp-plan.md)
