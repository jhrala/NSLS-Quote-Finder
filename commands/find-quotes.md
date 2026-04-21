Search the NSLS Speaker Broadcast quote database for quotes matching this query: $ARGUMENTS

Follow these steps exactly:

## Step 1 — Load the database
Read the file at this exact path: `{{QUOTES_DB_PATH}}`

If the file is empty or contains an empty array `[]`, tell the user to run `/update-quotes` first to populate it.

## Step 2 — Understand the query
The query may be:
- A topic or theme: "quotes about resilience"
- A sentiment/use case: "quotes that speak positively about the NSLS" or "quotes I could use in a fundraising email"
- A speaker: "anything from Jim Cramer about money"
- An emotion or message: "something inspiring about overcoming failure"

Match on **meaning and intent**, not just keywords. A quote about "bouncing back from setbacks" matches a query about "resilience" even if the word resilience never appears.

## Step 3 — Score and rank
Evaluate every quote against the query. Score each one:
- **Strong match** (3): directly addresses the query's theme or sentiment
- **Partial match** (2): tangentially related or touches on the topic
- **Weak/no match** (1 or 0): not meaningfully related

Return the top 8 quotes by score. If fewer than 8 have a score of 2 or higher, only return the ones that are genuinely relevant — don't pad results with weak matches.

## Step 4 — Format results

Present each result like this:

---
**[Speaker Name]** — *[Episode]*
Video timestamp: **[timestamp]** (seek to this point in the footage) | Added: [addedDate]

> "[Quote text]"

*Why this matches:* [One sentence explaining the connection to the query]

---

If a quote has no `timestamp` field (older entries ingested before this feature was added), omit that line rather than showing blank.

After all results, add a brief footer:
- Total quotes in database: [N]
- Search query: "[the original query]"
- To add more quotes, run `/update-quotes`

## If no good matches exist
Say: "No strong matches found for '[query]'. The database has [N] quotes total. Try a broader search, or run `/update-quotes` to add more broadcasts."

## Important
- Never fabricate quotes. Only return quotes that exist in the JSON file.
- If a speaker name appears in the query, filter to that speaker first before ranking.
- Preserve the exact quote text — do not paraphrase or trim quotes.
