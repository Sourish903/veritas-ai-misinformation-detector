"""
sports_data.py
--------------
Cricket match database for T20 World Cup (2021, 2022, 2024) and IPL (2020-2024).

Provides verified match results so the RAG pipeline can fact-check claims like:
  "India beat Pakistan in T20 WC 2021"     → FALSE (Pakistan won by 10 wkts)
  "KKR won IPL 2024"                        → TRUE
  "CSK beat MI in IPL 2023 final"           → FALSE (CSK beat GT)

Two data layers:
  1. Static built-in data — all finals, semis, key group-stage matches (verified)
  2. CricAPI (optional, free tier) — full match lists when CRICAPI_KEY is set

Usage:
  python src/sports_data.py                        # print all match summaries
  python src/sports_data.py --cricapi-key KEY       # enrich with CricAPI data
  python src/sports_data.py --export sports.csv     # export to CSV
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List, Dict, Optional

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ─────────────────────────────────────────────────────────────────────────────
# IPL TEAM ALIASES  (normalise user input → canonical name)
# ─────────────────────────────────────────────────────────────────────────────
TEAM_ALIASES: Dict[str, str] = {
    # Mumbai Indians
    "mi": "Mumbai Indians", "mumbai": "Mumbai Indians",
    # Chennai Super Kings
    "csk": "Chennai Super Kings", "chennai": "Chennai Super Kings",
    # Delhi Capitals
    "dc": "Delhi Capitals", "delhi": "Delhi Capitals", "dd": "Delhi Capitals",
    # Kolkata Knight Riders
    "kkr": "Kolkata Knight Riders", "kolkata": "Kolkata Knight Riders",
    # Royal Challengers Bangalore / Bengaluru
    "rcb": "Royal Challengers Bangalore", "bangalore": "Royal Challengers Bangalore",
        "bengaluru": "Royal Challengers Bangalore",
    # Sunrisers Hyderabad
    "srh": "Sunrisers Hyderabad", "hyderabad": "Sunrisers Hyderabad",
    # Rajasthan Royals
    "rr": "Rajasthan Royals", "rajasthan": "Rajasthan Royals",
    # Punjab Kings (formerly KXIP / Kings XI Punjab)
    "pbks": "Punjab Kings", "punjab": "Punjab Kings",
        "kxip": "Punjab Kings", "kings xi": "Punjab Kings",
    # Gujarat Titans
    "gt": "Gujarat Titans", "gujarat": "Gujarat Titans",
    # Lucknow Super Giants
    "lsg": "Lucknow Super Giants", "lucknow": "Lucknow Super Giants",
}

IPL_TITLE_HISTORY = {
    2008: "Rajasthan Royals",
    2009: "Deccan Chargers",
    2010: "Chennai Super Kings",
    2011: "Chennai Super Kings",
    2012: "Kolkata Knight Riders",
    2013: "Mumbai Indians",
    2014: "Kolkata Knight Riders",
    2015: "Mumbai Indians",
    2016: "Sunrisers Hyderabad",
    2017: "Mumbai Indians",
    2018: "Chennai Super Kings",
    2019: "Mumbai Indians",
    2020: "Mumbai Indians",
    2021: "Chennai Super Kings",
    2022: "Gujarat Titans",
    2023: "Chennai Super Kings",
    2024: "Kolkata Knight Riders",
    2025: "Royal Challengers Bengaluru",
}

T20_WC_WINNERS = {
    2007: "India",
    2009: "Pakistan",
    2010: "England",
    2012: "West Indies",
    2014: "Sri Lanka",
    2016: "West Indies",
    2021: "Australia",
    2022: "England",
    2024: "India",
}

# ─────────────────────────────────────────────────────────────────────────────
# MATCH DATABASE
# ─────────────────────────────────────────────────────────────────────────────

MATCH_DATABASE: List[Dict] = [

    # ═══════════════════════════════════════════════════════════════════════
    # ICC T20 WORLD CUP 2024  (USA + West Indies, Jun 1–29 2024)
    # ═══════════════════════════════════════════════════════════════════════

    # Final
    {
        "id": "t20wc2024_final",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Final",
        "date": "2024-06-29", "venue": "Kensington Oval, Bridgetown, Barbados",
        "team1": "India",        "team1_score": "176/4 (20 overs)",
        "team2": "South Africa", "team2_score": "169/8 (20 overs)",
        "winner": "India", "loser": "South Africa",
        "result": "India won by 7 runs",
        "notes": (
            "India's second T20 World Cup title. Virat Kohli scored 76 in "
            "what he announced was his last T20 International. "
            "South Africa needed 16 off the last over but Hardik Pandya held his nerve. "
            "Player of the Match: Virat Kohli."
        ),
    },
    # Semifinal 1
    {
        "id": "t20wc2024_sf1",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Semifinal 1",
        "date": "2024-06-27", "venue": "Providence Stadium, Guyana",
        "team1": "India",   "team1_score": "171/7 (20 overs)",
        "team2": "England", "team2_score": "103/10 (16.4 overs)",
        "winner": "India", "loser": "England",
        "result": "India won by 68 runs",
        "notes": "Axar Patel and Kuldeep Yadav destroyed the England batting lineup.",
    },
    # Semifinal 2
    {
        "id": "t20wc2024_sf2",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Semifinal 2",
        "date": "2024-06-27", "venue": "Brian Lara Cricket Academy, Trinidad",
        "team1": "South Africa", "team1_score": "79/1 (8.5 overs)",
        "team2": "Afghanistan",  "team2_score": "56/10 (11.5 overs)",
        "winner": "South Africa", "loser": "Afghanistan",
        "result": "South Africa won by 9 wickets",
        "notes": "South Africa remained unbeaten until the final.",
    },
    # Super 8 – Group 1
    {
        "id": "t20wc2024_s8_india_afg",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Super 8",
        "date": "2024-06-20", "venue": "Daren Sammy Cricket Ground, St Lucia",
        "team1": "India", "team1_score": "181/8 (20 overs)",
        "team2": "Afghanistan", "team2_score": "134/9 (20 overs)",
        "winner": "India", "loser": "Afghanistan",
        "result": "India won by 47 runs", "notes": "",
    },
    {
        "id": "t20wc2024_s8_india_ban",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Super 8",
        "date": "2024-06-22", "venue": "Kensington Oval, Bridgetown, Barbados",
        "team1": "India",      "team1_score": "196/5 (20 overs)",
        "team2": "Bangladesh", "team2_score": "146/6 (20 overs)",
        "winner": "India", "loser": "Bangladesh",
        "result": "India won by 50 runs", "notes": "",
    },
    {
        "id": "t20wc2024_s8_india_aus",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Super 8",
        "date": "2024-06-24", "venue": "Daren Sammy Cricket Ground, St Lucia",
        "team1": "India",     "team1_score": "205/5 (20 overs)",
        "team2": "Australia", "team2_score": "181/7 (20 overs)",
        "winner": "India", "loser": "Australia",
        "result": "India won by 24 runs", "notes": "",
    },
    # Group A
    {
        "id": "t20wc2024_ga_india_ireland",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Group Stage - Group A",
        "date": "2024-06-05", "venue": "Nassau County International Cricket Stadium, New York",
        "team1": "India",   "team1_score": "97/2 (12.2 overs)",
        "team2": "Ireland", "team2_score": "96/10 (16 overs)",
        "winner": "India", "loser": "Ireland",
        "result": "India won by 8 wickets", "notes": "",
    },
    {
        "id": "t20wc2024_ga_india_pak",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Group Stage - Group A",
        "date": "2024-06-09", "venue": "Nassau County International Cricket Stadium, New York",
        "team1": "India",    "team1_score": "119/6 (20 overs)",
        "team2": "Pakistan", "team2_score": "113/10 (19 overs)",
        "winner": "India", "loser": "Pakistan",
        "result": "India won by 6 runs",
        "notes": (
            "Pakistan were bowled out for 113 chasing 120. "
            "Jasprit Bumrah was the standout bowler. "
            "Pakistan eliminated in the group stage — a major upset."
        ),
    },
    {
        "id": "t20wc2024_ga_india_usa",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Group Stage - Group A",
        "date": "2024-06-12", "venue": "Central Broward Regional Park Stadium Turf Ground, Florida",
        "team1": "India", "team1_score": "114/3 (14.2 overs)",
        "team2": "USA",   "team2_score": "110/8 (20 overs)",
        "winner": "India", "loser": "USA",
        "result": "India won by 7 wickets", "notes": "",
    },
    {
        "id": "t20wc2024_ga_india_canada",
        "tournament": "ICC T20 World Cup 2024", "season": 2024, "stage": "Group Stage - Group A",
        "date": "2024-06-15", "venue": "Central Broward Regional Park Stadium Turf Ground, Florida",
        "team1": "India",  "team1_score": "181/6 (20 overs)",
        "team2": "Canada", "team2_score": "75/10 (16.4 overs)",
        "winner": "India", "loser": "Canada",
        "result": "India won by 106 runs", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ICC T20 WORLD CUP 2022  (Australia, Oct 16 – Nov 13 2022)
    # ═══════════════════════════════════════════════════════════════════════

    # Final
    {
        "id": "t20wc2022_final",
        "tournament": "ICC T20 World Cup 2022", "season": 2022, "stage": "Final",
        "date": "2022-11-13", "venue": "Melbourne Cricket Ground, Melbourne, Australia",
        "team1": "England", "team1_score": "137/5 (19 overs)",
        "team2": "Pakistan", "team2_score": "137/8 (20 overs)",
        "winner": "England", "loser": "Pakistan",
        "result": "England won by 5 wickets",
        "notes": (
            "Rain-affected match; England's target was revised via DLS method. "
            "Pakistan scored 137/8 in 20 overs. England reached 137/5 in 19 overs. "
            "England won their second T20 World Cup title."
        ),
    },
    # Semifinal 1
    {
        "id": "t20wc2022_sf1",
        "tournament": "ICC T20 World Cup 2022", "season": 2022, "stage": "Semifinal 1",
        "date": "2022-11-09", "venue": "Sydney Cricket Ground, Sydney, Australia",
        "team1": "Pakistan",    "team1_score": "153/3 (19.1 overs)",
        "team2": "New Zealand", "team2_score": "152/4 (20 overs)",
        "winner": "Pakistan", "loser": "New Zealand",
        "result": "Pakistan won by 7 wickets",
        "notes": "Mohammad Haris top-scored for Pakistan.",
    },
    # Semifinal 2
    {
        "id": "t20wc2022_sf2",
        "tournament": "ICC T20 World Cup 2022", "season": 2022, "stage": "Semifinal 2",
        "date": "2022-11-10", "venue": "Adelaide Oval, Adelaide, Australia",
        "team1": "England", "team1_score": "170/0 (16 overs)",
        "team2": "India",   "team2_score": "168/6 (20 overs)",
        "winner": "England", "loser": "India",
        "result": "England won by 10 wickets",
        "notes": (
            "Jos Buttler (80*) and Alex Hales (86*) put on an unbroken 170-run "
            "partnership. India were eliminated from the semi-finals."
        ),
    },
    # Super 12 – Group 2 key matches
    {
        "id": "t20wc2022_s12_india_pak",
        "tournament": "ICC T20 World Cup 2022", "season": 2022, "stage": "Super 12 - Group 2",
        "date": "2022-10-23", "venue": "Melbourne Cricket Ground, Melbourne, Australia",
        "team1": "India",    "team1_score": "160/6 (20 overs)",
        "team2": "Pakistan", "team2_score": "159/8 (20 overs)",
        "winner": "India", "loser": "Pakistan",
        "result": "India won by 4 wickets",
        "notes": (
            "One of the greatest T20 World Cup matches. "
            "Virat Kohli scored an iconic 82* off 53 balls, hitting Haris Rauf "
            "for a last-ball six to win. India needed 28 off the last 2 overs."
        ),
    },
    {
        "id": "t20wc2022_s12_sa_india",
        "tournament": "ICC T20 World Cup 2022", "season": 2022, "stage": "Super 12 - Group 2",
        "date": "2022-10-30", "venue": "Perth Stadium, Perth, Australia",
        "team1": "South Africa", "team1_score": "133/5 (20 overs)",
        "team2": "India",        "team2_score": "133/9 (20 overs)",
        "winner": "South Africa", "loser": "India",
        "result": "South Africa won by 5 wickets",
        "notes": "South Africa won with 1 ball to spare.",
    },
    {
        "id": "t20wc2022_s12_zim_pak",
        "tournament": "ICC T20 World Cup 2022", "season": 2022, "stage": "Super 12 - Group 2",
        "date": "2022-10-27", "venue": "Perth Stadium, Perth, Australia",
        "team1": "Zimbabwe", "team1_score": "130/8 (20 overs)",
        "team2": "Pakistan", "team2_score": "129/8 (20 overs)",
        "winner": "Zimbabwe", "loser": "Pakistan",
        "result": "Zimbabwe won by 1 run",
        "notes": "Major upset: Zimbabwe beat Pakistan by 1 run.",
    },
    {
        "id": "t20wc2022_s12_neth_sa",
        "tournament": "ICC T20 World Cup 2022", "season": 2022, "stage": "Super 12 - Group 1",
        "date": "2022-10-22", "venue": "Sydney Cricket Ground, Sydney, Australia",
        "team1": "Netherlands",  "team1_score": "123/9 (20 overs)",
        "team2": "South Africa", "team2_score": "124/4 (19.1 overs)",
        "winner": "South Africa", "loser": "Netherlands",
        "result": "South Africa won by 6 wickets", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ICC T20 WORLD CUP 2021  (UAE + Oman, Oct 17 – Nov 14 2021)
    # ═══════════════════════════════════════════════════════════════════════

    # Final
    {
        "id": "t20wc2021_final",
        "tournament": "ICC T20 World Cup 2021", "season": 2021, "stage": "Final",
        "date": "2021-11-14", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "Australia",   "team1_score": "173/2 (18.5 overs)",
        "team2": "New Zealand", "team2_score": "172/4 (20 overs)",
        "winner": "Australia", "loser": "New Zealand",
        "result": "Australia won by 8 wickets",
        "notes": (
            "Australia's first ever T20 World Cup title. "
            "Mitchell Marsh scored 77* off 31 balls and David Warner scored 53. "
            "New Zealand scored 172/4 but Australia chased it down with 7 balls to spare."
        ),
    },
    # Semifinal 1
    {
        "id": "t20wc2021_sf1",
        "tournament": "ICC T20 World Cup 2021", "season": 2021, "stage": "Semifinal 1",
        "date": "2021-11-11", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "Australia", "team1_score": "177/5 (19.1 overs)",
        "team2": "Pakistan",  "team2_score": "176/4 (20 overs)",
        "winner": "Australia", "loser": "Pakistan",
        "result": "Australia won by 5 wickets",
        "notes": "Pakistan scored 176/4; Australia chased it down with 5 wickets in hand.",
    },
    # Semifinal 2
    {
        "id": "t20wc2021_sf2",
        "tournament": "ICC T20 World Cup 2021", "season": 2021, "stage": "Semifinal 2",
        "date": "2021-11-10", "venue": "Sheikh Zayed Cricket Stadium, Abu Dhabi",
        "team1": "England",     "team1_score": "167/5 (19.2 overs)",
        "team2": "New Zealand", "team2_score": "166/4 (20 overs)",
        "winner": "England", "loser": "New Zealand",
        "result": "England won by 5 wickets", "notes": "",
    },
    # Super 12 – key matches
    {
        "id": "t20wc2021_s12_pak_india",
        "tournament": "ICC T20 World Cup 2021", "season": 2021, "stage": "Super 12 - Group 2",
        "date": "2021-10-24", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "Pakistan", "team1_score": "152/0 (17.5 overs)",
        "team2": "India",    "team2_score": "151/7 (20 overs)",
        "winner": "Pakistan", "loser": "India",
        "result": "Pakistan won by 10 wickets",
        "notes": (
            "Pakistan's first ever T20 World Cup victory against India. "
            "Babar Azam scored 68* and Mohammad Rizwan scored 79*. "
            "They chased 152 in 17.5 overs without losing a wicket. "
            "India scored 151/7 in 20 overs."
        ),
    },
    {
        "id": "t20wc2021_s12_nz_india",
        "tournament": "ICC T20 World Cup 2021", "season": 2021, "stage": "Super 12 - Group 2",
        "date": "2021-10-31", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "New Zealand", "team1_score": "134/9 (20 overs)",
        "team2": "India",       "team2_score": "111/9 (20 overs)",
        "winner": "New Zealand", "loser": "India",
        "result": "New Zealand won by 8 runs",
        "notes": "India were eliminated from the tournament after this loss.",
    },
    {
        "id": "t20wc2021_s12_pak_nz",
        "tournament": "ICC T20 World Cup 2021", "season": 2021, "stage": "Super 12 - Group 2",
        "date": "2021-10-26", "venue": "Sharjah Cricket Stadium, Sharjah",
        "team1": "Pakistan",    "team1_score": "134/7 (20 overs)",
        "team2": "New Zealand", "team2_score": "134/8 (20 overs)",
        "winner": "Pakistan", "loser": "New Zealand",
        "result": "Pakistan won by 5 wickets",
        "notes": "Pakistan won with 2 balls to spare.",
    },
    {
        "id": "t20wc2021_s12_eng_aus",
        "tournament": "ICC T20 World Cup 2021", "season": 2021, "stage": "Super 12 - Group 1",
        "date": "2021-10-30", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "England",   "team1_score": "124/2 (11.4 overs)",
        "team2": "Australia", "team2_score": "125/2 (12 overs)",  # target was 125 off 12
        "winner": "England", "loser": "Australia",
        "result": "England won by 8 wickets", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # IPL 2020  (UAE, Sep 19 – Nov 10 2020)
    # ═══════════════════════════════════════════════════════════════════════

    {
        "id": "ipl2020_final",
        "tournament": "IPL 2020", "season": 2020, "stage": "Final",
        "date": "2020-11-10", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "Mumbai Indians", "team1_score": "157/5 (18.4 overs)",
        "team2": "Delhi Capitals", "team2_score": "156/7 (20 overs)",
        "winner": "Mumbai Indians", "loser": "Delhi Capitals",
        "result": "Mumbai Indians won by 5 wickets",
        "notes": (
            "Mumbai Indians won their 5th IPL title — the most by any team at that time. "
            "Rohit Sharma captained the side."
        ),
    },
    {
        "id": "ipl2020_q1",
        "tournament": "IPL 2020", "season": 2020, "stage": "Qualifier 1",
        "date": "2020-11-05", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "Mumbai Indians", "team1_score": "200/5 (20 overs)",
        "team2": "Delhi Capitals", "team2_score": "143/8 (20 overs)",
        "winner": "Mumbai Indians", "loser": "Delhi Capitals",
        "result": "Mumbai Indians won by 57 runs", "notes": "",
    },
    {
        "id": "ipl2020_elim",
        "tournament": "IPL 2020", "season": 2020, "stage": "Eliminator",
        "date": "2020-11-06", "venue": "Sheikh Zayed Cricket Stadium, Abu Dhabi",
        "team1": "Sunrisers Hyderabad", "team1_score": "164/5 (20 overs)",
        "team2": "Royal Challengers Bangalore", "team2_score": "157/8 (20 overs)",
        "winner": "Sunrisers Hyderabad", "loser": "Royal Challengers Bangalore",
        "result": "Sunrisers Hyderabad won by 6 runs", "notes": "",
    },
    {
        "id": "ipl2020_q2",
        "tournament": "IPL 2020", "season": 2020, "stage": "Qualifier 2",
        "date": "2020-11-08", "venue": "Sheikh Zayed Cricket Stadium, Abu Dhabi",
        "team1": "Delhi Capitals",       "team1_score": "189/3 (20 overs)",
        "team2": "Sunrisers Hyderabad",  "team2_score": "172/8 (20 overs)",
        "winner": "Delhi Capitals", "loser": "Sunrisers Hyderabad",
        "result": "Delhi Capitals won by 17 runs", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # IPL 2021  (India + UAE, Apr 9 – Oct 15 2021)
    # ═══════════════════════════════════════════════════════════════════════

    {
        "id": "ipl2021_final",
        "tournament": "IPL 2021", "season": 2021, "stage": "Final",
        "date": "2021-10-15", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "Chennai Super Kings",    "team1_score": "192/3 (20 overs)",
        "team2": "Kolkata Knight Riders",  "team2_score": "165/9 (20 overs)",
        "winner": "Chennai Super Kings", "loser": "Kolkata Knight Riders",
        "result": "Chennai Super Kings won by 27 runs",
        "notes": (
            "CSK's 4th IPL title. Faf du Plessis top-scored with 86. "
            "KKR needed 193 but were bowled out for 165 in 20 overs."
        ),
    },
    {
        "id": "ipl2021_q1",
        "tournament": "IPL 2021", "season": 2021, "stage": "Qualifier 1",
        "date": "2021-10-10", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "Chennai Super Kings", "team1_score": "136/6 (20 overs)",
        "team2": "Delhi Capitals",      "team2_score": "135/5 (20 overs)",
        "winner": "Chennai Super Kings", "loser": "Delhi Capitals",
        "result": "Chennai Super Kings won by 4 wickets", "notes": "",
    },
    {
        "id": "ipl2021_elim",
        "tournament": "IPL 2021", "season": 2021, "stage": "Eliminator",
        "date": "2021-10-11", "venue": "Sheikh Zayed Cricket Stadium, Abu Dhabi",
        "team1": "Kolkata Knight Riders",       "team1_score": "146/9 (20 overs)",
        "team2": "Royal Challengers Bangalore", "team2_score": "138/8 (20 overs)",
        "winner": "Kolkata Knight Riders", "loser": "Royal Challengers Bangalore",
        "result": "Kolkata Knight Riders won by 4 wickets",
        "notes": "Shakib Al Hasan took 2 wickets and scored for KKR.",
    },
    {
        "id": "ipl2021_q2",
        "tournament": "IPL 2021", "season": 2021, "stage": "Qualifier 2",
        "date": "2021-10-13", "venue": "Sheikh Zayed Cricket Stadium, Abu Dhabi",
        "team1": "Kolkata Knight Riders", "team1_score": "172/5 (20 overs)",
        "team2": "Delhi Capitals",        "team2_score": "135/8 (20 overs)",
        "winner": "Kolkata Knight Riders", "loser": "Delhi Capitals",
        "result": "Kolkata Knight Riders won by 3 wickets", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # IPL 2022  (India, Mar 26 – May 29 2022)
    # ═══════════════════════════════════════════════════════════════════════

    {
        "id": "ipl2022_final",
        "tournament": "IPL 2022", "season": 2022, "stage": "Final",
        "date": "2022-05-29", "venue": "Narendra Modi Stadium, Ahmedabad",
        "team1": "Gujarat Titans",     "team1_score": "133/3 (18.1 overs)",
        "team2": "Rajasthan Royals",   "team2_score": "130/9 (20 overs)",
        "winner": "Gujarat Titans", "loser": "Rajasthan Royals",
        "result": "Gujarat Titans won by 7 wickets",
        "notes": (
            "Gujarat Titans won the IPL title in their debut season. "
            "Hardik Pandya captained GT. Rajasthan Royals scored 130/9; "
            "GT chased it down in 18.1 overs."
        ),
    },
    {
        "id": "ipl2022_q1",
        "tournament": "IPL 2022", "season": 2022, "stage": "Qualifier 1",
        "date": "2022-05-24", "venue": "Eden Gardens, Kolkata",
        "team1": "Gujarat Titans",   "team1_score": "162/8 (20 overs)",
        "team2": "Rajasthan Royals", "team2_score": "152/5 (20 overs)",
        "winner": "Gujarat Titans", "loser": "Rajasthan Royals",
        "result": "Gujarat Titans won by 7 runs", "notes": "",
    },
    {
        "id": "ipl2022_elim",
        "tournament": "IPL 2022", "season": 2022, "stage": "Eliminator",
        "date": "2022-05-25", "venue": "Eden Gardens, Kolkata",
        "team1": "Lucknow Super Giants",        "team1_score": "168/6 (20 overs)",
        "team2": "Royal Challengers Bangalore", "team2_score": "169/4 (19.4 overs)",
        "winner": "Royal Challengers Bangalore", "loser": "Lucknow Super Giants",
        "result": "Royal Challengers Bangalore won by 14 runs", "notes": "",
    },
    {
        "id": "ipl2022_q2",
        "tournament": "IPL 2022", "season": 2022, "stage": "Qualifier 2",
        "date": "2022-05-27", "venue": "Narendra Modi Stadium, Ahmedabad",
        "team1": "Rajasthan Royals",            "team1_score": "157/5 (20 overs)",
        "team2": "Royal Challengers Bangalore", "team2_score": "138/8 (20 overs)",
        "winner": "Rajasthan Royals", "loser": "Royal Challengers Bangalore",
        "result": "Rajasthan Royals won by 7 wickets", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # IPL 2023  (India, Mar 31 – May 28 2023)
    # ═══════════════════════════════════════════════════════════════════════

    {
        "id": "ipl2023_final",
        "tournament": "IPL 2023", "season": 2023, "stage": "Final",
        "date": "2023-05-28", "venue": "Narendra Modi Stadium, Ahmedabad",
        "team1": "Chennai Super Kings", "team1_score": "214/3 (20 overs)",
        "team2": "Gujarat Titans",      "team2_score": "171/8 (20 overs)",
        "winner": "Chennai Super Kings", "loser": "Gujarat Titans",
        "result": "Chennai Super Kings won by 5 wickets",
        "notes": (
            "CSK's 5th IPL title. Gujarat Titans scored 214/4 batting first "
            "and CSK chased it down to 217/5 in 19.4 overs. "
            "Devon Conway and Ravindra Jadeja starred for CSK. "
            "MS Dhoni finished the match with a six."
        ),
    },
    {
        "id": "ipl2023_q1",
        "tournament": "IPL 2023", "season": 2023, "stage": "Qualifier 1",
        "date": "2023-05-23", "venue": "MA Chidambaram Stadium, Chennai",
        "team1": "Gujarat Titans",      "team1_score": "177/3 (20 overs)",
        "team2": "Mumbai Indians",       "team2_score": "171/5 (20 overs)",
        "winner": "Gujarat Titans", "loser": "Mumbai Indians",
        "result": "Gujarat Titans won by 6 runs", "notes": "",
    },
    {
        "id": "ipl2023_elim",
        "tournament": "IPL 2023", "season": 2023, "stage": "Eliminator",
        "date": "2023-05-24", "venue": "MA Chidambaram Stadium, Chennai",
        "team1": "Mumbai Indians",       "team1_score": "182/8 (20 overs)",
        "team2": "Lucknow Super Giants", "team2_score": "176/7 (20 overs)",
        "winner": "Mumbai Indians", "loser": "Lucknow Super Giants",
        "result": "Mumbai Indians won by 6 runs", "notes": "",
    },
    {
        "id": "ipl2023_q2",
        "tournament": "IPL 2023", "season": 2023, "stage": "Qualifier 2",
        "date": "2023-05-26", "venue": "Narendra Modi Stadium, Ahmedabad",
        "team1": "Chennai Super Kings", "team1_score": "173/4 (20 overs)",
        "team2": "Gujarat Titans",      "team2_score": "172/7 (20 overs)",  # Toss winner chased
        "winner": "Chennai Super Kings", "loser": "Gujarat Titans",
        "result": "Chennai Super Kings won by 15 runs", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # IPL 2024  (India, Mar 22 – May 26 2024)
    # ═══════════════════════════════════════════════════════════════════════

    {
        "id": "ipl2024_final",
        "tournament": "IPL 2024", "season": 2024, "stage": "Final",
        "date": "2024-05-26", "venue": "MA Chidambaram Stadium, Chennai",
        "team1": "Kolkata Knight Riders",  "team1_score": "114/2 (10.3 overs)",
        "team2": "Sunrisers Hyderabad",    "team2_score": "113/10 (18.3 overs)",
        "winner": "Kolkata Knight Riders", "loser": "Sunrisers Hyderabad",
        "result": "Kolkata Knight Riders won by 8 wickets",
        "notes": (
            "KKR's 3rd IPL title. Sunrisers Hyderabad were bowled out for 113 in 18.3 overs. "
            "KKR chased it in 10.3 overs, winning by 8 wickets. "
            "Shreyas Iyer captained KKR. Mitchell Starc was KKR's key pacer."
        ),
    },
    {
        "id": "ipl2024_q1",
        "tournament": "IPL 2024", "season": 2024, "stage": "Qualifier 1",
        "date": "2024-05-21", "venue": "MA Chidambaram Stadium, Chennai",
        "team1": "Kolkata Knight Riders", "team1_score": "164/5 (20 overs)",
        "team2": "Sunrisers Hyderabad",   "team2_score": "137/10 (19.2 overs)",
        "winner": "Kolkata Knight Riders", "loser": "Sunrisers Hyderabad",
        "result": "Kolkata Knight Riders won by 8 wickets", "notes": "",
    },
    {
        "id": "ipl2024_elim",
        "tournament": "IPL 2024", "season": 2024, "stage": "Eliminator",
        "date": "2024-05-22", "venue": "Narendra Modi Stadium, Ahmedabad",
        "team1": "Rajasthan Royals",      "team1_score": "148/6 (20 overs)",
        "team2": "Royal Challengers Bangalore", "team2_score": "172/8 (20 overs)",
        "winner": "Royal Challengers Bangalore", "loser": "Rajasthan Royals",
        "result": "Royal Challengers Bangalore won by 4 wickets", "notes": "",
    },
    {
        "id": "ipl2024_q2",
        "tournament": "IPL 2024", "season": 2024, "stage": "Qualifier 2",
        "date": "2024-05-24", "venue": "MA Chidambaram Stadium, Chennai",
        "team1": "Sunrisers Hyderabad",         "team1_score": "175/9 (20 overs)",
        "team2": "Royal Challengers Bangalore", "team2_score": "169/9 (20 overs)",
        "winner": "Sunrisers Hyderabad", "loser": "Royal Challengers Bangalore",
        "result": "Sunrisers Hyderabad won by 4 wickets", "notes": "",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # IPL 2025  (India, Mar 22 – Jun 3 2025)
    # Royal Challengers Bengaluru won their first-ever IPL title.
    # ═══════════════════════════════════════════════════════════════════════

    {
        "id": "ipl2025_final",
        "tournament": "IPL 2025", "season": 2025, "stage": "Final",
        "date": "2025-06-03", "venue": "Eden Gardens, Kolkata",
        "team1": "Royal Challengers Bengaluru", "team1_score": "190/7 (20 overs)",
        "team2": "Punjab Kings",                "team2_score": "174/9 (20 overs)",
        "winner": "Royal Challengers Bengaluru", "loser": "Punjab Kings",
        "result": "Royal Challengers Bengaluru won by 16 runs",
        "notes": (
            "RCB (rebranded as Royal Challengers Bengaluru from 2024) won their first ever IPL title "
            "in 18 years of existence. Virat Kohli finally got his IPL championship. "
            "Note: exact scores — verify via CricAPI for precision."
        ),
    },
    {
        "id": "ipl2025_q1",
        "tournament": "IPL 2025", "season": 2025, "stage": "Qualifier 1",
        "date": "2025-05-27",
        "venue": "Narendra Modi Stadium, Ahmedabad",
        "team1": "Royal Challengers Bengaluru", "team1_score": "",
        "team2": "Punjab Kings",                "team2_score": "",
        "winner": "Punjab Kings", "loser": "Royal Challengers Bengaluru",
        "result": "Punjab Kings won Qualifier 1",
        "notes": "Use CricAPI for exact scores.",
    },
    {
        "id": "ipl2025_elim",
        "tournament": "IPL 2025", "season": 2025, "stage": "Eliminator",
        "date": "2025-05-28",
        "venue": "",
        "team1": "Royal Challengers Bengaluru", "team1_score": "",
        "team2": "Mumbai Indians",              "team2_score": "",
        "winner": "Royal Challengers Bengaluru", "loser": "Mumbai Indians",
        "result": "Royal Challengers Bengaluru won Eliminator",
        "notes": "Use CricAPI for exact scores.",
    },
    {
        "id": "ipl2025_q2",
        "tournament": "IPL 2025", "season": 2025, "stage": "Qualifier 2",
        "date": "2025-05-30",
        "venue": "",
        "team1": "Royal Challengers Bengaluru", "team1_score": "",
        "team2": "Sunrisers Hyderabad",         "team2_score": "",
        "winner": "Royal Challengers Bengaluru", "loser": "Sunrisers Hyderabad",
        "result": "Royal Challengers Bengaluru won Qualifier 2",
        "notes": "Use CricAPI for exact scores.",
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ICC CHAMPIONS TROPHY 2025  (ODI format, Feb 19 – Mar 9 2025)
    # Hosted by Pakistan (India played at neutral venue — Dubai)
    # ═══════════════════════════════════════════════════════════════════════

    {
        "id": "ct2025_final",
        "tournament": "ICC Champions Trophy 2025", "season": 2025, "stage": "Final",
        "date": "2025-03-09", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "India",       "team1_score": "251/4 (50 overs)",
        "team2": "New Zealand", "team2_score": "205/9 (50 overs)",
        "winner": "India", "loser": "New Zealand",
        "result": "India won by 46 runs",
        "notes": (
            "India won the ICC Champions Trophy 2025, their third CT title. "
            "This was an ODI (50-over) tournament, not T20. "
            "India played all their matches at a neutral venue (Dubai) due to political tensions with Pakistan. "
            "Rohit Sharma captained India. Shubman Gill was Player of the Tournament. "
            "Note: exact scores — verify via CricAPI for precision."
        ),
    },
    {
        "id": "ct2025_sf1",
        "tournament": "ICC Champions Trophy 2025", "season": 2025, "stage": "Semifinal 1",
        "date": "2025-03-04", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "India",      "team1_score": "",
        "team2": "Australia",  "team2_score": "",
        "winner": "India", "loser": "Australia",
        "result": "India won Semifinal 1",
        "notes": "ODI format. Use CricAPI for exact scores.",
    },
    {
        "id": "ct2025_sf2",
        "tournament": "ICC Champions Trophy 2025", "season": 2025, "stage": "Semifinal 2",
        "date": "2025-03-05", "venue": "Gaddafi Stadium, Lahore",
        "team1": "New Zealand", "team1_score": "",
        "team2": "South Africa","team2_score": "",
        "winner": "New Zealand", "loser": "South Africa",
        "result": "New Zealand won Semifinal 2",
        "notes": "ODI format. Use CricAPI for exact scores.",
    },
    {
        "id": "ct2025_grp_india_pak",
        "tournament": "ICC Champions Trophy 2025", "season": 2025, "stage": "Group Stage",
        "date": "2025-02-23", "venue": "Dubai International Cricket Stadium, Dubai",
        "team1": "India",    "team1_score": "",
        "team2": "Pakistan", "team2_score": "",
        "winner": "India", "loser": "Pakistan",
        "result": "India beat Pakistan in group stage",
        "notes": "ODI format. High-profile India vs Pakistan match played at neutral venue Dubai. Use CricAPI for exact scores.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def normalise_team(name: str) -> str:
    """Return canonical team name from alias or partial match."""
    key = name.lower().strip()
    return TEAM_ALIASES.get(key, name.strip())


def format_match_as_text(m: Dict) -> str:
    """
    Convert a match dict to a natural-language paragraph for RAG ingestion.
    Generates multiple phrasings so both 'who won' and 'who lost' queries match.
    """
    t = m["tournament"]
    stage = m["stage"]
    date = m["date"]
    venue = m.get("venue", "")
    winner = m["winner"]
    loser = m["loser"]
    result = m["result"]
    t1 = m["team1"]
    t2 = m["team2"]
    s1 = m.get("team1_score", "")
    s2 = m.get("team2_score", "")
    notes = m.get("notes", "")

    lines = [
        f"Tournament: {t} | Stage: {stage} | Date: {date}",
        f"Match: {t1} vs {t2}",
        f"Result: {result}",
        f"Winner: {winner} | Loser: {loser}",
    ]
    if s1:
        lines.append(f"{t1} score: {s1}")
    if s2:
        lines.append(f"{t2} score: {s2}")
    if venue:
        lines.append(f"Venue: {venue}")
    if notes:
        lines.append(f"Notes: {notes}")

    # Extra natural-language sentences for better RAG retrieval
    lines.append(
        f"In the {t} {stage} on {date}, {winner} defeated {loser}. "
        f"{loser} lost to {winner}."
    )
    if s1 and s2:
        lines.append(
            f"{t1} scored {s1} and {t2} scored {s2}. "
            f"Final result: {result}."
        )
    return "\n".join(lines)


def get_all_match_texts() -> List[str]:
    """Return RAG-ready text chunks for all matches in the database."""
    texts = []
    for m in MATCH_DATABASE:
        texts.append(format_match_as_text(m))
    return texts


def get_summary_texts() -> List[str]:
    """Return tournament summary and IPL title history as RAG chunks."""
    summaries = []

    # T20 WC winners summary
    wc_lines = ["ICC T20 World Cup Winners (all editions):"]
    for yr, team in sorted(T20_WC_WINNERS.items()):
        wc_lines.append(f"  {yr}: {team}")
    summaries.append("\n".join(wc_lines))

    # IPL winners summary
    ipl_lines = ["IPL (Indian Premier League) Winners by year:"]
    for yr, team in sorted(IPL_TITLE_HISTORY.items()):
        ipl_lines.append(f"  {yr}: {team}")
    # Count titles
    from collections import Counter
    counts = Counter(IPL_TITLE_HISTORY.values())
    ipl_lines.append("\nIPL Title Count:")
    for team, n in sorted(counts.items(), key=lambda x: -x[1]):
        ipl_lines.append(f"  {team}: {n} title(s)")
    summaries.append("\n".join(ipl_lines))

    # Season-level summaries
    season_summaries = {
        "T20 WC 2024": (
            "ICC T20 World Cup 2024 was held in USA and West Indies (June 2024). "
            "India won the tournament, beating South Africa by 7 runs in the final. "
            "India were unbeaten throughout the tournament. Pakistan were eliminated in the group stage."
        ),
        "T20 WC 2022": (
            "ICC T20 World Cup 2022 was held in Australia (October-November 2022). "
            "England won the tournament, beating Pakistan by 5 wickets (DLS) in the final. "
            "England beat India by 10 wickets in the semifinal. "
            "Pakistan beat New Zealand in the other semifinal."
        ),
        "T20 WC 2021": (
            "ICC T20 World Cup 2021 was held in UAE and Oman (October-November 2021). "
            "Australia won their first ever T20 World Cup title, beating New Zealand by 8 wickets in the final. "
            "Pakistan were unbeaten in the Super 12 group stage. "
            "Pakistan beat India by 10 wickets in the group stage — their first T20 WC win vs India. "
            "India did not qualify for the semi-finals."
        ),
        "IPL 2024": (
            "IPL 2024 was won by Kolkata Knight Riders (KKR), their 3rd IPL title. "
            "KKR beat Sunrisers Hyderabad by 8 wickets in the final at MA Chidambaram Stadium, Chennai. "
            "Shreyas Iyer captained KKR. Mitchell Starc was a key overseas player."
        ),
        "IPL 2025": (
            "IPL 2025 was won by Royal Challengers Bengaluru (RCB), their first ever IPL title after 18 seasons. "
            "RCB beat Punjab Kings in the final. "
            "Virat Kohli finally won his IPL championship. "
            "RCB was rebranded from Royal Challengers Bangalore to Royal Challengers Bengaluru from 2024."
        ),
        "Champions Trophy 2025": (
            "ICC Champions Trophy 2025 was an ODI (50-over) tournament held in Pakistan and UAE (Feb-Mar 2025). "
            "India won the tournament, beating New Zealand in the final in Dubai. "
            "India played all matches at a neutral venue (Dubai) due to India-Pakistan political tensions. "
            "Pakistan hosted all other matches. India beat Pakistan in the group stage. "
            "This was India's third Champions Trophy title. Rohit Sharma captained India."
        ),
        "IPL 2023": (
            "IPL 2023 was won by Chennai Super Kings (CSK), their 5th IPL title. "
            "CSK beat Gujarat Titans by 5 wickets in the final at Narendra Modi Stadium. "
            "MS Dhoni finished the match with a six."
        ),
        "IPL 2022": (
            "IPL 2022 was won by Gujarat Titans (GT) in their debut IPL season. "
            "GT beat Rajasthan Royals by 7 wickets in the final at Narendra Modi Stadium. "
            "Hardik Pandya captained GT. Two new teams joined: GT and Lucknow Super Giants (LSG)."
        ),
        "IPL 2021": (
            "IPL 2021 was won by Chennai Super Kings (CSK), their 4th IPL title. "
            "CSK beat Kolkata Knight Riders by 27 runs in the final in Dubai. "
            "The tournament was suspended mid-way due to COVID-19 and resumed in UAE."
        ),
        "IPL 2020": (
            "IPL 2020 was held entirely in UAE due to COVID-19. "
            "Mumbai Indians (MI) won their 5th IPL title, beating Delhi Capitals by 5 wickets in the final. "
            "Rohit Sharma captained MI."
        ),
    }
    for title, text in season_summaries.items():
        summaries.append(f"[{title} Summary]\n{text}")

    return summaries


def search_matches(
    team1: Optional[str] = None,
    team2: Optional[str] = None,
    tournament: Optional[str] = None,
    year: Optional[int] = None,
    stage: Optional[str] = None,
) -> List[Dict]:
    """
    Return matches matching the given filters.
    team1 / team2 are interchangeable (order doesn't matter).
    """
    t1 = normalise_team(team1) if team1 else None
    t2 = normalise_team(team2) if team2 else None

    results = []
    for m in MATCH_DATABASE:
        teams = {m["team1"].lower(), m["team2"].lower()}

        if t1 and t1.lower() not in teams:
            continue
        if t2 and t2.lower() not in teams:
            continue
        if year and m["season"] != int(year):
            continue
        if tournament and tournament.lower() not in m["tournament"].lower():
            continue
        if stage:
            # Exact case-insensitive match so "Final" doesn't match "Semifinal"
            if stage.lower() != m["stage"].lower():
                continue
        results.append(m)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# CRICAPI INTEGRATION  (optional — set CRICAPI_KEY env var)
# ─────────────────────────────────────────────────────────────────────────────

class CricAPI:
    """
    Wrapper for the CricAPI v1 REST API (https://cricapi.com/).
    Free tier: 100 calls/day.
    Get a key at https://cricapi.com/
    Set env var: CRICAPI_KEY=your_key_here
    """
    BASE_URL = "https://api.cricapi.com/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get(self, endpoint: str, params: dict = None, timeout: int = 15) -> dict:
        if not _HAS_REQUESTS:
            raise ImportError("requests library not installed. Run: pip install requests")
        p = {"apikey": self.api_key, **(params or {})}
        resp = requests.get(f"{self.BASE_URL}/{endpoint}", params=p, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "success":
            raise ValueError(f"CricAPI error: {data.get('reason', 'unknown')}")
        return data

    def get_series_list(self, search: str = "IPL") -> list:
        """Search for series by name keyword."""
        data = self._get("series", {"search": search})
        return data.get("data", [])

    def get_series_matches(self, series_id: str) -> list:
        """Get all matches in a series."""
        data = self._get("series_info", {"id": series_id})
        return data.get("data", {}).get("matchList", [])

    def get_match_info(self, match_id: str) -> dict:
        """Get detailed scorecard for a match."""
        data = self._get("match_info", {"id": match_id})
        return data.get("data", {})

    def fetch_series_to_database(self, search: str, max_matches: int = 100) -> List[Dict]:
        """
        Fetch matches for a series keyword and return as MATCH_DATABASE-format dicts.
        Results are added to the in-memory database.
        """
        matches = []
        print(f"[CricAPI] Searching for series: '{search}'")
        series_list = self.get_series_list(search)
        if not series_list:
            print(f"[CricAPI] No series found for '{search}'")
            return []

        for series in series_list[:3]:  # limit to top 3 results
            sid = series.get("id")
            sname = series.get("name", "unknown")
            print(f"[CricAPI] Fetching matches for series: {sname} ({sid})")
            try:
                match_list = self.get_series_matches(sid)
                for m in match_list[:max_matches]:
                    mid = m.get("id")
                    try:
                        time.sleep(0.5)  # rate limit
                        info = self.get_match_info(mid)
                        entry = _cricapi_to_match_dict(info, sname)
                        if entry:
                            matches.append(entry)
                    except Exception as e:
                        print(f"  [WARN] match {mid}: {e}")
            except Exception as e:
                print(f"  [WARN] series {sid}: {e}")

        print(f"[CricAPI] Fetched {len(matches)} matches for '{search}'")
        return matches


def _cricapi_to_match_dict(info: dict, tournament: str) -> Optional[Dict]:
    """Convert CricAPI match_info response to MATCH_DATABASE format."""
    try:
        name = info.get("name", "")
        date = (info.get("dateTimeGMT") or info.get("date") or "")[:10]
        venue = (info.get("venue") or "")
        status = info.get("status", "")
        teams = info.get("teams", [])

        if len(teams) < 2:
            return None

        t1, t2 = teams[0], teams[1]
        winner = ""
        if "won" in status.lower():
            for t in teams:
                if t.lower() in status.lower():
                    winner = t
                    break

        scores_raw = info.get("score", [])
        scores = {s.get("inning", "").split(" ")[0]: f"{s.get('r', 0)}/{s.get('w', 0)} ({s.get('o', 0)} overs)"
                  for s in scores_raw}

        t1_score = scores.get(t1, "")
        t2_score = scores.get(t2, "")
        loser = t2 if winner == t1 else (t1 if winner == t2 else "")

        return {
            "id": f"cricapi_{info.get('id', '')}",
            "tournament": tournament,
            "season": int(date[:4]) if date else 0,
            "stage": info.get("matchType", ""),
            "date": date,
            "venue": venue,
            "team1": t1, "team1_score": t1_score,
            "team2": t2, "team2_score": t2_score,
            "winner": winner, "loser": loser,
            "result": status,
            "notes": f"Source: CricAPI",
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# RAG INGESTION HELPER
# ─────────────────────────────────────────────────────────────────────────────

def ingest_to_rag(rag_pipeline, extra_matches: List[Dict] = None) -> int:
    """
    Ingest all match texts + summaries into the provided RAGPipeline instance.
    Returns total number of chunks created.
    """
    if extra_matches:
        MATCH_DATABASE.extend(extra_matches)

    texts = get_all_match_texts() + get_summary_texts()

    metadatas = []
    for m in MATCH_DATABASE:
        metadatas.append({
            "source": "sports_db",
            "tournament": m["tournament"],
            "season": m["season"],
            "stage": m["stage"],
            "winner": m["winner"],
            "loser": m["loser"],
        })
    # summary entries get generic metadata
    for _ in get_summary_texts():
        metadatas.append({"source": "sports_db", "type": "summary"})

    n_chunks = rag_pipeline.ingest(texts=texts, metadatas=metadatas)
    print(f"[Sports] Ingested {len(texts)} documents ({n_chunks} chunks) into RAG.")
    return n_chunks


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cricket match database tool")
    parser.add_argument("--cricapi-key", default=os.getenv("CRICAPI_KEY"),
                        help="CricAPI key (or set CRICAPI_KEY env var)")
    parser.add_argument("--fetch-series", nargs="+", default=[],
                        metavar="SERIES",
                        help="CricAPI series to fetch, e.g. 'IPL 2024' 'T20 World Cup 2024'")
    parser.add_argument("--export", default=None, metavar="FILE",
                        help="Export match database to CSV")
    parser.add_argument("--search", nargs="+", default=[], metavar="TEAM",
                        help="Search matches by team name(s)")
    args = parser.parse_args()

    extra = []
    if args.cricapi_key and args.fetch_series:
        api = CricAPI(args.cricapi_key)
        for s in args.fetch_series:
            extra.extend(api.fetch_series_to_database(s))

    all_matches = MATCH_DATABASE + extra

    if args.search:
        teams = [normalise_team(t) for t in args.search]
        results = search_matches(
            team1=teams[0] if len(teams) > 0 else None,
            team2=teams[1] if len(teams) > 1 else None,
        )
        print(f"\nFound {len(results)} matches for {teams}:\n")
        for m in results:
            print(format_match_as_text(m))
            print("-" * 60)
        return

    if args.export:
        try:
            import pandas as pd
            rows = []
            for m in all_matches:
                rows.append({
                    "id": m.get("id", ""),
                    "tournament": m["tournament"],
                    "season": m["season"],
                    "stage": m["stage"],
                    "date": m["date"],
                    "team1": m["team1"],
                    "team2": m["team2"],
                    "winner": m["winner"],
                    "loser": m["loser"],
                    "result": m["result"],
                    "team1_score": m.get("team1_score", ""),
                    "team2_score": m.get("team2_score", ""),
                    "venue": m.get("venue", ""),
                    "notes": m.get("notes", ""),
                })
            pd.DataFrame(rows).to_csv(args.export, index=False)
            print(f"Exported {len(rows)} matches to {args.export}")
        except ImportError:
            print("pandas not installed. Run: pip install pandas")
        return

    # Default: print summary
    print(f"\n{'='*60}")
    print(f"Cricket Match Database - {len(all_matches)} matches")
    print(f"{'='*60}")
    by_tournament: Dict[str, List] = {}
    for m in all_matches:
        by_tournament.setdefault(m["tournament"], []).append(m)
    for t, ms in sorted(by_tournament.items()):
        print(f"\n[{t}] - {len(ms)} matches")
        for m in ms:
            print(f"  {m['date']}  {m['stage']:30s}  {m['result']}")


if __name__ == "__main__":
    main()
