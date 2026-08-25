"""
Source list, categorized. RSS feeds cover the publisher-side signal.
Reddit + HN cover practitioner/community signal.
AI Search / GEO has no mature RSS ecosystem yet, so that category leans
on a targeted web_search call inside digest.py instead of feeds.

Verify feed URLs on first run (see README) — publishers change these
without warning and a dead feed should log + skip, never crash the run.
"""

SOURCES = {
    "Technical SEO": {
        "rss": [
            "https://searchengineland.com/feed",
            "https://www.seroundtable.com/index.xml",
            "https://developers.google.com/search/blog/feed.xml",
            "https://ahrefs.com/blog/feed/",
            "https://moz.com/posts/rss/blog",
        ],
        "reddit": ["TechSEO", "SEO", "bigseo"],
    },
    "Digital Marketing / Martech": {
        "rss": [
            "https://www.searchenginejournal.com/feed/",
            "https://martech.org/feed/",
            "https://blog.hubspot.com/marketing/rss.xml",
            "https://contentmarketinginstitute.com/feed/",
        ],
        "reddit": ["marketing", "PPC", "digital_marketing"],
    },
    "AI Search / GEO": {
        "rss": [],  # deliberately empty — see note above
        "reddit": ["TechSEO", "SEO"],  # filtered by keyword at digest time
        "web_search_queries": [
            "AI Overviews SEO news",
            "ChatGPT search visibility SEO",
            "generative engine optimization news",
            "LLM citation AI search ranking",
        ],
    },
}

HN_QUERY_TERMS = ["SEO", "search engine", "Google algorithm", "AI search"]

# Weight relevance scoring toward what Vishnu actually works on —
# don't just dedupe/summarize, rank by client-vertical relevance.
RELEVANCE_CONTEXT = """
Prioritize items relevant to: enterprise/travel SEO (cruise, automotive),
AI search visibility and GEO, Google algorithm updates, technical SEO
(crawling, indexation, Core Web Vitals), and content strategy for
AI-answer surfaces. Deprioritize generic listicle/how-to content and
pure PPC/paid media unless it intersects organic strategy.
"""
