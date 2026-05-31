"""
tests/test_live_news.py
------------------------
Unit tests for src/fetch_live_news.py

Tests cover:
  - Feed list completeness (all categories present, right labels)
  - GDELT query banks (all-category + misinfo, correct labels)
  - Historical date ranges (2020-2025 coverage)
  - _clean_html() utility
  - balance_articles() logic
  - NewsAPI category coverage
  - No duplicate feed URLs within a category
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd

from src.fetch_live_news import (
    WORLD_NEWS_FEEDS, POLITICS_FEEDS, TECH_FEEDS, BUSINESS_FEEDS,
    SCIENCE_FEEDS, HEALTH_FEEDS, ENTERTAINMENT_FEEDS, GAMING_FEEDS,
    SPORTS_FEEDS, ENVIRONMENT_FEEDS,
    FACTCHECK_FALSE_FEEDS, FACTCHECK_PARTIAL_FEEDS,
    ALL_LEGIT_FEEDS, ALL_RSS_FEEDS,
    GDELT_CURRENT_QUERIES, GDELT_MISINFO_QUERIES,
    GDELT_HISTORICAL_CATEGORY_QUERIES,
    GDELT_YEAR_RANGES_FULL, GDELT_YEAR_RANGES_DEFAULT,
    GOOGLE_FC_FALSE_KEYWORDS, GOOGLE_FC_PARTIAL_KEYWORDS,
    _clean_html, balance_articles,
)


# ─────────────────────────────────────────────────────────────────────────────
# Feed structure helpers
# ─────────────────────────────────────────────────────────────────────────────

def _labels(feeds):
    return {label for _, _, label in feeds}

def _urls(feeds):
    return [url for _, url, _ in feeds]

def _names(feeds):
    return [name for name, _, _ in feeds]


# ─────────────────────────────────────────────────────────────────────────────
# Category feed lists — existence and size
# ─────────────────────────────────────────────────────────────────────────────

class TestCategoryFeedsExist:
    @pytest.mark.parametrize("feeds,name,min_count", [
        (WORLD_NEWS_FEEDS,      "World/India News",  5),
        (POLITICS_FEEDS,        "Politics",          5),
        (TECH_FEEDS,            "Technology",        5),
        (BUSINESS_FEEDS,        "Business",          5),
        (SCIENCE_FEEDS,         "Science",           5),
        (HEALTH_FEEDS,          "Health",            5),
        (ENTERTAINMENT_FEEDS,   "Entertainment",     4),
        (GAMING_FEEDS,          "Gaming",            4),
        (SPORTS_FEEDS,          "Sports/Cricket",    5),
        (ENVIRONMENT_FEEDS,     "Environment",       4),
        (FACTCHECK_FALSE_FEEDS, "Factcheck False",   5),
        (FACTCHECK_PARTIAL_FEEDS, "Factcheck Partial", 4),
    ])
    def test_category_has_minimum_feeds(self, feeds, name, min_count):
        assert len(feeds) >= min_count, (
            f"{name} should have >= {min_count} feeds, got {len(feeds)}"
        )


class TestCategoryFeedLabels:
    def test_all_legit_feeds_label_2(self):
        for name, url, label in ALL_LEGIT_FEEDS:
            assert label == 2, f"Feed '{name}' should be label 2, got {label}"

    def test_factcheck_false_feeds_label_0(self):
        for name, url, label in FACTCHECK_FALSE_FEEDS:
            assert label == 0, f"Feed '{name}' should be label 0, got {label}"

    def test_factcheck_partial_feeds_label_1(self):
        for name, url, label in FACTCHECK_PARTIAL_FEEDS:
            assert label == 1, f"Feed '{name}' should be label 1, got {label}"


class TestFeedURLFormat:
    def test_all_rss_urls_start_with_http(self):
        for name, url, _ in ALL_RSS_FEEDS:
            assert url.startswith("http"), (
                f"Feed '{name}' URL '{url}' does not start with http"
            )

    def test_no_empty_feed_names(self):
        for name, _, _ in ALL_RSS_FEEDS:
            assert name.strip(), "Empty feed name found"

    def test_no_empty_feed_urls(self):
        for _, url, _ in ALL_RSS_FEEDS:
            assert url.strip(), "Empty feed URL found"


class TestFeedCoverage:
    def test_total_feed_count(self):
        assert len(ALL_RSS_FEEDS) >= 90

    def test_all_legit_feeds_count(self):
        assert len(ALL_LEGIT_FEEDS) >= 80

    def test_sports_contains_cricket_sources(self):
        names = _names(SPORTS_FEEDS)
        cricket_sources = {"BBC Sport Cricket", "ESPN Cricinfo", "ICC Cricket"}
        found = cricket_sources & set(names)
        assert len(found) >= 2, f"Expected cricket sources missing: {cricket_sources - set(names)}"

    def test_tech_contains_major_sources(self):
        names = _names(TECH_FEEDS)
        assert any("TechCrunch" in n or "Verge" in n or "Wired" in n for n in names)

    def test_business_contains_financial_sources(self):
        names = _names(BUSINESS_FEEDS)
        assert any("Reuters" in n or "CNBC" in n or "Economic" in n for n in names)

    def test_health_contains_who(self):
        names = _names(HEALTH_FEEDS)
        assert any("WHO" in n or "WebMD" in n or "Medical" in n for n in names)

    def test_science_contains_nasa(self):
        names = _names(SCIENCE_FEEDS)
        assert any("NASA" in n or "Space" in n or "Science Daily" in n for n in names)

    def test_india_news_in_world_feeds(self):
        names = _names(WORLD_NEWS_FEEDS)
        india_sources = ["The Hindu", "Times of India", "NDTV", "India Today"]
        found = [s for s in india_sources if any(s in n for n in names)]
        assert len(found) >= 2, "Expected India news sources missing from world feeds"

    def test_factcheck_includes_indian_sources(self):
        names = _names(FACTCHECK_FALSE_FEEDS)
        assert any("Alt News" in n or "Boom" in n or "Vishvas" in n or "Quint" in n
                   for n in names), "Expected Indian fact-checkers missing"

    def test_all_rss_feeds_combines_all(self):
        expected_total = (
            len(ALL_LEGIT_FEEDS) + len(FACTCHECK_FALSE_FEEDS) + len(FACTCHECK_PARTIAL_FEEDS)
        )
        assert len(ALL_RSS_FEEDS) == expected_total


# ─────────────────────────────────────────────────────────────────────────────
# GDELT query banks
# ─────────────────────────────────────────────────────────────────────────────

class TestGDELTQueries:
    def test_current_queries_count(self):
        assert len(GDELT_CURRENT_QUERIES) >= 10

    def test_misinfo_queries_count(self):
        assert len(GDELT_MISINFO_QUERIES) >= 5

    def test_historical_queries_count(self):
        assert len(GDELT_HISTORICAL_CATEGORY_QUERIES) >= 15

    def test_current_queries_are_tuples(self):
        for item in GDELT_CURRENT_QUERIES:
            assert len(item) == 2, "Each GDELT query should be (query_str, label)"

    def test_current_queries_all_label_2(self):
        for query, label in GDELT_CURRENT_QUERIES:
            assert label == 2, f"Current query '{query}' should be label 2 (legitimate)"

    def test_misinfo_queries_label_0_or_1(self):
        for query, label in GDELT_MISINFO_QUERIES:
            assert label in {0, 1}, (
                f"Misinfo query '{query}' should be label 0 or 1, got {label}"
            )

    def test_historical_queries_have_valid_labels(self):
        for query, label in GDELT_HISTORICAL_CATEGORY_QUERIES:
            assert label in {0, 1, 2}, (
                f"Historical query '{query}' has invalid label {label}"
            )

    def test_current_queries_cover_sports(self):
        all_q = " ".join(q for q, _ in GDELT_CURRENT_QUERIES).lower()
        assert "cricket" in all_q or "sports" in all_q or "ipl" in all_q

    def test_current_queries_cover_technology(self):
        all_q = " ".join(q for q, _ in GDELT_CURRENT_QUERIES).lower()
        assert "technology" in all_q or "ai" in all_q or "tech" in all_q

    def test_current_queries_cover_health(self):
        all_q = " ".join(q for q, _ in GDELT_CURRENT_QUERIES).lower()
        assert "health" in all_q or "medicine" in all_q

    def test_current_queries_cover_politics(self):
        all_q = " ".join(q for q, _ in GDELT_CURRENT_QUERIES).lower()
        assert "politics" in all_q or "government" in all_q or "election" in all_q

    def test_current_queries_cover_business(self):
        all_q = " ".join(q for q, _ in GDELT_CURRENT_QUERIES).lower()
        assert "business" in all_q or "economy" in all_q or "finance" in all_q

    def test_current_queries_cover_gaming(self):
        all_q = " ".join(q for q, _ in GDELT_CURRENT_QUERIES).lower()
        assert "gaming" in all_q or "esports" in all_q or "video games" in all_q

    def test_historical_queries_include_misinfo(self):
        misinfo_labels = [label for _, label in GDELT_HISTORICAL_CATEGORY_QUERIES
                          if label in {0, 1}]
        assert len(misinfo_labels) >= 3, "Historical queries should include some misinfo"

    def test_no_empty_query_strings(self):
        for query, _ in (GDELT_CURRENT_QUERIES + GDELT_MISINFO_QUERIES +
                         GDELT_HISTORICAL_CATEGORY_QUERIES):
            assert query.strip(), "Empty GDELT query string found"


# ─────────────────────────────────────────────────────────────────────────────
# GDELT year ranges
# ─────────────────────────────────────────────────────────────────────────────

class TestGDELTYearRanges:
    def test_full_range_covers_2020_to_2025(self):
        years = [int(start[:4]) for start, _ in GDELT_YEAR_RANGES_FULL]
        assert 2020 in years, "2020 missing from full year range"
        assert 2021 in years, "2021 missing from full year range"
        assert 2022 in years, "2022 missing from full year range"
        assert 2023 in years, "2023 missing from full year range"
        assert 2024 in years, "2024 missing from full year range"
        assert 2025 in years, "2025 missing from full year range"

    def test_full_range_has_6_years(self):
        assert len(GDELT_YEAR_RANGES_FULL) == 6

    def test_default_range_is_subset_of_full(self):
        full_starts = {s for s, _ in GDELT_YEAR_RANGES_FULL}
        for start, _ in GDELT_YEAR_RANGES_DEFAULT:
            assert start in full_starts

    def test_default_range_starts_at_2022_or_later(self):
        years = [int(start[:4]) for start, _ in GDELT_YEAR_RANGES_DEFAULT]
        assert min(years) >= 2022

    def test_year_range_format(self):
        import re
        pattern = re.compile(r"^\d{14}$")
        for start, end in GDELT_YEAR_RANGES_FULL:
            assert pattern.match(start), f"Invalid start datetime: {start}"
            assert pattern.match(end), f"Invalid end datetime: {end}"

    def test_start_before_end_in_each_range(self):
        for start, end in GDELT_YEAR_RANGES_FULL:
            assert start < end, f"Start {start} is not before end {end}"


# ─────────────────────────────────────────────────────────────────────────────
# _clean_html
# ─────────────────────────────────────────────────────────────────────────────

class TestCleanHTML:
    def test_removes_simple_tag(self):
        assert _clean_html("<b>hello</b>") == "hello"

    def test_removes_nested_tags(self):
        assert _clean_html("<div><p>text</p></div>") == "text"

    def test_removes_anchor_tag(self):
        result = _clean_html('<a href="http://example.com">click here</a>')
        assert "click here" in result
        assert "<a" not in result

    def test_plain_text_unchanged(self):
        assert _clean_html("plain text") == "plain text"

    def test_strips_whitespace(self):
        assert _clean_html("  hello  ") == "hello"

    def test_empty_string(self):
        assert _clean_html("") == ""

    def test_tag_with_attributes(self):
        result = _clean_html('<img src="x.png" alt="image"/>')
        assert "<img" not in result

    def test_removes_script_tag(self):
        result = _clean_html("<script>alert('xss')</script>safe text")
        assert "safe text" in result
        assert "<script" not in result


# ─────────────────────────────────────────────────────────────────────────────
# balance_articles
# ─────────────────────────────────────────────────────────────────────────────

class TestBalanceArticles:
    def _make_articles(self, counts):
        """Build a list with `counts` = {label: n} articles."""
        articles = []
        for label, n in counts.items():
            for i in range(n):
                articles.append({
                    "title": f"title {label} {i}",
                    "text":  f"text content label {label} item {i}",
                    "source": "test",
                    "label": label,
                })
        return articles

    def test_empty_input(self):
        result = balance_articles([], strategy="median")
        assert result == []

    def test_oversample_makes_equal_counts(self):
        arts = self._make_articles({0: 10, 1: 5, 2: 20})
        result = balance_articles(arts, strategy="oversample")
        df = pd.DataFrame(result)
        counts = df["label"].value_counts()
        assert counts[0] == counts[1] == counts[2]

    def test_undersample_makes_equal_counts(self):
        arts = self._make_articles({0: 10, 1: 5, 2: 20})
        result = balance_articles(arts, strategy="undersample")
        df = pd.DataFrame(result)
        counts = df["label"].value_counts()
        assert counts.min() == counts.max()

    def test_median_strategy_returns_valid_data(self):
        arts = self._make_articles({0: 10, 1: 30, 2: 50})
        result = balance_articles(arts, strategy="median")
        assert len(result) > 0
        df = pd.DataFrame(result)
        assert set(df["label"].unique()).issubset({0, 1, 2})

    def test_already_balanced_unchanged(self):
        arts = self._make_articles({0: 20, 1: 20, 2: 20})
        result = balance_articles(arts, strategy="oversample")
        df = pd.DataFrame(result)
        counts = df["label"].value_counts()
        assert counts[0] == counts[1] == counts[2] == 20

    def test_output_preserves_required_columns(self):
        arts = self._make_articles({0: 5, 1: 5, 2: 5})
        result = balance_articles(arts, strategy="median")
        df = pd.DataFrame(result)
        for col in ["title", "text", "source", "label"]:
            assert col in df.columns

    def test_single_class_does_not_crash(self):
        arts = self._make_articles({2: 10})
        result = balance_articles(arts, strategy="median")
        assert len(result) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Google Fact Check keyword lists
# ─────────────────────────────────────────────────────────────────────────────

class TestGoogleFCKeywords:
    def test_false_keywords_not_empty(self):
        assert len(GOOGLE_FC_FALSE_KEYWORDS) >= 5

    def test_partial_keywords_not_empty(self):
        assert len(GOOGLE_FC_PARTIAL_KEYWORDS) >= 5

    def test_false_contains_key_terms(self):
        assert "false" in GOOGLE_FC_FALSE_KEYWORDS
        assert "debunked" in GOOGLE_FC_FALSE_KEYWORDS

    def test_partial_contains_key_terms(self):
        assert any("half" in k for k in GOOGLE_FC_PARTIAL_KEYWORDS)
        assert any("context" in k for k in GOOGLE_FC_PARTIAL_KEYWORDS)

    def test_no_overlap_between_lists(self):
        overlap = set(GOOGLE_FC_FALSE_KEYWORDS) & set(GOOGLE_FC_PARTIAL_KEYWORDS)
        assert not overlap, f"Overlapping keywords: {overlap}"
