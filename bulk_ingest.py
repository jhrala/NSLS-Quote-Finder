#!/usr/bin/env python3
"""
Bulk ingester for NSLS Speaker Broadcast transcripts.

This script processes all .txt files in the srt_downloads/ folder and
extracts quotes into quotes.json non-interactively. Speaker metadata is
derived from the filename.

Usage:
    python3 bulk_ingest.py
    python3 bulk_ingest.py --dry-run
    python3 bulk_ingest.py --min-words 25 --max-words 200
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import date

import extract_quotes as eq

DOWNLOADS_DIR = Path(__file__).parent / "srt_downloads"

# Manually-curated metadata for known speakers.
# key: lowercase speaker name as it appears in the filename
# value: (full_name, approximate_year)
SPEAKER_META: dict[str, tuple[str, str]] = {
    "jim cramer":              ("Jim Cramer",             "2014"),
    "al roker":                ("Al Roker",               "2015"),
    "alexis jones":            ("Alexis Jones",           "2019"),
    "anderson cooper":         ("Anderson Cooper",        "2018"),
    "andy cohen":              ("Andy Cohen",             "2019"),
    "anita hill":              ("Anita Hill",             "2021"),
    "arianna huffington":      ("Arianna Huffington",     "2016"),
    "barbara corcoran":        ("Barbara Corcoran",       "2018"),
    "bill nye":                ("Bill Nye",               "2017"),
    "blake mycoskie":          ("Blake Mycoskie",         "2016"),
    "bozoma saint john":       ("Bozoma Saint John",      "2022"),
    "brene brown":             ("Brené Brown",            "2023"),
    "carly fiorina":           ("Carly Fiorina",          "2016"),
    "carla hall":              ("Carla Hall",             "2019"),
    "curt menefee":            ("Curt Menefee",           "2017"),
    "dan harris":              ("Dan Harris",             "2016"),
    "debbi fields":            ("Debbi Fields",           "2020"),
    "dr. deepak chopra":       ("Dr. Deepak Chopra",      "2015"),
    "dr. shefali":             ("Dr. Shefali",            "2022"),
    "emily balcetis":          ("Emily Balcetis",         "2023"),
    "frank caprio":            ("Frank Caprio",           "2024"),
    "goldie hawn":             ("Goldie Hawn",            "2018"),
    "hoda kotb":               ("Hoda Kotb",              "2023"),
    "jack black":              ("Jack Black",             "2018"),
    "jack canfield":           ("Jack Canfield",          "2016"),
    "jamie foxx":              ("Jamie Foxx",             "2017"),
    "jesse eisenberg":         ("Jesse Eisenberg",        "2018"),
    "jim kouzes":              ("Jim Kouzes",             "2022"),
    "john leguizamo":          ("John Leguizamo",         "2019"),
    "john maxwell":            ("John Maxwell",           "2014"),
    "jonathan sprinkles":      ("Jonathan Sprinkles",     "2022"),
    "juju chang":              ("Juju Chang",             "2018"),
    "kat cole":                ("Kat Cole",               "2017"),
    "kate mckinnon":           ("Kate McKinnon",          "2025"),
    "kelly ripa":              ("Kelly Ripa",             "2017"),
    "ketanji brown jackson":   ("Ketanji Brown Jackson",  "2023"),
    "kevin bacon":             ("Kevin Bacon",            "2024"),
    "kevin hart":              ("Kevin Hart",             "2024"),
    "malcolm gladwell":        ("Malcolm Gladwell",       "2025"),
    "marc kielburger":         ("Marc Kielburger",        "2020"),
    "marc randolph":           ("Marc Randolph",          "2021"),
    "marcia clark":            ("Marcia Clark",           "2016"),
    "matthew mcconaughey 1":   ("Matthew McConaughey",   "2022"),
    "matthew mcconaughey_ 2":  ("Matthew McConaughey",   "2023"),
    "matthew mcconaughey 2":   ("Matthew McConaughey",   "2023"),
    "mehdi hasan":             ("Mehdi Hasan",            "2023"),
    "neil patrick harris":     ("Neil Patrick Harris",   "2018"),
    "oprah winfrey":           ("Oprah Winfrey",         "2024"),
    "paul orfalea":            ("Paul Orfalea",           "2015"),
    "rachael ray":             ("Rachael Ray",            "2018"),
    "robert gates":            ("Robert Gates",           "2016"),
    "rohit bhargava":          ("Rohit Bhargava",         "2021"),
    "ryan serhant":            ("Ryan Serhant",           "2024"),
    "scott hamilton":          ("Scott Hamilton",         "2017"),
    "simon sinek":             ("Simon Sinek",            "2019"),
    "slava rubin":             ("Slava Rubin",            "2022"),
    "steve madden":            ("Steve Madden",           "2018"),
    "suze orman":              ("Suze Orman",             "2016"),
    "sylvester stallone":      ("Sylvester Stallone",    "2024"),
    "tanya acker":             ("Tanya Acker",            "2019"),
    "tiki barber":             ("Tiki Barber",            "2018"),
    "tom krieglstein":         ("Tom Krieglstein",        "2022"),
    "tony hsieh":              ("Tony Hsieh",             "2017"),
    "trevor noah":             ("Trevor Noah",            "2018"),
    "valerie jarrett":         ("Valerie Jarrett",        "2018"),
    "wendy williams":          ("Wendy Williams",         "2016"),
    "andrew yang":             ("Andrew Yang",            "2021"),
    "barack obama":            ("Barack Obama",           "2022"),
}


def parse_speaker_from_filename(title: str) -> str:
    """
    Extract the speaker key from a filename like:
      "NSLS_Speaker Broadcast_Jim Cramer"
      "NSLS_Speaker Broadcasts_Debbi Fields"
    Returns lowercase speaker portion.
    """
    # Strip extension
    title = Path(title).stem

    # Remove leading prefix variations
    title = re.sub(r"^NSLS_Speaker Broadcasts?_", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^NSLS_Speaker Broadcast_", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^NSLS Broadcast ", "", title, flags=re.IGNORECASE)

    return title.strip().lower()


def lookup_meta(speaker_key: str) -> tuple[str, str]:
    """Return (full_name, year) from SPEAKER_META, falling back to title-cased key."""
    if speaker_key in SPEAKER_META:
        return SPEAKER_META[speaker_key]
    # Fallback: title-case the key
    full_name = " ".join(w.capitalize() for w in speaker_key.split())
    return full_name, "unknown"


def main():
    parser = argparse.ArgumentParser(description="Bulk ingest srt_downloads/ into quotes.json")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument("--min-words", dest="min_words", type=int, default=30)
    parser.add_argument("--max-words", dest="max_words", type=int, default=200)
    args = parser.parse_args()

    txt_files = sorted(DOWNLOADS_DIR.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {DOWNLOADS_DIR}")
        sys.exit(0)

    print(f"Found {len(txt_files)} files in srt_downloads/\n")

    existing = eq.load_db()
    ingested_sources = {q.get("sourceFile", "") for q in existing}

    all_new_quotes: list[dict] = []
    summaries: list[str] = []

    for f in txt_files:
        if f.name in ingested_sources:
            print(f"  SKIP (already ingested): {f.name}")
            summaries.append(f"  {f.name}: SKIPPED")
            continue

        speaker_key = parse_speaker_from_filename(f.name)
        full_name, year = lookup_meta(speaker_key)
        episode = f"NSLS Speaker Broadcast — {full_name}"

        print(f"  Processing: {f.name}")
        print(f"    Speaker: {full_name} | Year: {year}", end=" | ")

        try:
            quotes = eq.extract_from_srt(
                srt_path=f,
                speaker=full_name,
                episode=episode,
                broadcast_date=year,
                speaker_type="speaker-broadcast",
                min_words=args.min_words,
                max_words=args.max_words,
            )
            print(f"{len(quotes)} quotes")
            all_new_quotes.extend(quotes)
            summaries.append(f"  {f.name}: {len(quotes)} quotes — {full_name}")
        except Exception as e:
            print(f"ERROR: {e}")
            summaries.append(f"  {f.name}: ERROR — {e}")

    if not args.dry_run and all_new_quotes:
        ids = eq.next_ids(existing, len(all_new_quotes))
        today = date.today().isoformat()
        for i, q in enumerate(all_new_quotes):
            q["id"] = ids[i]
            q["addedDate"] = today
        merged = existing + all_new_quotes
        eq.save_db(merged)

    print(f"\n{'='*60}")
    if args.dry_run:
        print("DRY RUN — database not modified")
    else:
        print("Ingestion complete.")
    print(f"\nFiles processed:")
    for s in summaries:
        print(s)
    total = len(existing) + len(all_new_quotes)
    print(f"\nQuotes added:      {len(all_new_quotes)}")
    print(f"Total in database: {total if not args.dry_run else len(existing)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
