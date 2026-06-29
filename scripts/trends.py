#!/usr/bin/env python3
"""
Trend monitor for niche-aware ad campaign orchestration.

Polls one or more RSS/Atom feeds, extracts candidate topics, scores them by
relevance to a niche keyword set and recency, and emits ranked JSON for the
ads-orchestrate pipeline. No API keys required; feeds are user-supplied so the
tool stays self-hosted and credential-free.

Usage:
    python trends.py --niche perfume
    python trends.py --niche perfume --feeds feeds.txt --output trends.json
    python trends.py --niche "perfume,fragrance,niche scent" --top 10
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from url_utils import sanitize_error, sanitize_url, validate_url

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install -r requirements.txt")
    sys.exit(1)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ClaudeAds/1.7; +https://github.com/AI-Marketing-Hub/claude-ads)",
    "Accept": "application/rss+xml,application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Niche-agnostic feeds; perfume defaults so the demo runs out of the box.
DEFAULT_FEEDS = [
    "https://www.fragrantica.com/news/rss.xml",
    "https://news.google.com/rss/search?q=perfume+fragrance",
]


def _parse_date(value: str):
    """Best-effort RFC822/ISO date parse; returns aware datetime or None."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_feed(url: str, timeout: int = 20) -> list:
    """Fetch and parse one RSS/Atom feed into title/link/date items."""
    validate_url(url)  # SSRF guard: rejects private/loopback/metadata hosts
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    resp.raise_for_status()
    root = ElementTree.fromstring(resp.content)
    items = []
    for node in root.iter():
        tag = node.tag.split("}")[-1].lower()
        if tag in ("item", "entry"):
            title = link = pub = ""
            for child in node:
                ctag = child.tag.split("}")[-1].lower()
                if ctag == "title":
                    title = (child.text or "").strip()
                elif ctag == "link":
                    link = (child.text or child.get("href") or "").strip()
                elif ctag in ("pubdate", "published", "updated"):
                    pub = (child.text or "").strip()
            if title:
                items.append({"title": title, "link": link, "published": pub})
    return items


def score_topics(items: list, keywords: list, top: int) -> list:
    """Rank items by keyword relevance x recency. Returns top N topics."""
    now = datetime.now(timezone.utc)
    kw = [k.lower() for k in keywords if k]
    scored = []
    for it in items:
        text = it["title"].lower()
        relevance = sum(1 for k in kw if k in text)
        if relevance == 0:
            continue
        dt = _parse_date(it["published"])
        recency = 1.0
        if dt:
            age_days = max((now - dt.astimezone(timezone.utc)).days, 0)
            recency = 1.0 / (1 + age_days)
        scored.append({
            "topic": it["title"],
            "link": sanitize_url(it["link"]),
            "relevance": relevance,
            "recency": round(recency, 3),
            "score": round(relevance * recency, 3),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top]


def monitor(niche: str, feeds: list, top: int = 10) -> dict:
    """Run the trend monitor over feeds and return ranked JSON."""
    keywords = [k.strip() for k in re.split(r"[,;]", niche) if k.strip()]
    all_items, errors = [], []
    for feed in feeds:
        try:
            all_items.extend(fetch_feed(feed))
        except Exception as e:  # noqa: BLE001 - report per-feed, keep going
            errors.append({"feed": sanitize_url(feed), "error": sanitize_error(e)})
    return {
        "niche": niche,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topics": score_topics(all_items, keywords, top),
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Niche trend monitor (JSON output)")
    parser.add_argument("--niche", default="perfume", help="Comma-separated keywords")
    parser.add_argument("--feeds", help="File with one feed URL per line")
    parser.add_argument("--top", type=int, default=10, help="Max topics to return")
    parser.add_argument("--output", "-o", help="Write JSON to file")
    args = parser.parse_args()

    feeds = DEFAULT_FEEDS
    if args.feeds:
        with open(args.feeds, encoding="utf-8") as f:
            feeds = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    result = monitor(args.niche, feeds, args.top)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"Saved {len(result['topics'])} topics to {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
