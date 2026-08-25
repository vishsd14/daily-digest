#!/usr/bin/env python3
"""Render digest.json -> index.html (single file, no external calls)."""
import html
import json
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


def render():
    with open("digest.json") as f:
        data = json.load(f)

    date_full = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%A, %B %d %Y")

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

    page = TEMPLATE.format(
        date=data["date"],
        date_full=date_full,
        generated_at=data["generated_at"],
        sections="".join(sections_html),
    )

    with open("index.html", "w") as f:
        f.write(page)

    print("[render] wrote index.html")


if __name__ == "__main__":
    render()
