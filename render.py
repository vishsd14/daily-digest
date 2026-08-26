#!/usr/bin/env python3
"""Render digest.json -> index.html (single file, no external calls)."""
import html
import json
import os
from datetime import datetime

CATEGORY_ORDER = ["Technical SEO", "AI Search / GEO", "Digital Marketing / Martech"]

CATEGORY_ICON = {
    "Technical SEO": "⚙",
    "AI Search / GEO": "◈",
    "Digital Marketing / Martech": "▲",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Digest · {date}</title>
<style>
  :root {{
    --bg: #14120f;
    --bg-card: #1c1a16;
    --amber: #d99b4a;
    --amber-soft: #b9853f;
    --ink: #ece7dd;
    --ink-soft: #9a9488;
    --hairline: #2c2924;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.5;
  }}
  .wrap {{ max-width: 760px; margin: 0 auto; padding: 48px 20px 80px; }}
  header {{ margin-bottom: 40px; }}
  .eyebrow {{
    color: var(--amber);
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
  }}
  h1 {{ font-size: 28px; margin: 6px 0 4px; font-weight: 700; }}
  .subdate {{ color: var(--ink-soft); font-size: 14px; }}
  section {{ margin-bottom: 36px; }}
  .cat-heading {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 600;
    color: var(--amber);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid var(--hairline);
    padding-bottom: 8px;
    margin-bottom: 14px;
  }}
  .item {{
    background: var(--bg-card);
    border: 1px solid var(--hairline);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
  }}
  .item a {{
    color: var(--ink);
    text-decoration: none;
    font-weight: 600;
    font-size: 15px;
  }}
  .item a:hover {{ color: var(--amber); }}
  .item .source {{
    color: var(--amber-soft);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 2px;
  }}
  .item .summary {{
    color: var(--ink-soft);
    font-size: 13.5px;
    margin-top: 6px;
  }}
  .empty {{ color: var(--ink-soft); font-size: 14px; font-style: italic; }}
  .archive-list {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .archive-link {{
    color: var(--ink-soft);
    font-size: 12px;
    text-decoration: none;
    border: 1px solid var(--hairline);
    border-radius: 6px;
    padding: 4px 10px;
  }}
  .archive-link:hover {{ color: var(--amber); border-color: var(--amber-soft); }}
  footer {{
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid var(--hairline);
    color: var(--ink-soft);
    font-size: 12px;
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">SEO / Digital Marketing</div>
    <h1>Daily Digest</h1>
    <div class="subdate">{date_full}</div>
  </header>
  {sections}
  {archive_nav}
  <footer>Generated automatically · {generated_at}</footer>
</div>
</body>
</html>
"""

SECTION_TEMPLATE = """
<section>
  <div class="cat-heading">{icon} {category}</div>
  {items}
</section>
"""

ITEM_TEMPLATE = """
  <div class="item">
    <a href="{url}" target="_blank" rel="noopener">{title}</a>
    <div class="source">{source}</div>
    <div class="summary">{summary}</div>
  </div>
"""

EMPTY_TEMPLATE = '<div class="empty">Nothing scored relevant today.</div>'

ARCHIVE_NAV_TEMPLATE = """
<section>
  <div class="cat-heading">Past digests</div>
  <div class="archive-list">{links}</div>
</section>
"""

ARCHIVE_LINK_TEMPLATE = '<a class="archive-link" href="archive/{date}/">{date}</a>'


def build_sections(data):
    sections_html = []
    for category in CATEGORY_ORDER:
        items = data["categories"].get(category, [])
        if items:
            items_html = "".join(
                ITEM_TEMPLATE.format(
                    url=html.escape(it["url"]),
                    title=html.escape(it["title"]),
                    source=html.escape(it["source"]),
                    summary=html.escape(it["summary"]),
                )
                for it in items
            )
        else:
            items_html = EMPTY_TEMPLATE

        sections_html.append(SECTION_TEMPLATE.format(
            icon=CATEGORY_ICON.get(category, "•"),
            category=html.escape(category),
            items=items_html,
        ))
    return "".join(sections_html)


def past_archive_dates(today, limit=14):
    """Scan archive/ for existing dated folders, excluding today, most recent first."""
    if not os.path.isdir("archive"):
        return []
    dates = sorted(
        d for d in os.listdir("archive")
        if os.path.isdir(os.path.join("archive", d)) and d != today
    )
    return list(reversed(dates))[:limit]


def render():
    with open("digest.json") as f:
        data = json.load(f)

    date_full = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%A, %B %d %Y")
    sections = build_sections(data)

    # Archive copy — permanent, dated, never overwritten. This is what
    # keeps a shared link from going stale once other people bookmark it.
    archive_dir = os.path.join("archive", data["date"])
    os.makedirs(archive_dir, exist_ok=True)
    archive_page = TEMPLATE.format(
        date=data["date"], date_full=date_full,
        generated_at=data["generated_at"], sections=sections, archive_nav="",
    )
    with open(os.path.join(archive_dir, "index.html"), "w") as f:
        f.write(archive_page)

    # Root page — always "today", plus a nav back through past days.
    past_dates = past_archive_dates(data["date"])
    if past_dates:
        links = "".join(ARCHIVE_LINK_TEMPLATE.format(date=d) for d in past_dates)
        archive_nav = ARCHIVE_NAV_TEMPLATE.format(links=links)
    else:
        archive_nav = ""

    root_page = TEMPLATE.format(
        date=data["date"], date_full=date_full,
        generated_at=data["generated_at"], sections=sections, archive_nav=archive_nav,
    )
    with open("index.html", "w") as f:
        f.write(root_page)

    print(f"[render] wrote index.html + archive/{data['date']}/index.html ({len(past_dates)} past days linked)")


if __name__ == "__main__":
    render()
