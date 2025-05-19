#!/usr/bin/env python3
import argparse
import feedparser
import json
import os
import sys
import time
import unicodedata
from datetime import datetime, timedelta

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Remove accents and lowercase for consistent matching."""
    nk = unicodedata.normalize('NFKD', text)
    return nk.encode('ascii', 'ignore').decode('ascii').lower()

def parse_args():
    p = argparse.ArgumentParser(
        description="Fetch one RSS feed, filter by keywords & date, emit JSON."
    )
    p.add_argument(
        "--feed-url", required=True,
        help="The RSS/Atom feed URL to scrape."
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--since-days", type=int,
        help="How many days back to include (e.g. 1 = last 24h)."
    )
    group.add_argument(
        "--since-hours", type=int,
        help="How many hours back to include (e.g. 1 = last hour)."
    )
    p.add_argument(
        "--output", required=True,
        help="Path to write raw JSON."
    )
    return p.parse_args()

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    args = parse_args()

    # Time window
    now = datetime.now()
    if args.since_hours is not None:
        start_date = now - timedelta(hours=args.since_hours)
    else:
        start_date = now - timedelta(days=args.since_days)
    end_date = now

    print(f"⏱  Filtering entries from {start_date.isoformat()} to {end_date.isoformat()}")

    # Keywords to filter
    KEYWORDS = [
        "maiz", "sorgo", "girasol", "trigo", "importaciones",
        "importacion", "bioceres", "remingtom", "agidea",
        "corteva", "syngenta", "gdm", "los grobo",
        "limagrain", "rizobacter", "bayer"
    ]

    # Fetch & parse
    feed = feedparser.parse(args.feed_url)
    source = feed.feed.get("title", args.feed_url)

    results = []
    for entry in feed.entries:
        # try to get published time
        if not hasattr(entry, "published_parsed"):
            continue
        published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        if not (start_date <= published <= end_date):
            continue

        # text match
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        txt = normalize_text(title + " " + summary)
        if not any(normalize_text(k) in txt for k in KEYWORDS):
            continue

        results.append({
            "title": title,
            "link": entry.get("link", ""),
            "published": published.isoformat()
        })

    grouped = { source: results }

    # Write out raw JSON
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote {len(results)} items to {args.output}")

if __name__ == "__main__":
    main()
