---
title: "feat: Speaker Broadcast Quote Search Webapp"
type: feat
status: active
date: 2026-04-17
---

# feat: Speaker Broadcast Quote Search Webapp

## Overview

Build a simple internal webapp that lets NSLS staff search Speaker Broadcast quotes using natural language. Staff type queries like "quotes that talk positively about the NSLS" or "quotes about leadership resilience" and get back the most relevant quotes ranked by relevance, with an explanation of why each matches.

The system has two modes:
1. **Admin ingestion**: An admin page where staff paste or process Speaker Broadcast documents, using Claude to automatically extract individual quotes and populate a Google Sheets database.
2. **Search**: A clean search interface that queries the Google Sheets database via Claude API semantic search and returns ranked results.

## Problem Frame

NSLS hosts Speaker Broadcasts with notable guests. Quotes from these sessions are valuable for marketing, communications, and program content — but they currently live inside Google Docs and PDFs in a Drive folder, making them hard to find by topic or sentiment. Staff need a searchable quote library with natural language search, not just keyword matching.

## Requirements Trace

- R1. Staff can type a natural language query and get back relevant Speaker Broadcast quotes
- R2. Results show the speaker name, quote text, broadcast episode/date, and a brief relevance explanation
- R3. Quotes are stored in Google Sheets (easy for non-technical staff to view and manually edit)
- R4. An admin flow allows processing existing Google Docs/PDFs from Drive to auto-extract quotes into the Sheet
- R5. The app is deployable to Netlify without a separate backend service
- R6. Search uses semantic/AI matching, not just keyword matching

## Scope Boundaries

- No user authentication (internal-only tool; Netlify password protection is sufficient if needed)
- No real-time sync from Drive — ingestion is a deliberate admin action
- No pagination or infinite scroll in MVP (all results returned at once, capped)
- No quote editing UI — staff edit the Google Sheet directly
- No analytics or usage tracking

### Deferred to Separate Tasks

- Embedding-based vector search: only needed if quote count exceeds ~1,000 where Claude single-prompt approach becomes expensive
- Quote approval workflow: currently any admin can add quotes without review step

## Context & Research

### Relevant Code and Patterns

This is a greenfield Next.js project. No existing codebase to mirror.

### Institutional Learnings

None applicable — new project.

### External References

- Google Sheets API v4 with service account auth: `googleapis` npm package, JWT client with `spreadsheets.readonly` scope
- Google Drive API v3 for reading Docs and PDFs: `drive.readonly` scope (safe for service accounts, no CASA audit required)
- Google Doc export as plain text: `drive.files.export({ mimeType: 'text/plain' })`
- PDF text extraction in serverless: `unpdf` library (serverless-safe, avoids `pdf-parse` filesystem bug)
- Claude API with prompt caching: quote list sent as cached content, query as dynamic — ~90% cost reduction on repeated searches
- Netlify serverless functions: 60s timeout, 1GB memory, read-only filesystem except `/tmp`

## Key Technical Decisions

- **Google Sheets as canonical database**: Rather than searching Drive Docs/PDFs directly at query time, extracted quotes live in a Sheet. This is stable, fast to query, and editable by non-technical staff. Drive Docs/PDFs are only touched during the admin ingestion step.
- **Claude Haiku for search + ingestion**: Cost-effective at this scale. With prompt caching on the quote list, search cost is ~$0.0025/query. Ingestion (extraction from docs) uses a separate call per document.
- **Claude does quote extraction during ingestion**: Rather than requiring manual quote entry, Claude reads the full text of a Broadcast Doc/PDF and identifies individual quotable quotes, saving staff significant manual work.
- **Single-prompt semantic search (no vector embeddings)**: For 100–500 quotes, passing all quotes to Claude in one prompt is simpler, cheaper to maintain, and produces better semantic results than embedding cosine similarity. Revisit if quote count exceeds ~1,000.
- **Next.js App Router on Netlify**: API routes become Netlify serverless functions automatically. No separate backend needed.
- **No real-time Drive sync**: Ingestion is an intentional admin action, not automatic. This avoids rate-limit complexity and keeps the architecture simple.

## Open Questions

### Resolved During Planning

- **Should we search Docs/PDFs directly or extract first?** Resolved: extract to Google Sheets. Drive file parsing on every search would be slow, hit Netlify's 60s timeout for large corpora, and be fragile. A stable Sheet is the right source of truth.
- **Embeddings or direct Claude search?** Resolved: direct Claude search with prompt caching at this scale. Embeddings add infrastructure complexity (vector DB) with no meaningful quality gain for <1,000 quotes.
- **PDF parsing library?** Resolved: `unpdf` — serverless-safe, actively maintained, avoids the `pdf-parse` filesystem footgun in Lambda environments.

### Deferred to Implementation

- Exact Google Sheets column schema: implementer should confirm with Josh what metadata fields matter (e.g., whether "program" or "audience type" should be tracked alongside speaker/date)
- Whether to cap returned results at 5, 10, or 20 — implementer can set a sensible default and make it configurable via env var
- Exact Claude prompt tuning: the "find relevant quotes" prompt will need iteration to return well-formatted JSON reliably

## Output Structure

```
speaker-broadcast-quote-finder/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                    # Search UI (home page)
│   ├── admin/
│   │   └── page.tsx                # Admin ingestion UI
│   └── api/
│       ├── search/
│       │   └── route.ts            # Search endpoint (Claude + Sheets)
│       └── ingest/
│           └── route.ts            # Ingestion endpoint (Drive → Claude → Sheets)
├── lib/
│   ├── google-sheets.ts            # Sheets read/write helpers
│   ├── google-drive.ts             # Drive file listing and export helpers
│   └── claude-search.ts            # Claude API search and extraction helpers
├── components/
│   ├── SearchBar.tsx
│   └── QuoteCard.tsx
├── docs/
│   └── plans/
│       └── 2026-04-17-001-feat-speaker-broadcast-quote-search-webapp-plan.md
├── .env.local.example
├── netlify.toml
└── package.json
```

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
SEARCH FLOW
───────────
User query
    │
    ▼
POST /api/search { query }
    │
    ├─ 1. Fetch all quotes from Google Sheets
    │       (cached in-memory with 1hr TTL to avoid Sheets API on every request)
    │
    ├─ 2. Build Claude prompt:
    │       [CACHED] System + quote list (prompt cache_control: "ephemeral")
    │       [DYNAMIC] User query
    │
    ├─ 3. Claude returns JSON array of { quoteId, relevanceScore, reason }
    │
    └─ 4. Join with full quote data, sort by score, return top N

INGESTION FLOW
──────────────
Admin selects Drive folder → clicks "Ingest"
    │
    ▼
POST /api/ingest { folderId }
    │
    ├─ 1. List files in Drive folder (Docs + PDFs)
    │
    ├─ For each file:
    │   ├─ Google Doc → drive.files.export({ mimeType: 'text/plain' })
    │   └─ PDF → drive.files.get({ alt: 'media' }) → unpdf text extraction
    │
    ├─ 2. POST full text to Claude:
    │       "Extract all individually quotable quotes from this broadcast transcript.
    │        For each quote return: speaker, quote_text, context, themes[]"
    │
    ├─ 3. Append extracted quotes to Google Sheet
    │       (skip duplicates by checking quote text similarity or hash)
    │
    └─ 4. Return summary: { filesProcessed, quotesAdded, duplicatesSkipped }
```

## Implementation Units

- [ ] **Unit 1: Project scaffold and configuration**

**Goal:** Initialize the Next.js project with all dependencies, Netlify config, and environment variable structure.

**Requirements:** R5

**Dependencies:** None

**Files:**
- Create: `package.json`
- Create: `app/layout.tsx`
- Create: `netlify.toml`
- Create: `.env.local.example`
- Create: `next.config.ts`

**Approach:**
- `next.config.ts` should set `output: 'standalone'` is NOT needed for Netlify — Netlify handles routing natively. Keep default config.
- `netlify.toml` should configure `[build]` with `command = "npm run build"` and `publish = ".next"`
- `.env.local.example` should document all required env vars: `GOOGLE_SERVICE_ACCOUNT_EMAIL`, `GOOGLE_PRIVATE_KEY`, `GOOGLE_SPREADSHEET_ID`, `GOOGLE_DRIVE_FOLDER_ID`, `ANTHROPIC_API_KEY`
- Dependencies: `next`, `react`, `react-dom`, `googleapis`, `unpdf`, `@anthropic-ai/sdk`
- Dev dependencies: `typescript`, `@types/react`, `@types/node`, `tailwindcss`

**Test scenarios:**
- Test expectation: none — pure scaffolding, no behavioral logic

**Verification:**
- `npm run dev` starts without errors
- `npm run build` completes successfully

---

- [ ] **Unit 2: Google Sheets integration**

**Goal:** Read all quotes from the Google Sheets database and write new rows during ingestion.

**Requirements:** R2, R3

**Dependencies:** Unit 1

**Files:**
- Create: `lib/google-sheets.ts`
- Create: `lib/google-sheets.test.ts`

**Approach:**
- Single `getSheetsClient()` factory using `google.auth.JWT` with `GOOGLE_SERVICE_ACCOUNT_EMAIL` and `GOOGLE_PRIVATE_KEY` (apply `.replace(/\\n/g, '\n')` to the key)
- `getAllQuotes()`: reads the full sheet range, maps rows to typed `Quote` objects. Cache the result in a module-level variable with a timestamp; return cached value if less than 1 hour old.
- `appendQuotes(quotes: Quote[])`: appends new rows to the sheet. Each quote row: `[speaker, quoteText, broadcastEpisode, broadcastDate, sourceFile, themes, addedDate]`
- `Quote` type: `{ id: string, speaker: string, text: string, episode: string, date: string, sourceFile: string, themes: string, addedDate: string }`
- The `id` is the row number (to use as a stable reference in Claude's returned JSON)

**Test scenarios:**
- Happy path: `getAllQuotes()` returns an array of typed Quote objects from a mocked Sheets response
- Edge case: empty sheet (no rows below header) returns empty array without throwing
- Edge case: private key with escaped `\n` characters is correctly unescaped before JWT init
- Error path: Sheets API call fails → error is thrown (not swallowed) so the API route returns a 500

**Verification:**
- `getAllQuotes()` called manually returns structured data matching the Sheet contents

---

- [ ] **Unit 3: Google Drive ingestion helpers**

**Goal:** List Drive files in a folder and extract plain text from Google Docs and PDFs.

**Requirements:** R4

**Dependencies:** Unit 1

**Files:**
- Create: `lib/google-drive.ts`
- Create: `lib/google-drive.test.ts`

**Approach:**
- `getDriveClient()`: same service account auth pattern as Sheets but with `drive.readonly` scope
- `listDriveFiles(folderId)`: paginates through all files in the folder, filters to `application/vnd.google-apps.document` and `application/pdf` MIME types, returns `{ id, name, mimeType, modifiedTime }[]`
- `extractTextFromFile(fileId, mimeType)`: branches on MIME type:
  - Google Doc: `drive.files.export({ mimeType: 'text/plain' }, { responseType: 'text' })`
  - PDF: `drive.files.get({ alt: 'media' }, { responseType: 'arraybuffer' })` → `unpdf.extractText()`
- Both paths return a plain string

**Test scenarios:**
- Happy path: Google Doc export returns string from Drive API response
- Happy path: PDF download + `unpdf` extraction returns text string
- Edge case: folder contains unsupported file types (e.g., images, spreadsheets) — these are silently skipped
- Error path: Drive API returns 403 (file not shared with service account) → error is surfaced with the file name in the message
- Edge case: PDF with no extractable text (scanned image PDF) returns empty string gracefully

**Verification:**
- Calling `listDriveFiles` against the real Drive folder returns the expected files
- `extractTextFromFile` returns non-empty text for a known test Doc

---

- [ ] **Unit 4: Claude API semantic search and quote extraction**

**Goal:** Two Claude-powered functions: (a) semantic search over a quote list, (b) quote extraction from raw broadcast text.

**Requirements:** R1, R6, R4

**Dependencies:** Unit 1

**Files:**
- Create: `lib/claude-search.ts`
- Create: `lib/claude-search.test.ts`

**Approach:**
- `searchQuotes(query: string, quotes: Quote[]): Promise<SearchResult[]>`:
  - Builds a Claude message with the quote list as `cache_control: { type: 'ephemeral' }` user content (prompt caching)
  - Dynamic part: the user's search query appended after the cached block
  - Instructs Claude to return a JSON array of `{ quoteId: string, score: number, reason: string }` sorted by descending score
  - Parses the response JSON; if parsing fails, retries once with a stricter "JSON only, no prose" instruction
  - Returns top 10 results joined with the full Quote objects

- `extractQuotesFromText(text: string, sourceFile: string): Promise<ExtractedQuote[]>`:
  - Passes the full broadcast transcript text to Claude
  - Instructs Claude to identify individually quotable statements (not paraphrases), attribute each to the named speaker, and return JSON: `{ speaker, quoteText, context, themes[] }`
  - Handles long documents by checking token estimate; if the document is very long (>80K tokens est.), splits into chunks with overlap and deduplicates

- Use `claude-haiku-4-5-20251001` as the default model (cost-efficient); make the model name an env var `CLAUDE_MODEL` for easy overriding
- Never log full quote lists or API keys

**Test scenarios:**
- Happy path: `searchQuotes` with a valid query returns a sorted array of `SearchResult` with `quoteId`, `score`, `reason`
- Happy path: `extractQuotesFromText` returns an array of `ExtractedQuote` objects from broadcast transcript text
- Edge case: Claude returns malformed JSON → retry logic is triggered, second attempt uses stricter prompt
- Edge case: empty quote list passed to `searchQuotes` → returns empty array without calling Claude
- Edge case: broadcast text is empty string → returns empty array without calling Claude
- Error path: Anthropic API returns 429 (rate limit) → error is thrown with a user-friendly message

**Verification:**
- `searchQuotes` called with "quotes about personal growth" returns relevant matches from a seeded quote list
- `extractQuotesFromText` called with a sample broadcast transcript returns structured quote objects

---

- [ ] **Unit 5: Search API route and search UI**

**Goal:** The `/api/search` endpoint and the main search page that staff use daily.

**Requirements:** R1, R2, R6

**Dependencies:** Units 2, 4

**Files:**
- Create: `app/api/search/route.ts`
- Create: `app/page.tsx`
- Create: `components/SearchBar.tsx`
- Create: `components/QuoteCard.tsx`

**Approach:**
- `POST /api/search` accepts `{ query: string }`, calls `getAllQuotes()` then `searchQuotes()`, returns `SearchResult[]` enriched with full Quote data
- Returns 400 if query is empty or missing; 500 with a generic message if Claude or Sheets fails
- The search page (`app/page.tsx`) is a client component with a search bar, loading skeleton, and results list
- `SearchBar`: controlled input with a submit button; also submits on Enter; disables while loading
- `QuoteCard`: displays speaker name, quote text (in block-quote styling), episode and date, and the Claude-generated relevance reason in a subdued style
- Keep styling minimal — Tailwind utility classes, NSLS brand colors if known, otherwise clean white/navy

**Test scenarios:**
- Happy path: POST `/api/search` with `{ query: "leadership" }` returns 200 with an array of results
- Error path: POST with empty `{ query: "" }` returns 400
- Error path: Sheets unavailable → 500 with `{ error: "Quote database unavailable" }` (no stack traces in response)
- Integration: end-to-end — query hits the route, route calls real Sheets + Claude (in integration test or manual verification), results come back

**Verification:**
- Typing a query in the search bar and submitting returns relevant quote cards
- Loading state is visible during the API call
- Empty results state shows a helpful message ("No quotes found — try a different search")

---

- [ ] **Unit 6: Admin ingestion UI and API route**

**Goal:** Admin page where staff can trigger Drive folder ingestion to extract and save new quotes.

**Requirements:** R4

**Dependencies:** Units 2, 3, 4

**Files:**
- Create: `app/admin/page.tsx`
- Create: `app/api/ingest/route.ts`

**Approach:**
- `POST /api/ingest` with optional `{ folderId?: string }` (falls back to `GOOGLE_DRIVE_FOLDER_ID` env var)
  - Lists files in Drive folder
  - For each file: extract text → call `extractQuotesFromText()` → append to Sheet
  - Returns `{ filesProcessed: number, quotesAdded: number, errors: string[] }`
  - Runs sequentially (not parallel) to avoid Netlify timeout — one file at a time
- Admin page: simple form showing the configured Drive folder ID, a "Run Ingestion" button, and a results summary after completion
- No authentication on the admin page in MVP — add a note in code that this should be protected if the app becomes public
- Show a progress indicator (the API call may take 20–40s for a folder with several docs)

**Test scenarios:**
- Happy path: POST `/api/ingest` processes a folder with one Google Doc and one PDF, returns `{ filesProcessed: 2, quotesAdded: N, errors: [] }`
- Edge case: folder is empty → `{ filesProcessed: 0, quotesAdded: 0, errors: [] }`
- Error path: one file fails to parse (e.g., password-protected PDF) → that file's error is added to `errors[]`, processing continues for remaining files
- Edge case: Claude extraction returns no quotes for a file → no rows appended, no error raised

**Verification:**
- Clicking "Run Ingestion" on the admin page processes the configured Drive folder and shows a success summary
- New quotes appear in the Google Sheet after ingestion completes

## System-Wide Impact

- **Interaction graph:** All search and ingestion flows go through Next.js API routes → Netlify serverless functions. No workers, queues, or webhooks involved.
- **Error propagation:** API route handlers should catch all errors and return structured JSON error responses. Never expose raw error messages or stack traces to the browser.
- **State lifecycle risks:** The in-memory quote cache in `lib/google-sheets.ts` is per-function-instance (Netlify spins up new instances). Cache TTL prevents stale data issues; the tradeoff is that quote updates in the Sheet take up to 1 hour to appear in search results. This is acceptable for MVP.
- **API surface parity:** No external consumers of the API in MVP.
- **Integration coverage:** The search flow crosses three external services (Google Sheets → Claude API → browser). A manual end-to-end smoke test after deployment is the primary integration verification.
- **Unchanged invariants:** The Google Sheet is the source of truth. The webapp never deletes rows — it only reads and appends.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Netlify 60s timeout during ingestion of large folders | Process files sequentially; if a folder has many large PDFs, advise admin to break ingestion into smaller batches or use a separate run per subfolder |
| Claude returns malformed JSON for search results | Retry with stricter prompt; fall back to returning all quotes unranked if retry fails |
| Google Sheet grows beyond ~1,000 quotes, making Claude search expensive | Document the embedding upgrade path; set a cost alert in Anthropic console |
| Service account key exposed in repo | `.env.local` must be in `.gitignore`; `.env.local.example` documents required vars without values |
| PDF contains only scanned images (no extractable text) | `unpdf` returns empty string; implementer should surface this as a warning to admin, not a silent failure |
| Drive API rate limits during large ingestion | Add a small delay (500ms) between file fetches; Drive API allows 1,000 requests/100 seconds per user |

## Documentation / Operational Notes

- After deployment, share the Google Sheet and Drive folder with the service account email (viewer permission)
- The `.env.local.example` file is the setup guide for new deployments
- Netlify env vars must be set in the dashboard; the private key value must include real newlines (Netlify handles this correctly when pasted into the dashboard)
- Recommend Netlify password protection (under Site settings → Access control) if the URL is ever shared outside NSLS staff

## Sources & References

- Google Sheets API v4 with `googleapis` npm package
- Google Drive API v3: files.list, files.export, files.get with `alt=media`
- `unpdf` for serverless-safe PDF text extraction
- Anthropic SDK with prompt caching (`cache_control: { type: 'ephemeral' }`)
- Netlify Next.js deployment docs
