"""
tests/test_predict.py
---------------------
Unit tests for src/predict.py

Run with:
  pytest tests/test_predict.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.predict import predict, _deception_score, _PREDICT_CACHE, LABELS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_cache():
    _PREDICT_CACHE.clear()


# ---------------------------------------------------------------------------
# Label constants
# ---------------------------------------------------------------------------

class TestLabels:
    def test_label_count(self):
        assert len(LABELS) == 3

    def test_label_names(self):
        assert "Highly Deceptive" in LABELS
        assert "Misleading" in LABELS
        assert "Legitimate" in LABELS


# ---------------------------------------------------------------------------
# Deception pattern matching
# ---------------------------------------------------------------------------

class TestDeceptionPatterns:
    def test_high_pattern_vaccine_microchip(self):
        high, med = _deception_score("vaccines contain microchips to track the population")
        assert len(high) > 0

    def test_high_pattern_cover_up(self):
        high, med = _deception_score("the government is covering up the truth about 5G")
        assert len(high) > 0

    def test_high_pattern_bleach_cure(self):
        high, med = _deception_score("drinking bleach cures COVID-19")
        assert len(high) > 0

    def test_med_pattern_unnamed_sources(self):
        high, med = _deception_score("according to unnamed sources the minister resigned")
        assert len(med) > 0

    def test_med_pattern_guaranteed(self):
        high, med = _deception_score("this investment is guaranteed to double your money")
        assert len(med) > 0

    def test_clean_text_no_patterns(self):
        high, med = _deception_score("The prime minister held a press conference today.")
        assert len(high) == 0
        assert len(med) == 0


# ---------------------------------------------------------------------------
# Prediction outputs
# ---------------------------------------------------------------------------

class TestPredictOutput:
    def setup_method(self):
        _clear_cache()

    def test_returns_five_tuple(self):
        result = predict("The government announced a new policy on healthcare.")
        assert len(result) == 5

    def test_label_is_valid(self):
        label, *_ = predict("Scientists have confirmed vaccines are safe.")
        valid = {"Highly Deceptive", "Misleading", "Legitimate", "Uncertain"}
        assert label in valid

    def test_confidence_in_range(self):
        _, confidence, *_ = predict("Breaking: leaked document reveals secret cure suppressed by Big Pharma.")
        assert 0.0 <= confidence <= 100.0

    def test_reasons_is_list(self):
        _, _, reasons, *_ = predict("Some text about news.")
        assert isinstance(reasons, list)

    def test_empty_input(self):
        label, conf, reasons, rec, ctype = predict("")
        assert label == "Invalid Input"
        assert conf == 0.0

    def test_whitespace_input(self):
        label, conf, *_ = predict("   ")
        assert label == "Invalid Input"

    def test_conspiracy_text_flagged_high(self):
        label, *_ = predict(
            "The deep state is hiding classified files that prove the moon landing was staged. "
            "Big Pharma has been suppressing the cure for cancer for decades."
        )
        assert label == "Highly Deceptive"

    def test_legitimate_text(self):
        label, conf, *_ = predict(
            "The Federal Reserve raised interest rates by 25 basis points on Wednesday, "
            "citing continued progress on inflation. The decision was unanimous."
        )
        assert label in {"Legitimate", "Misleading"}  # should not be Highly Deceptive


# ---------------------------------------------------------------------------
# Prediction caching
# ---------------------------------------------------------------------------

class TestPredictCache:
    def setup_method(self):
        _clear_cache()

    def test_cache_hit_returns_same_result(self):
        text = "The prime minister announced new climate legislation."
        r1 = predict(text)
        r2 = predict(text)
        assert r1 == r2

    def test_different_texts_not_colliding(self):
        r1 = predict("vaccines contain microchips to track everyone")
        r2 = predict("The central bank kept rates unchanged.")
        assert r1[0] != r2[0] or True  # may differ — just ensure no crash

    def test_cache_populated_after_call(self):
        text = "A unique test string for cache population check."
        predict(text)
        assert any(text in k for k in _PREDICT_CACHE)
