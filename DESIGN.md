# NSLS Quote Finder

## What This Is (for the user)

You're looking for the right quote from an NSLS Speaker Broadcast — for a social post, email, deck, or article. Instead of scrubbing through videos or guessing exact keywords, you describe the theme or idea you want, and the tool surfaces the most relevant quotes — each with who said it, which episode it's from, and a timestamp link to the exact moment.

## Customers

### Marketing / Content Creators — the primary direct users
- **Who**: NSLS staff producing social, email, copy, and decks. Comfortable running a slash command; not interested in database mechanics.
- **Context**: Mid-content-creation, need a compelling, attributable quote fast.
- **Flows**: `/find-quotes <theme or idea>`.

### Maintainers — smaller set of direct users
- **Who**: Builders who keep the quote database current as new broadcasts air.
- **Context**: After a new Speaker Broadcast, adding its transcript so the quote is searchable.
- **Flows**: `/ingest-quotes` (single) or `bulk_ingest.py` (batch), then commit and push.

## UX Principles

1. **Search by meaning, not keywords.** Describe the idea and get relevant quotes even when the exact words differ.
2. **Every result is attributable and verifiable.** Speaker, episode, and a timestamp link back to the source moment — always.
3. **Ranked and bounded.** A short, ranked set (up to ~8), never an overwhelming dump.
4. **One command to search.** `/find-quotes <query>` — no filters or syntax to learn.
5. **Maintenance is invisible to searchers.** Finding a quote never requires knowing how the database is built or updated.
6. **Trustworthy quotes.** Results reflect what was actually said — no paraphrasing that changes meaning.

## What This Should NOT Become

- A keyword-only / grep search over a transcript file.
- A general media or asset library (DAM).
- A quote generator or paraphraser that invents or rewords quotes.
- A tool that requires every user to curate the database to get value.
- A public-facing endpoint — it's an internal builder tool.

## Interaction Surface

- **Channel**: Claude Code (CLI)
- **Trigger**: User-initiated — `/find-quotes <theme/query>` for searchers; `/ingest-quotes` or `bulk_ingest.py` for maintainers
- **User actions**: Install once via script → run `/find-quotes` with a description; maintainers add transcripts and push
- **Output the user sees**: Up to 8 ranked quotes, each with speaker, episode, a video timestamp link, and a short relevance explanation

## Measuring Success

### Adoption
- **What "adopted" looks like**: Content creators reach for `/find-quotes` when they need a quote; repeat use; maintainers keep the database current.
- **Current adoption**: Early (TBD).
- **Adoption goal**: Regular use across the content team within 90 days (TBD).

### Satisfaction
- **How we'll know**: Searchers find a usable quote on the first query; quotes show up in real content; few "how do I…" questions.
- **Signals to watch**: Searches run, share of searches yielding a used quote, repeat usage, transcript freshness.
- **Red flags**: People go back to manually scrubbing videos; results irrelevant to the query; database goes stale; quotes turn out misattributed.

## Change Log

| Date | Change | Reviewed |
|------|--------|----------|
| 2026-06-04 | Initial design intent | Josh Hrala |
