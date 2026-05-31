"""
fetch_live_news.py
------------------
Fetches current, real-world news articles and saves them as live_news.csv.

Labels assigned per source:
  0 = Highly Deceptive — fact-checked DEBUNKED / FALSE / PANTS-FIRE claims
  1 = Misleading       — fact-checked MISLEADING / HALF-TRUE / BARELY-TRUE claims
  2 = Legitimate       — reputable news outlets (all categories)

Sources (all free, no mandatory API key):
  1. Legitimate RSS feeds — Politics, Tech, Business, Science, Health,
                            Entertainment, Gaming, Sports, Environment,
                            India/World News                              → label 2
  2. Fact-checking RSS feeds — Snopes, PolitiFact, FullFact, etc.        → label 0/1
  3. GDELT Document API — current news (all categories)                  → label 2
  4. GDELT historical (2020–2025) — all categories + misinfo             → label 0/1/2
  5. Google Fact Check Tools API (optional — GOOGLE_FC_KEY)              → label 0/1
  6. NewsAPI all categories (optional — NEWS_API_KEY)                    → label 2

Usage:
  python src/fetch_live_news.py                        # live RSS + GDELT current
  python src/fetch_live_news.py --history              # + GDELT misinfo 2022-2025
  python src/fetch_live_news.py --history-full         # + GDELT ALL categories 2020-2025
  python src/fetch_live_news.py --no-sports            # skip sports feeds
  python src/fetch_live_news.py --no-balance           # disable class balancing
  python src/fetch_live_news.py --newsapi-key KEY --google-fc-key KEY
"""

import argparse
import os
import re
import time

import pandas as pd
import requests

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("[WARN] feedparser not installed — RSS feeds skipped. Run: pip install feedparser")

# ─────────────────────────────────────────────────────────────────────────────
# RSS FEEDS  (label = 2, Legitimate)
# ─────────────────────────────────────────────────────────────────────────────

# ── General / World News ──────────────────────────────────────────────────────
WORLD_NEWS_FEEDS = [
    ("BBC News",              "http://feeds.bbci.co.uk/news/rss.xml",                         2),
    ("BBC World",             "http://feeds.bbci.co.uk/news/world/rss.xml",                   2),
    ("Reuters Top News",      "https://feeds.reuters.com/reuters/topNews",                     2),
    ("Reuters World",         "https://feeds.reuters.com/reuters/worldNews",                   2),
    ("Associated Press",      "https://feeds.apnews.com/rss/apf-topnews",                     2),
    ("Al Jazeera",            "https://www.aljazeera.com/xml/rss/all.xml",                    2),
    ("NPR News",              "https://feeds.npr.org/1001/rss.xml",                           2),
    ("DW News",               "https://rss.dw.com/rdf/rss-en-all",                            2),
    ("France 24",             "https://www.france24.com/en/rss",                              2),
    ("The Hindu",             "https://www.thehindu.com/news/feeder/default.rss",             2),
    ("Times of India",        "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",   2),
    ("NDTV India",            "https://feeds.feedburner.com/ndtvnews-top-stories",            2),
    ("India Today",           "https://www.indiatoday.in/rss/home",                           2),
    ("The Wire",              "https://thewire.in/rss-feed",                                  2),
]

# ── Politics ──────────────────────────────────────────────────────────────────
POLITICS_FEEDS = [
    ("BBC Politics",          "http://feeds.bbci.co.uk/news/politics/rss.xml",                2),
    ("Reuters Politics",      "https://feeds.reuters.com/reuters/politicsNews",               2),
    ("The Guardian Politics", "https://www.theguardian.com/politics/rss",                     2),
    ("The Hill",              "https://thehill.com/homenews/feed/",                           2),
    ("Politico",              "https://www.politico.com/rss/politicopicks.xml",               2),
    ("NPR Politics",          "https://feeds.npr.org/1014/rss.xml",                          2),
    ("Al Jazeera Politics",   "https://www.aljazeera.com/tag/politics/feed",                  2),
    ("The Hindu Politics",    "https://www.thehindu.com/news/national/?service=rss",          2),
    ("BBC India",             "http://feeds.bbci.co.uk/news/world/south_asia/rss.xml",        2),
]

# ── Technology ────────────────────────────────────────────────────────────────
TECH_FEEDS = [
    ("BBC Technology",        "http://feeds.bbci.co.uk/news/technology/rss.xml",              2),
    ("Reuters Technology",    "https://feeds.reuters.com/reuters/technologyNews",             2),
    ("TechCrunch",            "https://techcrunch.com/feed/",                                 2),
    ("Wired",                 "https://www.wired.com/feed/rss",                               2),
    ("Ars Technica",          "https://feeds.arstechnica.com/arstechnica/index",              2),
    ("The Verge",             "https://www.theverge.com/rss/index.xml",                       2),
    ("MIT Tech Review",       "https://www.technologyreview.com/stories.rss",                 2),
    ("The Guardian Tech",     "https://www.theguardian.com/technology/rss",                   2),
    ("Hacker News (top)",     "https://hnrss.org/frontpage",                                  2),
    ("ZDNet",                 "https://www.zdnet.com/news/rss.xml",                           2),
    ("NDTV Gadgets",          "https://gadgets.ndtv.com/rss/feeds",                           2),
]

# ── Business & Finance ────────────────────────────────────────────────────────
BUSINESS_FEEDS = [
    ("BBC Business",          "http://feeds.bbci.co.uk/news/business/rss.xml",                2),
    ("Reuters Business",      "https://feeds.reuters.com/reuters/businessNews",               2),
    ("CNBC Top News",         "https://www.cnbc.com/id/100003114/device/rss/rss.html",        2),
    ("Forbes",                "https://www.forbes.com/news/feed/",                            2),
    ("MarketWatch",           "https://feeds.marketwatch.com/marketwatch/topstories/",        2),
    ("Economic Times",        "https://economictimes.indiatimes.com/rssfeedsdefault.cms",     2),
    ("Business Standard",     "https://www.business-standard.com/rss/home_page_top_stories.rss", 2),
    ("Mint",                  "https://www.livemint.com/rss/news",                            2),
    ("Financial Express",     "https://www.financialexpress.com/feed/",                       2),
    ("NPR Business",          "https://feeds.npr.org/1006/rss.xml",                          2),
]

# ── Science & Space ───────────────────────────────────────────────────────────
SCIENCE_FEEDS = [
    ("BBC Science",           "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", 2),
    ("Reuters Science",       "https://feeds.reuters.com/reuters/scienceNews",                2),
    ("Science Daily",         "https://www.sciencedaily.com/rss/all.xml",                    2),
    ("New Scientist",         "https://www.newscientist.com/feed/home",                       2),
    ("NASA Breaking News",    "https://www.nasa.gov/rss/dyn/breaking_news.rss",              2),
    ("Space.com",             "https://www.space.com/feeds/all",                              2),
    ("The Guardian Science",  "https://www.theguardian.com/science/rss",                     2),
    ("NPR Science",           "https://feeds.npr.org/1007/rss.xml",                          2),
    ("Phys.org",              "https://phys.org/rss-feed/",                                  2),
]

# ── Health & Medicine ─────────────────────────────────────────────────────────
HEALTH_FEEDS = [
    ("BBC Health",            "http://feeds.bbci.co.uk/news/health/rss.xml",                  2),
    ("Reuters Health",        "https://feeds.reuters.com/reuters/healthNews",                 2),
    ("NPR Health",            "https://feeds.npr.org/1128/rss.xml",                          2),
    ("Medical News Today",    "https://www.medicalnewstoday.com/rss/news.xml",               2),
    ("WHO News",              "https://www.who.int/rss-feeds/news-english.xml",              2),
    ("The Guardian Health",   "https://www.theguardian.com/society/health/rss",              2),
    ("WebMD Health News",     "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC", 2),
    ("NDTV Health",           "https://doctor.ndtv.com/rss/health",                          2),
]

# ── Entertainment & Culture ───────────────────────────────────────────────────
ENTERTAINMENT_FEEDS = [
    ("BBC Entertainment",     "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",  2),
    ("Variety",               "https://variety.com/feed/",                                    2),
    ("Hollywood Reporter",    "https://www.hollywoodreporter.com/feed/",                      2),
    ("Rolling Stone",         "https://www.rollingstone.com/feed/",                           2),
    ("The Guardian Culture",  "https://www.theguardian.com/culture/rss",                      2),
    ("NPR Arts",              "https://feeds.npr.org/1008/rss.xml",                          2),
    ("Bollywood Hungama",     "https://www.bollywoodhungama.com/feed/",                       2),
    ("Filmfare",              "https://www.filmfare.com/news/rss/bollywood/all",             2),
]

# ── Gaming ────────────────────────────────────────────────────────────────────
GAMING_FEEDS = [
    ("IGN",                   "https://feeds.ign.com/ign/games-all",                          2),
    ("GameSpot",              "https://www.gamespot.com/feeds/mashup/",                       2),
    ("Kotaku",                "https://kotaku.com/rss",                                       2),
    ("Eurogamer",             "https://www.eurogamer.net/?format=rss",                        2),
    ("PC Gamer",              "https://www.pcgamer.com/rss/",                                 2),
    ("Rock Paper Shotgun",    "https://www.rockpapershotgun.com/feed",                        2),
    ("VG247",                 "https://www.vg247.com/feed",                                   2),
]

# ── Sports (Cricket + General) ────────────────────────────────────────────────
SPORTS_FEEDS = [
    ("BBC Sport Cricket",     "https://feeds.bbci.co.uk/sport/cricket/rss.xml",               2),
    ("BBC Sport",             "https://feeds.bbci.co.uk/sport/rss.xml",                       2),
    ("ESPN Cricinfo",         "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",   2),
    ("Times of India Sports", "https://timesofindia.indiatimes.com/rssfeeds/4719161.cms",     2),
    ("The Hindu Cricket",     "https://www.thehindu.com/sport/cricket/?service=rss",          2),
    ("The Guardian Sport",    "https://www.theguardian.com/sport/rss",                        2),
    ("Cricbuzz",              "https://www.cricbuzz.com/cricket-news/rss-feeds",              2),
    ("ICC Cricket",           "https://www.icc-cricket.com/media-releases/news.xml",          2),
    ("NDTV Sports",           "https://sports.ndtv.com/cricket/rss",                          2),
    ("Sky Sports",            "https://www.skysports.com/rss/12040",                          2),
    ("ESPN Sports",           "https://www.espn.com/espn/rss/news",                           2),
]

# ── Environment & Climate ─────────────────────────────────────────────────────
ENVIRONMENT_FEEDS = [
    ("BBC Environment",       "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", 2),
    ("The Guardian Env",      "https://www.theguardian.com/environment/rss",                  2),
    ("Climate Home News",     "https://www.climatechangenews.com/feed/",                      2),
    ("Carbon Brief",          "https://www.carbonbrief.org/feed",                             2),
    ("Reuters Environment",   "https://feeds.reuters.com/reuters/environment",                2),
    ("NPR Environment",       "https://feeds.npr.org/1025/rss.xml",                          2),
]

# ── Fact-checking — debunked / false claims (label = 0) ──────────────────────
FACTCHECK_FALSE_FEEDS = [
    ("Snopes",                "https://www.snopes.com/fact-check/feed/",                      0),
    ("FactCheck.org",         "https://www.factcheck.org/feed/",                              0),
    ("FullFact",              "https://fullfact.org/feed/",                                   0),
    ("Africa Check",          "https://africacheck.org/feed/",                                0),
    ("Vishvas News",          "https://www.vishvasnews.com/feed/",                            0),
    ("Boom Live",             "https://www.boomlive.in/feed",                                 0),
    ("EUvsDisinfo",           "https://euvsdisinfo.eu/feed/",                                 0),
    ("CheckYourFact",         "https://checkyourfact.com/feed/",                              0),
    ("Alt News",              "https://www.altnews.in/feed/",                                 0),
    ("Quint WebQoof",         "https://www.thequint.com/section/webqoof/rss",                 0),
]

# ── Fact-checking — half-true / misleading (label = 1) ───────────────────────
FACTCHECK_PARTIAL_FEEDS = [
    ("The Dispatch",          "https://thedispatch.com/feed/",                                1),
    ("Poynter",               "https://www.poynter.org/feed/",                                1),
    ("PolitiFact",            "https://www.politifact.com/rss/all/",                          1),
    ("Reuters Fact Check",    "https://feeds.reuters.com/reuters/CNESfactcheck",              1),
    ("AP Fact Check",         "https://apnews.com/hub/ap-fact-check/feed",                   1),
    ("Washington Post FC",    "https://www.washingtonpost.com/news/fact-checker/feed/",       1),
    ("USA Today FC",          "https://www.usatoday.com/rss/topic/fact-check/",              1),
]

# Combined list used when all feeds are fetched together
ALL_LEGIT_FEEDS = (
    WORLD_NEWS_FEEDS + POLITICS_FEEDS + TECH_FEEDS + BUSINESS_FEEDS +
    SCIENCE_FEEDS + HEALTH_FEEDS + ENTERTAINMENT_FEEDS + GAMING_FEEDS +
    SPORTS_FEEDS + ENVIRONMENT_FEEDS
)
ALL_RSS_FEEDS = ALL_LEGIT_FEEDS + FACTCHECK_FALSE_FEEDS + FACTCHECK_PARTIAL_FEEDS

# ─────────────────────────────────────────────────────────────────────────────
# GDELT QUERY BANKS
# ─────────────────────────────────────────────────────────────────────────────

# Current news — all categories (label 2)
GDELT_CURRENT_QUERIES = [
    ("world politics government election", 2),
    ("technology AI cybersecurity innovation", 2),
    ("economy business markets finance", 2),
    ("science research discovery space NASA", 2),
    ("health medicine disease vaccine pandemic", 2),
    ("sports cricket IPL T20 football Olympics", 2),
    ("entertainment movies music celebrity Bollywood", 2),
    ("gaming video games esports", 2),
    ("environment climate energy disaster", 2),
    ("India news latest", 2),
    ("war conflict diplomacy international", 2),
    ("education law crime justice", 2),
]

# Misinformation queries — for model training labels 0/1
GDELT_MISINFO_QUERIES = [
    ("false claim debunked fact check", 0),
    ("misinformation disinformation viral fake news", 0),
    ("conspiracy theory false allegation hoax", 0),
    ("misleading claim half truth exaggerated", 1),
    ("satire parody misrepresented out of context", 1),
    ("fake video deepfake manipulated image", 0),
    ("health misinformation vaccine false cure", 0),
    ("election fraud political disinformation", 0),
    ("sports match fixing rumor false score", 0),
]

# Historical all-category GDELT queries (used with --history-full)
GDELT_HISTORICAL_CATEGORY_QUERIES = [
    # Politics & World
    ("government policy election politics", 2),
    ("international relations war diplomacy", 2),
    ("COVID coronavirus pandemic lockdown", 2),
    # Technology
    ("artificial intelligence machine learning tech", 2),
    ("social media platform privacy data breach", 2),
    ("smartphone 5G semiconductor chip", 2),
    # Business
    ("stock market economy inflation recession", 2),
    ("startup funding IPO merger acquisition", 2),
    ("cryptocurrency bitcoin blockchain", 2),
    # Science & Health
    ("medical research drug trial vaccine", 2),
    ("climate change global warming emissions", 2),
    ("space mission satellite moon Mars", 2),
    # Sports
    ("cricket IPL T20 World Cup test match", 2),
    ("football soccer UEFA Champions League FIFA World Cup", 2),
    ("Olympics athletics tennis Grand Slam", 2),
    # Entertainment & Gaming
    ("movies box office Hollywood Bollywood awards", 2),
    ("music album concert streaming artist", 2),
    ("video games console gaming industry esports", 2),
    # India-specific
    ("India Modi parliament budget policy", 2),
    ("India economy GDP manufacturing agriculture", 2),
    ("India tech startup Bengaluru Mumbai", 2),
    # Misinformation (historical)
    ("false claim debunked fact check", 0),
    ("misinformation disinformation viral fake", 0),
    ("conspiracy theory hoax propaganda", 0),
    ("misleading half truth exaggerated", 1),
]

# Full date range: 2020 → 2025  (6 years)
GDELT_YEAR_RANGES_FULL = [
    ("20200101000000", "20201231235959"),
    ("20210101000000", "20211231235959"),
    ("20220101000000", "20221231235959"),
    ("20230101000000", "20231231235959"),
    ("20240101000000", "20241231235959"),
    ("20250101000000", "20251231235959"),
]

# Shorter range (2022-2025) for the default --history flag
GDELT_YEAR_RANGES_DEFAULT = GDELT_YEAR_RANGES_FULL[2:]  # 2022–2025

# ─────────────────────────────────────────────────────────────────────────────
# Google Fact Check keyword mappings
# ─────────────────────────────────────────────────────────────────────────────
GOOGLE_FC_FALSE_KEYWORDS = [
    "false", "pants on fire", "mostly false", "fabricated", "wrong",
    "inaccurate", "incorrect", "untrue", "debunked", "fake", "no evidence",
    "misleading", "exaggerated",
]
GOOGLE_FC_PARTIAL_KEYWORDS = [
    "half true", "half-true", "partially true", "mixed", "unverified",
    "needs context", "distorted", "missing context", "out of context",
    "unproven", "disputed", "misleading but",
]

# ─────────────────────────────────────────────────────────────────────────────
# FETCHERS
# ─────────────────────────────────────────────────────────────────────────────

def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def _parse_feed_with_retry(url: str, retries: int = 2):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            feed = feedparser.parse(url)
            if feed.bozo and hasattr(feed, "bozo_exception"):
                exc_type = type(feed.bozo_exception).__name__
                if any(t in exc_type for t in ("Connection", "Timeout", "URLError", "gaierror", "socket")):
                    raise feed.bozo_exception
            return feed
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise last_exc or Exception("feed parse failed")


def fetch_rss(feeds=None, max_per_feed=50, retries=2):
    if not HAS_FEEDPARSER:
        return []
    if feeds is None:
        feeds = ALL_RSS_FEEDS

    articles = []
    for name, url, label in feeds:
        try:
            feed = _parse_feed_with_retry(url, retries=retries)
            count = 0
            for entry in feed.entries:
                title   = _clean_html(entry.get("title")   or "")
                summary = _clean_html(entry.get("summary") or entry.get("description") or "")
                text = f"{title} {summary}".strip()
                if len(text) > 40:
                    articles.append({"title": title, "text": text, "source": name, "label": label})
                    count += 1
                    if count >= max_per_feed:
                        break
            verdict = {0: "Highly Deceptive", 1: "Misleading", 2: "Legitimate"}[label]
            print(f"  {name}: {count} articles [{verdict}]")
        except Exception as exc:
            print(f"  {name}: FAILED - {exc}")
    return articles


def fetch_gdelt(query="latest news world", max_records=250,
                startdatetime=None, enddatetime=None, default_label=2,
                retries=2, timeout=15):
    """
    GDELT Document API — completely free, no API key required.
    Returns article titles (full text not available without scraping).
    startdatetime / enddatetime format: 'YYYYMMDDHHMMSS'
    """
    params = (
        f"?query={requests.utils.quote(query)}"
        f"&mode=artlist&maxrecords={max_records}&format=json"
    )
    if startdatetime:
        params += f"&startdatetime={startdatetime}"
    if enddatetime:
        params += f"&enddatetime={enddatetime}"

    url        = f"https://api.gdeltproject.org/api/v2/doc/doc{params}"
    label_name = {0: "Highly Deceptive", 1: "Misleading", 2: "Legitimate"}[default_label]
    date_tag   = f" ({startdatetime[:4]})" if startdatetime else ""

    for attempt in range(retries + 1):
        try:
            time.sleep(2)  # respect GDELT rate limit
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 429:
                wait = 20 * (attempt + 1)
                print(f"  GDELT rate-limited - waiting {wait}s ...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            arts = []
            for art in data.get("articles", []):
                title = (art.get("title") or "").strip()
                if len(title) > 20:
                    arts.append({
                        "title": title, "text": title,
                        "source": art.get("domain", "gdelt"),
                        "label": default_label,
                    })
            print(f"  GDELT ({query[:45]!r}){date_tag}: {len(arts)} articles [{label_name}]")
            return arts
        except requests.exceptions.ConnectionError:
            print(f"  GDELT ({query[:45]!r}){date_tag}: SKIPPED (no network)")
            return []
        except Exception as exc:
            if attempt < retries:
                print(f"  GDELT ({query[:45]!r}): attempt {attempt+1} failed - retrying...")
            else:
                print(f"  GDELT ({query[:45]!r}): FAILED - {exc}")
    return []


def fetch_google_fact_check(api_key, max_per_query=50):
    """
    Google Fact Check Tools API — free with key.
    Covers claims across sports, politics, health, etc. from 100+ publishers since 2022.
    Get key: https://developers.google.com/fact-check/tools/api
    """
    base_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    queries = [
        # Politics & elections
        "election fraud", "political misinformation", "government false claim",
        # Health
        "vaccine misinformation", "covid false claim", "health fake cure",
        # Climate
        "climate change denial", "environment false claim",
        # Sports
        "cricket match fixing false", "sports fake news",
        # Tech
        "AI deepfake false", "tech company false claim",
        # India
        "India false claim viral", "Modi government misinformation",
        # General
        "false news viral", "war propaganda fake",
    ]

    articles = []
    for query in queries:
        params = {"query": query, "languageCode": "en", "pageSize": max_per_query, "key": api_key}
        try:
            resp = requests.get(base_url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            count = 0
            for claim in data.get("claims", []):
                claim_text = (claim.get("text") or "").strip()
                if len(claim_text) < 20:
                    continue
                rating_text = ""
                for review in claim.get("claimReview", []):
                    rating_text = (review.get("textualRating") or "").lower()
                    break
                if any(kw in rating_text for kw in GOOGLE_FC_FALSE_KEYWORDS):
                    label = 0
                elif any(kw in rating_text for kw in GOOGLE_FC_PARTIAL_KEYWORDS):
                    label = 1
                else:
                    continue
                articles.append({"title": claim_text[:200], "text": claim_text,
                                  "source": "Google Fact Check", "label": label})
                count += 1
            print(f"  Google FC ({query!r}): {count} claims")
        except Exception as exc:
            print(f"  Google FC ({query!r}): FAILED - {exc}")
    return articles


def fetch_newsapi(api_key, max_per_category=50):
    """
    NewsAPI — fetches top headlines across ALL 7 supported categories.
    Free tier: 100 requests/day. Get key: https://newsapi.org/register
    Categories: business, entertainment, general, health, science, sports, technology
    """
    categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    articles = []
    for category in categories:
        url = (
            f"https://newsapi.org/v2/top-headlines"
            f"?language=en&category={category}&pageSize={min(max_per_category, 100)}&apiKey={api_key}"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            count = 0
            for art in data.get("articles", []):
                title   = (art.get("title")       or "").strip()
                desc    = (art.get("description") or "").strip()
                content = (art.get("content")     or "").strip()
                text = f"{title} {desc} {content}".strip()
                if len(text) > 40:
                    articles.append({
                        "title": title, "text": text,
                        "source": f"NewsAPI-{category}",
                        "label": 2,
                    })
                    count += 1
            print(f"  NewsAPI [{category}]: {count} articles [Legitimate]")
        except Exception as exc:
            print(f"  NewsAPI [{category}]: FAILED - {exc}")
    return articles


def balance_articles(articles, strategy="oversample"):
    """
    Balance the article list so each label (0, 1, 2) has equal representation.
    strategy: 'oversample' | 'undersample' | 'median'
    """
    df = pd.DataFrame(articles)
    if df.empty:
        return articles

    counts = {lbl: (df["label"] == lbl).sum() for lbl in [0, 1, 2]}
    print(f"\n  Before balancing: {counts}")

    if strategy == "oversample":
        target = max(counts.values())
    elif strategy == "undersample":
        target = min(c for c in counts.values() if c > 0)
    else:  # median
        non_zero = [c for c in counts.values() if c > 0]
        target = int(sorted(non_zero)[len(non_zero) // 2])

    parts = []
    for lbl in [0, 1, 2]:
        grp = df[df["label"] == lbl]
        if len(grp) == 0:
            continue
        if len(grp) < target:
            extra = grp.sample(target - len(grp), replace=True, random_state=42)
            grp = pd.concat([grp, extra], ignore_index=True)
        elif len(grp) > target:
            grp = grp.sample(target, random_state=42)
        parts.append(grp)

    balanced = pd.concat(parts, ignore_index=True).sample(frac=1, random_state=42)
    new_counts = {lbl: (balanced["label"] == lbl).sum() for lbl in [0, 1, 2]}
    print(f"  After balancing:  {new_counts}")
    return balanced.to_dict("records")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch live news (all categories) for model fine-tuning")

    # API keys
    parser.add_argument("--newsapi-key",   default=os.getenv("NEWS_API_KEY"),  help="NewsAPI key (optional)")
    parser.add_argument("--google-fc-key", default=os.getenv("GOOGLE_FC_KEY"), help="Google Fact Check API key (optional)")

    # RSS category toggles (all on by default)
    parser.add_argument("--no-world",         dest="world",         action="store_false", default=True)
    parser.add_argument("--no-politics",      dest="politics",      action="store_false", default=True)
    parser.add_argument("--no-tech",          dest="tech",          action="store_false", default=True)
    parser.add_argument("--no-business",      dest="business",      action="store_false", default=True)
    parser.add_argument("--no-science",       dest="science",       action="store_false", default=True)
    parser.add_argument("--no-health",        dest="health",        action="store_false", default=True)
    parser.add_argument("--no-entertainment", dest="entertainment", action="store_false", default=True)
    parser.add_argument("--no-gaming",        dest="gaming",        action="store_false", default=True)
    parser.add_argument("--no-sports",        dest="sports",        action="store_false", default=True)
    parser.add_argument("--no-environment",   dest="environment",   action="store_false", default=True)

    # GDELT options
    parser.add_argument("--gdelt-records",   type=int, default=100,
                        help="Max GDELT records per query (default 100)")
    parser.add_argument("--history",         action="store_true",
                        help="Fetch GDELT misinfo history 2022-2025 (fast, ~5 min)")
    parser.add_argument("--history-full",    action="store_true",
                        help="Fetch GDELT ALL categories 2020-2025 (comprehensive, ~30 min)")

    # Per-feed limit
    parser.add_argument("--max-per-feed",    type=int, default=50,
                        help="Max articles per RSS feed (default 50)")

    # Balancing
    parser.add_argument("--balance",         dest="balance", action="store_true",  default=True)
    parser.add_argument("--no-balance",      dest="balance", action="store_false",
                        help="Disable class balancing")
    parser.add_argument("--balance-strategy", default="median",
                        choices=["oversample", "undersample", "median"])

    parser.add_argument("--out", default=None, help="Output CSV path (default: src/live_news.csv)")

    args = parser.parse_args()
    output_path = args.out or os.path.join(os.path.dirname(__file__), "live_news.csv")

    all_articles = []

    # ── RSS feeds by category ─────────────────────────────────────────────────
    category_feeds = []
    if args.world:
        category_feeds.extend(WORLD_NEWS_FEEDS)
    if args.politics:
        category_feeds.extend(POLITICS_FEEDS)
    if args.tech:
        category_feeds.extend(TECH_FEEDS)
    if args.business:
        category_feeds.extend(BUSINESS_FEEDS)
    if args.science:
        category_feeds.extend(SCIENCE_FEEDS)
    if args.health:
        category_feeds.extend(HEALTH_FEEDS)
    if args.entertainment:
        category_feeds.extend(ENTERTAINMENT_FEEDS)
    if args.gaming:
        category_feeds.extend(GAMING_FEEDS)
    if args.sports:
        category_feeds.extend(SPORTS_FEEDS)
    if args.environment:
        category_feeds.extend(ENVIRONMENT_FEEDS)

    if category_feeds:
        print(f"\n[Legitimate News RSS - {len(category_feeds)} feeds across all categories]")
        all_articles.extend(fetch_rss(feeds=category_feeds, max_per_feed=args.max_per_feed))

    print("\n[Fact-Checking Feeds - Highly Deceptive (label 0)]")
    all_articles.extend(fetch_rss(feeds=FACTCHECK_FALSE_FEEDS, max_per_feed=args.max_per_feed))

    print("\n[Fact-Checking Feeds - Misleading (label 1)]")
    all_articles.extend(fetch_rss(feeds=FACTCHECK_PARTIAL_FEEDS, max_per_feed=args.max_per_feed))

    # ── GDELT current news (all categories) ───────────────────────────────────
    print("\n[GDELT - Current News (all categories)]")
    for query, lbl in GDELT_CURRENT_QUERIES:
        all_articles.extend(fetch_gdelt(query=query, max_records=args.gdelt_records, default_label=lbl))

    # ── GDELT historical misinfo 2022-2025 (default --history) ───────────────
    if args.history or args.history_full:
        print("\n[GDELT - Historical Misinformation 2022-2025]")
        for query, lbl in GDELT_MISINFO_QUERIES:
            for start, end in GDELT_YEAR_RANGES_DEFAULT:
                all_articles.extend(fetch_gdelt(
                    query=query, max_records=30,
                    startdatetime=start, enddatetime=end, default_label=lbl,
                ))

    # ── GDELT full history 2020-2025 ALL categories (--history-full) ─────────
    if args.history_full:
        print("\n[GDELT - Full History 2020-2025 (all categories) - this may take ~30 min]")
        for query, lbl in GDELT_HISTORICAL_CATEGORY_QUERIES:
            for start, end in GDELT_YEAR_RANGES_FULL:
                all_articles.extend(fetch_gdelt(
                    query=query, max_records=50,
                    startdatetime=start, enddatetime=end, default_label=lbl,
                ))

    # ── Optional: Google Fact Check Tools API ─────────────────────────────────
    if args.google_fc_key:
        print("\n[Google Fact Check Tools API]")
        all_articles.extend(fetch_google_fact_check(args.google_fc_key))
    else:
        print("\n[Google Fact Check] Skipped - set GOOGLE_FC_KEY env var to enable.")

    # ── Optional: NewsAPI (all 7 categories) ─────────────────────────────────
    if args.newsapi_key:
        print("\n[NewsAPI - all 7 categories]")
        all_articles.extend(fetch_newsapi(args.newsapi_key))
    else:
        print("\n[NewsAPI] Skipped - set NEWS_API_KEY env var to enable.")

    # ── Deduplicate & filter ──────────────────────────────────────────────────
    df = pd.DataFrame(all_articles).drop_duplicates(subset=["text"])
    df = df[df["text"].str.len() > 40].reset_index(drop=True)

    print(f"\nRaw totals before balancing: {len(df)} unique articles")
    print("Label breakdown:")
    for lbl, name in [(0, "Highly Deceptive"), (1, "Misleading"), (2, "Legitimate")]:
        count = (df["label"] == lbl).sum()
        print(f"  {lbl} ({name}): {count}")

    # ── Balance classes ───────────────────────────────────────────────────────
    if args.balance:
        print(f"\n[Balance] Normalizing with strategy='{args.balance_strategy}' ...")
        balanced = balance_articles(df.to_dict("records"), strategy=args.balance_strategy)
        df = pd.DataFrame(balanced).drop_duplicates(subset=["text"]).reset_index(drop=True)

    print(f"\nTotal: {len(df)} articles saved to {output_path}")
    print("Final label breakdown:")
    for lbl, name in [(0, "Highly Deceptive"), (1, "Misleading"), (2, "Legitimate")]:
        count = (df["label"] == lbl).sum()
        print(f"  {lbl} ({name}): {count}")

    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    main()
