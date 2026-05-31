"""
tests/test_sports_data.py
--------------------------
Unit tests for src/sports_data.py

Tests cover:
  - MATCH_DATABASE integrity (required fields, valid data)
  - IPL_TITLE_HISTORY and T20_WC_WINNERS dicts
  - normalise_team() alias resolution
  - search_matches() filtering logic
  - format_match_as_text() output quality
  - get_all_match_texts() and get_summary_texts()
  - Known correct match results (fact-checking ground truth)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.sports_data import (
    MATCH_DATABASE, IPL_TITLE_HISTORY, T20_WC_WINNERS, TEAM_ALIASES,
    normalise_team, search_matches, format_match_as_text,
    get_all_match_texts, get_summary_texts,
)


# ─────────────────────────────────────────────────────────────────────────────
# Database integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestMatchDatabaseIntegrity:
    REQUIRED_FIELDS = {"id", "tournament", "season", "stage", "date",
                       "team1", "team2", "winner", "loser", "result"}

    def test_database_not_empty(self):
        assert len(MATCH_DATABASE) >= 40

    def test_all_required_fields_present(self):
        for m in MATCH_DATABASE:
            missing = self.REQUIRED_FIELDS - m.keys()
            assert not missing, f"Match {m.get('id')} missing fields: {missing}"

    def test_winner_is_team1_or_team2(self):
        for m in MATCH_DATABASE:
            assert m["winner"] in {m["team1"], m["team2"]}, (
                f"Match {m['id']}: winner '{m['winner']}' not in teams "
                f"({m['team1']}, {m['team2']})"
            )

    def test_loser_is_team1_or_team2(self):
        for m in MATCH_DATABASE:
            assert m["loser"] in {m["team1"], m["team2"]}, (
                f"Match {m['id']}: loser '{m['loser']}' not in teams"
            )

    def test_winner_and_loser_differ(self):
        for m in MATCH_DATABASE:
            assert m["winner"] != m["loser"], (
                f"Match {m['id']}: winner and loser are both '{m['winner']}'"
            )

    def test_ids_are_unique(self):
        ids = [m["id"] for m in MATCH_DATABASE]
        assert len(ids) == len(set(ids)), "Duplicate match IDs found"

    def test_seasons_are_integers(self):
        for m in MATCH_DATABASE:
            assert isinstance(m["season"], int), f"Match {m['id']} season is not int"

    def test_dates_are_formatted(self):
        import re
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for m in MATCH_DATABASE:
            if m.get("date"):
                assert pattern.match(m["date"]), (
                    f"Match {m['id']} date '{m['date']}' not in YYYY-MM-DD format"
                )

    def test_results_contain_won(self):
        for m in MATCH_DATABASE:
            assert "won" in m["result"].lower() or "beat" in m["result"].lower(), (
                f"Match {m['id']} result '{m['result']}' doesn't mention 'won'"
            )

    def test_seasons_in_expected_range(self):
        for m in MATCH_DATABASE:
            assert 2020 <= m["season"] <= 2026, (
                f"Match {m['id']} season {m['season']} out of expected range"
            )

    def test_covers_required_tournaments(self):
        tournaments = {m["tournament"] for m in MATCH_DATABASE}
        required = [
            "ICC T20 World Cup 2021",
            "ICC T20 World Cup 2022",
            "ICC T20 World Cup 2024",
            "IPL 2020", "IPL 2021", "IPL 2022", "IPL 2023", "IPL 2024", "IPL 2025",
        ]
        for t in required:
            assert t in tournaments, f"Tournament '{t}' missing from database"

    def test_each_tournament_has_a_final(self):
        by_tournament = {}
        for m in MATCH_DATABASE:
            by_tournament.setdefault(m["tournament"], []).append(m)
        for tournament, matches in by_tournament.items():
            stages = [m["stage"].lower() for m in matches]
            assert any("final" in s for s in stages), (
                f"Tournament '{tournament}' has no Final match"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Known correct results (ground truth for fact-checking)
# ─────────────────────────────────────────────────────────────────────────────

class TestKnownResults:
    """
    These tests verify that the database stores factually correct results.
    If any of these fail, the database data needs correction — NOT the test.
    """

    def _find(self, match_id):
        for m in MATCH_DATABASE:
            if m["id"] == match_id:
                return m
        return None

    # T20 WC 2024
    def test_t20wc2024_final_india_beat_sa(self):
        m = self._find("t20wc2024_final")
        assert m is not None, "T20 WC 2024 final not found"
        assert m["winner"] == "India"
        assert m["loser"] == "South Africa"
        assert "7 runs" in m["result"]

    def test_t20wc2024_india_beat_pakistan_group(self):
        m = self._find("t20wc2024_ga_india_pak")
        assert m is not None, "T20 WC 2024 India vs Pakistan group match not found"
        assert m["winner"] == "India"
        assert m["loser"] == "Pakistan"

    def test_t20wc2024_india_beat_england_sf(self):
        m = self._find("t20wc2024_sf1")
        assert m is not None
        assert m["winner"] == "India"
        assert m["loser"] == "England"
        assert "68 runs" in m["result"]

    def test_t20wc2024_sa_beat_afghanistan_sf(self):
        m = self._find("t20wc2024_sf2")
        assert m is not None
        assert m["winner"] == "South Africa"
        assert m["loser"] == "Afghanistan"

    # T20 WC 2022
    def test_t20wc2022_final_england_beat_pakistan(self):
        m = self._find("t20wc2022_final")
        assert m is not None
        assert m["winner"] == "England"
        assert m["loser"] == "Pakistan"
        assert "5 wickets" in m["result"]

    def test_t20wc2022_sf_england_beat_india_10wkts(self):
        m = self._find("t20wc2022_sf2")
        assert m is not None
        assert m["winner"] == "England"
        assert m["loser"] == "India"
        assert "10 wickets" in m["result"]

    def test_t20wc2022_sf_pak_beat_nz(self):
        m = self._find("t20wc2022_sf1")
        assert m is not None
        assert m["winner"] == "Pakistan"
        assert m["loser"] == "New Zealand"

    def test_t20wc2022_india_beat_pakistan_kohli(self):
        m = self._find("t20wc2022_s12_india_pak")
        assert m is not None
        assert m["winner"] == "India"
        assert m["loser"] == "Pakistan"
        assert "Kohli" in m.get("notes", "")

    # T20 WC 2021
    def test_t20wc2021_final_australia_beat_nz(self):
        m = self._find("t20wc2021_final")
        assert m is not None
        assert m["winner"] == "Australia"
        assert m["loser"] == "New Zealand"
        assert "8 wickets" in m["result"]

    def test_t20wc2021_pakistan_beat_india_10wkts(self):
        """Pakistan beat India by 10 wkts — their first ever T20 WC win vs India."""
        m = self._find("t20wc2021_s12_pak_india")
        assert m is not None
        assert m["winner"] == "Pakistan"
        assert m["loser"] == "India"
        assert "10 wickets" in m["result"]
        # Verify scores: India 151/7, Pakistan 152/0
        assert "151" in m.get("team2_score", "") or "151" in m.get("team1_score", "")
        assert "152/0" in m.get("team1_score", "") or "152/0" in m.get("team2_score", "")

    # IPL finals
    def test_ipl2020_final_mi_beat_dc(self):
        m = self._find("ipl2020_final")
        assert m is not None
        assert m["winner"] == "Mumbai Indians"
        assert m["loser"] == "Delhi Capitals"
        assert "5 wickets" in m["result"]

    def test_ipl2021_final_csk_beat_kkr(self):
        m = self._find("ipl2021_final")
        assert m is not None
        assert m["winner"] == "Chennai Super Kings"
        assert m["loser"] == "Kolkata Knight Riders"
        assert "27 runs" in m["result"]

    def test_ipl2022_final_gt_beat_rr(self):
        m = self._find("ipl2022_final")
        assert m is not None
        assert m["winner"] == "Gujarat Titans"
        assert m["loser"] == "Rajasthan Royals"
        assert "7 wickets" in m["result"]

    def test_ipl2023_final_csk_beat_gt(self):
        m = self._find("ipl2023_final")
        assert m is not None
        assert m["winner"] == "Chennai Super Kings"
        assert m["loser"] == "Gujarat Titans"
        assert "5 wickets" in m["result"]

    def test_ipl2024_final_kkr_beat_srh(self):
        m = self._find("ipl2024_final")
        assert m is not None
        assert m["winner"] == "Kolkata Knight Riders"
        assert m["loser"] == "Sunrisers Hyderabad"
        assert "8 wickets" in m["result"]

    def test_ipl2025_final_rcb_beat_pbks(self):
        m = self._find("ipl2025_final")
        assert m is not None
        assert "Royal Challengers Bengaluru" in m["winner"]
        assert m["loser"] == "Punjab Kings"


# ─────────────────────────────────────────────────────────────────────────────
# Title history dicts
# ─────────────────────────────────────────────────────────────────────────────

class TestTitleHistory:
    def test_ipl_title_history_covers_2020_to_2025(self):
        for yr in range(2020, 2026):
            assert yr in IPL_TITLE_HISTORY, f"IPL {yr} missing from title history"

    def test_ipl_title_history_all_str_values(self):
        for yr, team in IPL_TITLE_HISTORY.items():
            assert isinstance(team, str) and len(team) > 0

    def test_t20_wc_winners_covers_key_editions(self):
        for yr in [2021, 2022, 2024]:
            assert yr in T20_WC_WINNERS

    def test_t20_wc_2021_winner(self):
        assert T20_WC_WINNERS[2021] == "Australia"

    def test_t20_wc_2022_winner(self):
        assert T20_WC_WINNERS[2022] == "England"

    def test_t20_wc_2024_winner(self):
        assert T20_WC_WINNERS[2024] == "India"

    def test_ipl2020_winner(self):
        assert IPL_TITLE_HISTORY[2020] == "Mumbai Indians"

    def test_ipl2021_winner(self):
        assert IPL_TITLE_HISTORY[2021] == "Chennai Super Kings"

    def test_ipl2022_winner(self):
        assert IPL_TITLE_HISTORY[2022] == "Gujarat Titans"

    def test_ipl2023_winner(self):
        assert IPL_TITLE_HISTORY[2023] == "Chennai Super Kings"

    def test_ipl2024_winner(self):
        assert IPL_TITLE_HISTORY[2024] == "Kolkata Knight Riders"

    def test_ipl2025_winner(self):
        assert "Royal Challengers" in IPL_TITLE_HISTORY[2025]


# ─────────────────────────────────────────────────────────────────────────────
# normalise_team
# ─────────────────────────────────────────────────────────────────────────────

class TestNormaliseTeam:
    def test_rcb_alias(self):
        assert normalise_team("rcb") == "Royal Challengers Bangalore"

    def test_mi_alias(self):
        assert normalise_team("mi") == "Mumbai Indians"

    def test_csk_alias(self):
        assert normalise_team("csk") == "Chennai Super Kings"

    def test_kkr_alias(self):
        assert normalise_team("kkr") == "Kolkata Knight Riders"

    def test_dc_alias(self):
        assert normalise_team("dc") == "Delhi Capitals"

    def test_srh_alias(self):
        assert normalise_team("srh") == "Sunrisers Hyderabad"

    def test_rr_alias(self):
        assert normalise_team("rr") == "Rajasthan Royals"

    def test_gt_alias(self):
        assert normalise_team("gt") == "Gujarat Titans"

    def test_lsg_alias(self):
        assert normalise_team("lsg") == "Lucknow Super Giants"

    def test_full_name_passthrough(self):
        assert normalise_team("India") == "India"

    def test_unknown_returns_as_is(self):
        assert normalise_team("UnknownTeam") == "UnknownTeam"

    def test_case_insensitive(self):
        assert normalise_team("MI") == normalise_team("mi")

    def test_whitespace_stripped(self):
        assert normalise_team("  mi  ") == "Mumbai Indians"

    def test_mumbai_word(self):
        assert normalise_team("mumbai") == "Mumbai Indians"

    def test_chennai_word(self):
        assert normalise_team("chennai") == "Chennai Super Kings"


# ─────────────────────────────────────────────────────────────────────────────
# search_matches
# ─────────────────────────────────────────────────────────────────────────────

class TestSearchMatches:
    def test_search_by_year_ipl2024(self):
        results = search_matches(year=2024, tournament="IPL")
        assert len(results) >= 4
        for m in results:
            assert m["season"] == 2024

    def test_search_india_pakistan_finds_all_3(self):
        results = search_matches(team1="India", team2="Pakistan")
        assert len(results) >= 3  # T20 WC 2021, 2022, 2024

    def test_search_india_pakistan_2021(self):
        results = search_matches(team1="India", team2="Pakistan", year=2021)
        assert len(results) == 1
        assert results[0]["winner"] == "Pakistan"

    def test_search_india_pakistan_2022(self):
        results = search_matches(team1="India", team2="Pakistan", year=2022)
        assert len(results) == 1
        assert results[0]["winner"] == "India"

    def test_search_india_pakistan_2024(self):
        results = search_matches(team1="India", team2="Pakistan", year=2024)
        assert len(results) == 1
        assert results[0]["winner"] == "India"

    def test_team_order_is_symmetric(self):
        """team1/team2 order should not affect results."""
        r1 = search_matches(team1="India", team2="Pakistan")
        r2 = search_matches(team1="Pakistan", team2="India")
        assert len(r1) == len(r2)

    def test_search_final_stage(self):
        results = search_matches(stage="Final")
        assert len(results) >= 8  # at minimum IPL 2020-2025 + T20 WC 2021/22/24

    def test_search_t20_wc_tournament(self):
        results = search_matches(tournament="T20 World Cup")
        assert len(results) >= 15
        for m in results:
            assert "T20 World Cup" in m["tournament"]

    def test_search_ipl_tournament(self):
        results = search_matches(tournament="IPL")
        assert len(results) >= 20
        for m in results:
            assert "IPL" in m["tournament"]

    def test_search_no_filters_returns_all(self):
        results = search_matches()
        assert len(results) == len(MATCH_DATABASE)

    def test_search_nonexistent_team_returns_empty(self):
        results = search_matches(team1="Nonexistent FC")
        assert results == []

    def test_search_kkr_aliases(self):
        r1 = search_matches(team1="kkr")
        r2 = search_matches(team1="Kolkata Knight Riders")
        assert len(r1) == len(r2)


# ─────────────────────────────────────────────────────────────────────────────
# format_match_as_text
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatMatchAsText:
    def test_returns_string(self):
        m = MATCH_DATABASE[0]
        text = format_match_as_text(m)
        assert isinstance(text, str)

    def test_contains_winner(self):
        m = next(x for x in MATCH_DATABASE if x["id"] == "t20wc2021_s12_pak_india")
        text = format_match_as_text(m)
        assert "Pakistan" in text

    def test_contains_loser(self):
        m = next(x for x in MATCH_DATABASE if x["id"] == "t20wc2021_s12_pak_india")
        text = format_match_as_text(m)
        assert "India" in text

    def test_contains_result(self):
        m = next(x for x in MATCH_DATABASE if x["id"] == "t20wc2021_s12_pak_india")
        text = format_match_as_text(m)
        assert "10 wickets" in text

    def test_contains_tournament_name(self):
        m = MATCH_DATABASE[0]
        text = format_match_as_text(m)
        assert m["tournament"] in text

    def test_contains_both_directions(self):
        """RAG text should mention both 'X won' and 'Y lost'."""
        m = next(x for x in MATCH_DATABASE if x["id"] == "t20wc2024_final")
        text = format_match_as_text(m)
        assert "India" in text
        assert "South Africa" in text

    def test_minimum_length(self):
        for m in MATCH_DATABASE:
            text = format_match_as_text(m)
            assert len(text) >= 80, f"Match {m['id']} text too short ({len(text)} chars)"


# ─────────────────────────────────────────────────────────────────────────────
# get_all_match_texts / get_summary_texts
# ─────────────────────────────────────────────────────────────────────────────

class TestRAGTexts:
    def test_get_all_match_texts_count(self):
        texts = get_all_match_texts()
        assert len(texts) == len(MATCH_DATABASE)

    def test_get_all_match_texts_all_strings(self):
        for t in get_all_match_texts():
            assert isinstance(t, str) and len(t) > 50

    def test_get_summary_texts_not_empty(self):
        summaries = get_summary_texts()
        assert len(summaries) >= 5

    def test_summary_contains_ipl_history(self):
        summaries = get_summary_texts()
        combined = "\n".join(summaries)
        assert "Mumbai Indians" in combined
        assert "Chennai Super Kings" in combined

    def test_summary_contains_t20_wc_history(self):
        summaries = get_summary_texts()
        combined = "\n".join(summaries)
        assert "Australia" in combined  # T20 WC 2021 winner
        assert "England" in combined    # T20 WC 2022 winner
        assert "India" in combined      # T20 WC 2024 winner

    def test_summary_contains_2025_info(self):
        summaries = get_summary_texts()
        combined = "\n".join(summaries)
        assert "2025" in combined

    def test_no_empty_texts(self):
        for i, t in enumerate(get_all_match_texts()):
            assert t.strip(), f"Match text at index {i} is empty"
