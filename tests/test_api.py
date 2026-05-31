"""
tests/test_api.py
-----------------
Integration tests for the FastAPI endpoints.

Run with:
  pytest tests/test_api.py -v

Requires the model to be trained (models/final_v5 or similar must exist).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /predict
# ---------------------------------------------------------------------------

class TestPredict:
    def test_basic_prediction(self):
        r = client.post("/predict", json={"text": "Scientists confirm the earth is round."})
        assert r.status_code == 200
        data = r.json()
        assert "severity" in data
        assert "confidence" in data
        assert "reasons" in data
        assert "recommendation" in data

    def test_severity_is_valid(self):
        r = client.post("/predict", json={"text": "The government is covering up the truth."})
        assert r.status_code == 200
        valid = {"Highly Deceptive", "Misleading", "Legitimate", "Uncertain"}
        assert r.json()["severity"] in valid

    def test_confidence_in_range(self):
        r = client.post("/predict", json={"text": "Vaccines cause autism according to a new study."})
        assert r.status_code == 200
        conf = r.json()["confidence"]
        assert 0 <= conf <= 100

    def test_empty_text_returns_400(self):
        r = client.post("/predict", json={"text": ""})
        assert r.status_code == 400

    def test_whitespace_text_returns_400(self):
        r = client.post("/predict", json={"text": "   "})
        assert r.status_code == 400

    def test_text_over_5000_chars_returns_400(self):
        r = client.post("/predict", json={"text": "a" * 5001})
        assert r.status_code == 400

    def test_conspiracy_text_highly_deceptive(self):
        r = client.post("/predict", json={
            "text": "The deep state is hiding classified files proving the moon landing was staged. "
                    "Big Pharma suppressed the cure for cancer for decades."
        })
        assert r.status_code == 200
        assert r.json()["severity"] == "Highly Deceptive"

    def test_reasons_is_list(self):
        r = client.post("/predict", json={"text": "Breaking: leaked document reveals secret truth."})
        assert r.status_code == 200
        assert isinstance(r.json()["reasons"], list)


# ---------------------------------------------------------------------------
# /scheduler/status
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_scheduler_status(self):
        r = client.get("/scheduler/status")
        assert r.status_code == 200
        assert "status" in r.json()


# ---------------------------------------------------------------------------
# Frontend routes
# ---------------------------------------------------------------------------

class TestFrontendRoutes:
    def test_home(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_index_html(self):
        r = client.get("/index.html")
        assert r.status_code == 200

    def test_features_html(self):
        r = client.get("/features.html")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# /sports/status
# ---------------------------------------------------------------------------

class TestSportsStatus:
    def test_status_returns_200(self):
        r = client.get("/sports/status")
        assert r.status_code == 200

    def test_status_has_total_matches(self):
        r = client.get("/sports/status")
        data = r.json()
        assert "total_matches" in data
        assert data["total_matches"] >= 40

    def test_status_has_by_tournament(self):
        r = client.get("/sports/status")
        data = r.json()
        assert "by_tournament" in data
        assert isinstance(data["by_tournament"], dict)

    def test_status_covers_ipl_and_t20wc(self):
        r = client.get("/sports/status")
        by_tournament = r.json()["by_tournament"]
        keys = " ".join(by_tournament.keys())
        assert "IPL" in keys
        assert "T20 World Cup" in keys

    def test_status_has_rag_loaded_field(self):
        r = client.get("/sports/status")
        assert "rag_loaded" in r.json()


# ---------------------------------------------------------------------------
# /sports/search
# ---------------------------------------------------------------------------

class TestSportsSearch:
    def test_search_no_filters(self):
        r = client.post("/sports/search", json={})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 40

    def test_search_by_year(self):
        r = client.post("/sports/search", json={"year": 2024, "tournament": "IPL"})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 4
        for m in data["matches"]:
            assert "2024" in m["tournament"] or m["tournament"] == "IPL 2024"

    def test_search_india_pakistan_all_years(self):
        r = client.post("/sports/search", json={"team1": "India", "team2": "Pakistan"})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 3

    def test_search_india_pak_2021_pakistan_won(self):
        r = client.post("/sports/search", json={
            "team1": "India", "team2": "Pakistan", "year": 2021
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["matches"][0]["winner"] == "Pakistan"

    def test_search_india_pak_2022_india_won(self):
        r = client.post("/sports/search", json={
            "team1": "India", "team2": "Pakistan", "year": 2022
        })
        assert r.status_code == 200
        assert r.json()["matches"][0]["winner"] == "India"

    def test_search_india_pak_2024_india_won(self):
        r = client.post("/sports/search", json={
            "team1": "India", "team2": "Pakistan", "year": 2024
        })
        assert r.status_code == 200
        assert r.json()["matches"][0]["winner"] == "India"

    def test_search_ipl2024_final(self):
        r = client.post("/sports/search", json={
            "tournament": "IPL 2024", "stage": "Final"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["matches"][0]["winner"] == "Kolkata Knight Riders"
        assert data["matches"][0]["loser"] == "Sunrisers Hyderabad"

    def test_search_ipl2025_final_rcb_won(self):
        r = client.post("/sports/search", json={
            "tournament": "IPL 2025", "stage": "Final"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert "Royal Challengers" in data["matches"][0]["winner"]

    def test_search_t20wc_2024_final_india_won(self):
        r = client.post("/sports/search", json={
            "tournament": "ICC T20 World Cup 2024", "stage": "Final"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["matches"][0]["winner"] == "India"
        assert "7 runs" in data["matches"][0]["result"]

    def test_search_t20wc_2021_final_australia_won(self):
        r = client.post("/sports/search", json={
            "tournament": "ICC T20 World Cup 2021", "stage": "Final"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["matches"][0]["winner"] == "Australia"

    def test_search_nonexistent_team_returns_count_0(self):
        r = client.post("/sports/search", json={"team1": "Nonexistent FC"})
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_search_response_has_required_fields(self):
        r = client.post("/sports/search", json={"year": 2024, "stage": "Final", "tournament": "IPL"})
        assert r.status_code == 200
        for m in r.json()["matches"]:
            for field in ["tournament", "stage", "date", "team1", "team2",
                          "winner", "loser", "result"]:
                assert field in m, f"Field '{field}' missing from match response"

    def test_search_team_aliases_work(self):
        r_alias = client.post("/sports/search", json={"team1": "kkr"})
        r_full  = client.post("/sports/search", json={"team1": "Kolkata Knight Riders"})
        assert r_alias.json()["count"] == r_full.json()["count"]

    def test_search_team_order_symmetric(self):
        r1 = client.post("/sports/search", json={"team1": "India", "team2": "England"})
        r2 = client.post("/sports/search", json={"team1": "England", "team2": "India"})
        assert r1.json()["count"] == r2.json()["count"]


# ---------------------------------------------------------------------------
# /sports/ingest — requires RAG to be initialised first; skip gracefully
# ---------------------------------------------------------------------------

class TestSportsIngest:
    def test_ingest_without_rag_returns_503(self):
        """Without /rag/init first, /sports/ingest should return 503."""
        r = client.post("/sports/ingest", json={})
        # RAG not initialised → 503
        assert r.status_code == 503
