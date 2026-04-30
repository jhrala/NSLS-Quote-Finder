#!/usr/bin/env python3
"""
NSLS Quote Extractor — Rule-based SRT parser for the Speaker Broadcast quote database.

Usage:
    # Single file (prompts for metadata):
    python extract_quotes.py "NSLS_Speaker Broadcast_Jim Cramer.srt"

    # Single file with all flags:
    python extract_quotes.py "NSLS_Speaker Broadcast_Jim Cramer.srt" \
        --speaker "Jim Cramer" \
        --episode "NSLS Speaker Broadcast — Jim Cramer" \
        --date 2024 \
        --speaker-type speaker-broadcast

    # Batch: process all .srt files in a folder:
    python extract_quotes.py transcripts/ --speaker-type speaker-broadcast

    # Preview only (don't write to database):
    python extract_quotes.py file.srt --speaker "Name" --dry-run

    # Adjust minimum word count (default: 30):
    python extract_quotes.py file.srt --speaker "Name" --min-words 20
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

QUOTES_DB = Path(__file__).parent / "quotes.json"

# Labels that identify the host or non-guest speakers — skip these blocks.
# Case-insensitive prefix match before the colon in subtitle text.
HOST_LABELS = {
    "bracy", "kevin", "host", "announcer", "woman", "man", "moderator",
    "interviewer", "narrator", "emcee", "mc",
}

# Text patterns that indicate non-speech content — skip any block containing these.
SKIP_PATTERNS = [
    # Markdown-escaped bracket forms: \[ applause \]
    r"\\\[.*?applause.*?\\\]", r"\\\[.*?cheer.*?\\\]",
    r"\\\[.*?music.*?\\\]",    r"\\\[.*?laughter.*?\\\]",
    r"\\\[.*?crowd.*?\\\]",    r"\\\[.*?inaudible.*?\\\]",
    r"\\\[.*?crosstalk.*?\\\]",r"\\\[.*?noise.*?\\\]",
    r"\\\[.*?announcer.*?\\\]",r"\\\[.*?narrator.*?\\\]",
    # Raw bracket forms: [applause]
    r"\[applause\]", r"\[cheer", r"\[music\]", r"\[laughter\]",
    r"\[crowd\]", r"\[inaudible\]", r"\[crosstalk\]",
    r"\[announcer\]", r"\[narrator\]",
    # Parenthesis forms: (applause), (upbeat music), (cheers and applause)
    r"\(.*?applause.*?\)", r"\(.*?cheer.*?\)", r"\(.*?music.*?\)",
    r"\(.*?laughter.*?\)", r"\(.*?crowd.*?\)", r"\(.*?inaudible.*?\)",
    r"\(.*?audience.*?\)",
    # URLs
    r"www\.", r"http", r"\.com", r"\.org",
]
SKIP_REGEX = re.compile("|".join(SKIP_PATTERNS), re.IGNORECASE)

# Keyword → theme mapping. A passage earns a theme if any keyword appears in it.
# Themes are ranked by hit count; top 2–5 are assigned.
THEME_KEYWORDS: dict[str, list[str]] = {
    "leadership": ["lead", "leader", "leadership", "executive", "influence", "direct",
                   "vision", "inspire", "motivate", "authority", "decision"],
    "success": ["success", "succeed", "achieve", "accomplish", "win", "goal",
                "results", "excellence", "thrive", "prosper", "attain"],
    "failure": ["fail", "failure", "mistake", "wrong", "setback", "loss",
                "defeat", "stumble", "error", "regret", "fell short"],
    "resilience": ["resilience", "resilient", "bounce back", "recover", "overcome",
                   "adversity", "hardship", "tough", "strength", "endure", "rise"],
    "NSLS": ["nsls", "national society", "honor society", "honor student",
             "leadership society", "this organization"],
    "career": ["career", "profession", "industry", "job market", "opportunity",
               "path", "workplace", "promotion", "hire", "interview", "resume"],
    "money": ["money", "financial", "finance", "wealth", "income", "salary",
              "pay", "earnings", "net worth", "budget", "debt", "saving"],
    "investing": ["invest", "investment", "stock", "market", "portfolio",
                  "fund", "return", "asset", "equity", "dividend", "trading"],
    "entrepreneurship": ["entrepreneur", "startup", "business", "founded",
                         "venture", "build a company", "own a business", "risk"],
    "education": ["education", "school", "college", "university", "degree",
                  "learn", "study", "graduate", "campus", "knowledge"],
    "self-belief": ["believe in yourself", "confidence", "confident", "self-worth",
                    "trust yourself", "potential", "capable", "self-doubt",
                    "you can", "believe you"],
    "work ethic": ["work hard", "dedication", "discipline", "effort", "commitment",
                   "diligence", "hustle", "grind", "put in the work", "show up"],
    "community": ["community", "together", "support each other", "give back",
                  "serve", "help others", "society", "neighbors", "collective"],
    "growth mindset": ["grow", "growth mindset", "mindset", "improve", "develop",
                       "evolve", "open to", "feedback", "learn from"],
    "perseverance": ["persevere", "persist", "keep going", "don't give up",
                     "never stop", "continue", "push through", "stay the course",
                     "keep trying", "determination"],
    "student success": ["student", "students", "campus", "chapter", "academic",
                        "grade", "scholarship", "honor student", "college student"],
    "mentorship": ["mentor", "mentee", "guide", "advice", "advise", "coach",
                   "role model", "sponsor", "teach", "show the way"],
    "purpose": ["purpose", "mission", "meaning", "why", "passion", "calling",
                "driven", "what drives", "reason for"],
    "innovation": ["innovation", "innovative", "create", "creative", "new idea",
                   "technology", "disrupt", "invent", "breakthrough", "cutting edge"],
}

VALID_SPEAKER_TYPES = ["speaker-broadcast", "student", "advisor", "member"]


# ---------------------------------------------------------------------------
# SRT parsing
# ---------------------------------------------------------------------------

def parse_srt(text: str) -> list[dict]:
    """
    Parse an SRT file into a list of blocks:
        {"seq": int, "start": "HH:MM:SS", "text": str}

    Handles both HH:MM:SS,mmm and HH:MM:SS.mmm timestamp formats.
    """
    blocks = []
    # Split on double newline (blank line between blocks)
    raw_blocks = re.split(r"\n\s*\n", text.strip())

    for raw in raw_blocks:
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue

        # Line 0: sequence number
        if not lines[0].isdigit():
            continue
        seq = int(lines[0])

        # Line 1: timestamps  e.g. 00:01:23,456 --> 00:01:25,789
        ts_match = re.match(
            r"(\d{2}:\d{2}:\d{2})[,.](\d+)\s*--\\?>?\s*(\d{2}:\d{2}:\d{2})[,.](\d+)",
            lines[1],
        )
        if not ts_match:
            continue
        start_ts = ts_match.group(1)  # HH:MM:SS only

        # Lines 2+: subtitle text
        text_lines = " ".join(lines[2:])
        blocks.append({"seq": seq, "start": start_ts, "text": text_lines})

    return blocks


def extract_speaker_label(text: str) -> tuple[str | None, str]:
    """
    If text starts with 'LABEL: rest', return (label_lower, rest).
    Otherwise return (None, text).
    """
    m = re.match(r"^([A-Z][A-Z0-9 ]{0,20}):\s*(.*)", text)
    if m:
        return m.group(1).strip().lower(), m.group(2).strip()
    return None, text


def should_skip(text: str, label: str | None) -> bool:
    """Return True if this block should be excluded from candidate quotes."""
    # Skip known host labels
    if label and label in HOST_LABELS:
        return True
    # Skip if text matches non-speech patterns
    if SKIP_REGEX.search(text):
        return True
    # Skip very short fragments
    if len(text.split()) < 5:
        return True
    return False


def join_blocks(blocks: list[dict]) -> list[dict]:
    """
    Merge consecutive SRT blocks that appear to be part of the same utterance
    (i.e. same speaker label, or continuation without a speaker change).
    Returns a list of passages: {"start": "HH:MM:SS", "label": str|None, "text": str}
    """
    if not blocks:
        return []

    passages = []
    current_label: str | None = None
    current_start: str | None = None
    current_words: list[str] = []

    def flush():
        nonlocal current_label, current_start, current_words
        if current_words:
            passages.append({
                "start": current_start,
                "label": current_label,
                "text": " ".join(current_words),
            })
        current_label = None
        current_start = None
        current_words = []

    for block in blocks:
        # Non-speech blocks (applause, music, URLs) break the current passage.
        if SKIP_REGEX.search(block["text"]):
            flush()
            continue

        # Dash-prefix format: "- text" marks a speaker-change boundary (WebVTT/newer SRT).
        raw_text = block["text"]
        if raw_text.startswith("- "):
            flush()
            raw_text = raw_text[2:].strip()
            if not raw_text or SKIP_REGEX.search(raw_text):
                continue
            current_label = None
            current_start = block["start"]
            current_words = [raw_text]
            continue

        label, text = extract_speaker_label(raw_text)

        if not text:
            continue

        # If current passage is empty (start of transcript or after skip/flush),
        # always start fresh — don't inherit a None start timestamp.
        if not current_words:
            current_label = label
            current_start = block["start"]
            current_words = [text]
            continue

        # If a new speaker label appears, flush and start a new passage.
        if label is not None and label != current_label:
            flush()
            current_label = label
            current_start = block["start"]
            current_words = [text]
        else:
            # Continuation — same speaker (or unlabeled continuation)
            current_words.append(text)

    flush()
    return passages


# ---------------------------------------------------------------------------
# Theme assignment
# ---------------------------------------------------------------------------

def assign_themes(text: str) -> list[str]:
    """
    Return 2–5 theme tags based on keyword presence in the passage text.
    Falls back to ["success", "leadership"] if nothing matches.
    """
    text_lower = text.lower()
    scores: dict[str, int] = {}

    for theme, keywords in THEME_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[theme] = scores.get(theme, 0) + 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    themes = [t for t, _ in ranked[:5]]

    if len(themes) < 2:
        # Ensure at least 2 tags even with sparse keyword matches
        defaults = ["success", "leadership"]
        for d in defaults:
            if d not in themes:
                themes.append(d)
            if len(themes) >= 2:
                break

    return themes[:5]


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def next_ids(existing: list[dict], count: int) -> list[str]:
    """
    Generate `count` sequential IDs for today's date, continuing from the
    highest existing ID for today if any.
    Format: YYYY-MM-DD-NNN
    """
    today = date.today().isoformat()
    prefix = f"{today}-"

    highest = 0
    for q in existing:
        qid = q.get("id", "")
        if qid.startswith(prefix):
            try:
                n = int(qid[len(prefix):])
                highest = max(highest, n)
            except ValueError:
                pass

    return [f"{today}-{highest + i + 1:03d}" for i in range(count)]


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def split_into_quotes(text: str, min_words: int, max_words: int) -> list[str]:
    """
    Split a long passage into quote-sized chunks at sentence boundaries.
    Each chunk will be between min_words and max_words in length.
    """
    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks: list[str] = []
    current: list[str] = []
    current_wc = 0

    for sentence in sentences:
        swc = len(sentence.split())
        # If adding this sentence would exceed max_words AND we already have enough
        if current_wc + swc > max_words and current_wc >= min_words:
            chunks.append(" ".join(current))
            current = [sentence]
            current_wc = swc
        else:
            current.append(sentence)
            current_wc += swc

    if current:
        joined = " ".join(current)
        if len(joined.split()) >= min_words:
            chunks.append(joined)

    return chunks


def detect_guest_labels(speaker: str) -> set[str]:
    """
    Derive likely SRT speaker labels from the speaker's name.
    e.g. "Jim Cramer" → {"jim", "cramer"}, "Dr. Shefali" → {"shefali", "dr"}
    """
    parts = re.split(r"[\s.\-]+", speaker.upper())
    return {p.lower() for p in parts if len(p) > 2}


def extract_from_srt(
    srt_path: Path,
    speaker: str,
    episode: str,
    broadcast_date: str,
    speaker_type: str,
    min_words: int,
    max_words: int = 200,
) -> list[dict]:
    """
    Parse one SRT file and return a list of quote dicts (without id/addedDate).

    Guest detection: derives likely SRT speaker labels from the speaker name
    (e.g. "Jim Cramer" → looks for CRAMER: labels). None-labeled passages that
    appear before the first guest-labeled block are treated as host content and
    excluded. None-labeled passages after the first guest block are included
    (guests frequently speak in long unlabeled runs after an initial label).
    """
    raw = srt_path.read_text(encoding="utf-8", errors="replace")
    blocks = parse_srt(raw)
    passages = join_blocks(blocks)

    # Find the index of the first passage labeled as the guest
    guest_labels = detect_guest_labels(speaker)
    first_guest_idx: int | None = None
    for i, p in enumerate(passages):
        if p["label"] in guest_labels:
            first_guest_idx = i
            break

    quotes = []
    for i, passage in enumerate(passages):
        label = passage["label"]
        text = passage["text"].strip()

        # Always skip known host labels and non-speech content
        if should_skip(text, label):
            continue

        # Skip unlabeled passages that come before the guest's first appearance
        # (these are typically host announcements/intros)
        if label is None and first_guest_idx is not None and i < first_guest_idx:
            continue

        word_count = len(text.split())
        if word_count < min_words:
            continue

        # Split long passages into quote-sized chunks
        chunks = split_into_quotes(text, min_words, max_words)
        for chunk in chunks:
            quotes.append({
                "speaker": speaker,
                "speakerType": speaker_type,
                "text": chunk,
                "episode": episode,
                "date": broadcast_date,
                "timestamp": passage["start"],
                "sourceFile": srt_path.name,
                "themes": assign_themes(chunk),
            })

    return quotes


# ---------------------------------------------------------------------------
# Metadata prompting
# ---------------------------------------------------------------------------

def prompt_metadata(srt_path: Path, speaker_type: str, args) -> dict | None:
    """
    Collect required metadata for a file, either from CLI flags or interactively.
    Returns None if the user skips the file.
    """
    print(f"\n{'='*60}")
    print(f"File: {srt_path.name}")
    print(f"{'='*60}")

    # Speaker
    if args.speaker:
        speaker = args.speaker
    else:
        speaker = input("  Speaker full name (or 's' to skip): ").strip()
        if speaker.lower() == "s":
            print("  Skipped.")
            return None

    # Episode
    if args.episode:
        episode = args.episode
    else:
        default_episode = f"NSLS Speaker Broadcast — {speaker}"
        ep_input = input(f"  Episode name [{default_episode}]: ").strip()
        episode = ep_input if ep_input else default_episode

    # Date
    if args.date:
        broadcast_date = args.date
    else:
        broadcast_date = input("  Broadcast year (e.g. 2024): ").strip() or "unknown"

    return {
        "speaker": speaker,
        "episode": episode,
        "date": broadcast_date,
        "speaker_type": speaker_type,
    }


# ---------------------------------------------------------------------------
# Database read/write
# ---------------------------------------------------------------------------

def load_db() -> list[dict]:
    if not QUOTES_DB.exists():
        return []
    with open(QUOTES_DB, encoding="utf-8") as f:
        return json.load(f)


def save_db(quotes: list[dict]) -> None:
    with open(QUOTES_DB, "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract quotes from NSLS Speaker Broadcast SRT transcripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "path",
        help="Path to an SRT file or a directory of SRT files.",
    )
    parser.add_argument(
        "--speaker",
        help="Full name of the guest speaker (skips interactive prompt).",
    )
    parser.add_argument(
        "--episode",
        help='Episode name, e.g. "NSLS Speaker Broadcast — Jim Cramer".',
    )
    parser.add_argument(
        "--date",
        help='Broadcast year or date, e.g. "2024".',
    )
    parser.add_argument(
        "--speaker-type",
        dest="speaker_type",
        choices=VALID_SPEAKER_TYPES,
        default="speaker-broadcast",
        help="Speaker category (default: speaker-broadcast).",
    )
    parser.add_argument(
        "--min-words",
        dest="min_words",
        type=int,
        default=30,
        help="Minimum word count for a passage to be included (default: 30).",
    )
    parser.add_argument(
        "--max-words",
        dest="max_words",
        type=int,
        default=200,
        help="Maximum word count per quote — longer passages are split at sentence boundaries (default: 200).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and preview quotes but do NOT write to the database.",
    )
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"ERROR: Path not found: {target}", file=sys.stderr)
        sys.exit(1)

    # Collect SRT files
    if target.is_dir():
        srt_files = sorted(target.glob("*.srt"))
        if not srt_files:
            print(f"No .srt files found in {target}")
            sys.exit(0)
    else:
        srt_files = [target]

    # Load existing DB
    existing = load_db()
    ingested_sources = {q.get("sourceFile", "") for q in existing}

    total_added = 0
    all_new_quotes: list[dict] = []
    file_summaries: list[str] = []

    for srt_path in srt_files:
        if srt_path.name in ingested_sources:
            print(f"\nSkipping (already ingested): {srt_path.name}")
            file_summaries.append(f"  {srt_path.name}: SKIPPED (already in database)")
            continue

        meta = prompt_metadata(srt_path, args.speaker_type, args)
        if meta is None:
            file_summaries.append(f"  {srt_path.name}: SKIPPED (user)")
            continue

        print(f"  Parsing...", end=" ", flush=True)
        new_quotes = extract_from_srt(
            srt_path=srt_path,
            speaker=meta["speaker"],
            episode=meta["episode"],
            broadcast_date=meta["date"],
            speaker_type=meta["speaker_type"],
            min_words=args.min_words,
            max_words=args.max_words,
        )
        print(f"{len(new_quotes)} passages found.")

        if args.dry_run:
            print(f"\n  --- DRY RUN PREVIEW ({len(new_quotes)} quotes) ---")
            for i, q in enumerate(new_quotes[:5], 1):
                print(f"\n  [{i}] ({q['timestamp']}) {q['text'][:120]}...")
                print(f"       Themes: {', '.join(q['themes'])}")
            if len(new_quotes) > 5:
                print(f"\n  ... and {len(new_quotes) - 5} more (not shown in preview)")
        else:
            all_new_quotes.extend(new_quotes)
            file_summaries.append(
                f"  {srt_path.name}: {len(new_quotes)} quotes — Speaker: {meta['speaker']}"
            )
            total_added += len(new_quotes)

    # Assign IDs and addedDate, write to DB
    if not args.dry_run and all_new_quotes:
        ids = next_ids(existing, len(all_new_quotes))
        today = date.today().isoformat()
        for i, q in enumerate(all_new_quotes):
            q["id"] = ids[i]
            q["addedDate"] = today

        merged = existing + all_new_quotes
        save_db(merged)

    # Summary
    print(f"\n{'='*60}")
    if args.dry_run:
        print("DRY RUN complete — database was NOT modified.")
    else:
        print("Ingestion complete.")
        print(f"\nFiles processed:")
        for s in file_summaries:
            print(s)
        print(f"\nQuotes added:       {total_added}")
        print(f"Total in database:  {len(existing) + total_added}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
