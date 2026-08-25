#!/usr/bin/env python3
"""
Daily SEO / Digital Marketing digest engine.

Pulls RSS + Reddit + HN + targeted web search, dedupes, then hands the
raw pool to Claude for categorization, relevance scoring, and 1-2 line
summaries. Outputs digest.json for render.py to turn into the HTML page.

Env vars required:
  ANTHROPIC_API_KEY

Usage:
  python3 digest.py
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests
import anthropic

from sources import SOURCES, HN_QUERY_TERMS, RELEVANCE_CONTEXT

LOOKBACK_HOURS = 26  # small overlap on 24h to avoid gaps from cron drift
MODEL = "claude-sonnet-4-6"


def log(msg):
    print(f"[digest] {msg}", file=sys.stderr)


def within_lookback(struct_time):
    if not struct_time:
        return True  # no date info — keep it, let the model filter relevance
    published = datetime(*struct_time[:6], tzinfo=timezone.utc)
    return published > datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)


def pull_rss(category, feeds):
    items = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                log(f"SKIP dead/unreachable feed: {url}")
                continue
            for entry in parsed.entries[:15]:
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                if not within_lookback(pub):
                    continue
                items.append({
                    "category_hint": category,
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", ""),
                    "source": parsed.feed.get("title", url),
                    "snippet": entry.get("summary", "")[:400],
                })
        except Exception as e:
            log(f"SKIP feed error {url}: {e}")
    return items


def pull_reddit(category, subreddits):
    items = []
    headers = {"User-Agent": "daily-digest/1.0"}
    for sub in subreddits:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/top.json",
                params={"t": "day", "limit": 10},
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            for post in r.json()["data"]["children"]:
                d = post["data"]
                if d.get("stickied"):
                    continue
                items.append({
                    "category_hint": category,
                    "title": d.get("title", "").strip(),
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "source": f"r/{sub}",
                    "snippet": d.get("selftext", "")[:400],
                    "engagement": d.get("score", 0),
                })
        except Exception as e:
            log(f"SKIP reddit r/{sub}: {e}")
        time.sleep(1)  # be polite, avoid rate limit
    return items


def pull_hn():
    items = []
    since = int((datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).timestamp())
    for term in HN_QUERY_TERMS:
        try:
            r = requests.get(
                "https://hn.algolia.com/api/v1/search_by_date",
                params={"query": term, "tags": "story", "numericFilters": f"created_at_i>{since}"},
                timeout=10,
            )
            r.raise_for_status()
            for hit in r.json().get("hits", [])[:5]:
                items.append({
                    "category_hint": "AI Search / GEO",
                    "title": hit.get("title", ""),
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "source": "Hacker News",
                    "snippet": "",
                    "engagement": hit.get("points", 0),
                })
        except Exception as e:
            log(f"SKIP HN term '{term}': {e}")
    return items


def pull_web_search(client, queries):
    """Targeted web_search for AI Search/GEO — thin RSS ecosystem here."""
    items = []
    for q in queries:
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{
                    "role": "user",
                    "content": (
                        f"Search for: {q} — last 24 hours only. "
                        "Return only real results you found via search, nothing from memory."
                    ),
                }],
            )
            for block in resp.content:
                if block.type == "web_search_tool_result":
                    for result in getattr(block, "content", []):
                        items.append({
                            "category_hint": "AI Search / GEO",
                            "title": getattr(result, "title", ""),
                            "url": getattr(result, "url", ""),
                            "source": "web search",
                            "snippet": "",
                        })
        except Exception as e:
            log(f"SKIP web_search '{q}': {e}")
    return items


def dedupe(items):
    seen = set()
    out = []
    for it in items:
        key = it["url"] or it["title"].lower()
        if key in seen or not it["title"]:
            continue
        seen.add(key)
        out.append(it)
    return out


def categorize_and_summarize(client, items):
    """
    Single Claude call: categorize, score relevance, summarize.
    Explicit fabrication-risk guardrail — same discipline as the
    fanout auditor's outline-depth issue: never invent a number, date,
    or claim not present in the title/snippet/source.
    """
    if not items:
        return {"Technical SEO": [], "Digital Marketing / Martech": [], "AI Search / GEO": []}

    payload = json.dumps(items, indent=2)[:60000]  # guard against oversized prompt

    prompt = f"""You are curating a daily digest for a Tech SEO Manager who runs
enterprise SEO + GEO/AI-search work.

{RELEVANCE_CONTEXT}

Raw pool of {len(items)} items (RSS/Reddit/HN/web search results) below. For each
item worth keeping:
- Assign it to exactly one category: "Technical SEO", "Digital Marketing / Martech", or "AI Search / GEO"
- Write a 1-2 sentence summary using ONLY facts present in the title/snippet — never invent
  a statistic, date, percentage, or quote that isn't there. If the snippet is empty, summarize
  from the title alone and keep it short and literal.
- Score relevance 1-5 (5 = directly actionable for enterprise/travel SEO, GEO, or algorithm
  updates; 1 = generic/low-value)
- Drop items scoring below 3 entirely — this is a curated digest, not a feed reader
- Drop exact or near-duplicate stories, keeping the best-sourced version
- Cap at 8 items per category, ranked by relevance score descending

Return ONLY valid JSON, no preamble, no markdown fences, in this exact shape:
{{
  "Technical SEO": [{{"title": "...", "url": "...", "source": "...", "summary": "...", "relevance": 5}}],
  "Digital Marketing / Martech": [...],
  "AI Search / GEO": [...]
}}

Raw items:
{payload}
"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"Claude returned non-JSON, dumping raw for debugging: {e}")
        log(raw[:2000])
        raise


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log("FATAL: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    all_items = []
    for category, cfg in SOURCES.items():
        if cfg.get("rss"):
            all_items += pull_rss(category, cfg["rss"])
        if cfg.get("reddit"):
            all_items += pull_reddit(category, cfg["reddit"])
        if cfg.get("web_search_queries"):
            all_items += pull_web_search(client, cfg["web_search_queries"])

    all_items += pull_hn()

    log(f"Pulled {len(all_items)} raw items before dedupe")
    all_items = dedupe(all_items)
    log(f"{len(all_items)} items after dedupe, sending to Claude for curation")

    digest = categorize_and_summarize(client, all_items)

    output = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "categories": digest,
    }

    with open("digest.json", "w") as f:
        json.dump(output, f, indent=2)

    total = sum(len(v) for v in digest.values())
    log(f"Wrote digest.json — {total} items across {len(digest)} categories")


if __name__ == "__main__":
    main()
