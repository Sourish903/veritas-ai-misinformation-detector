"""
scheduler.py
------------
Background scheduler that keeps the model up-to-date with live news.

Daily job (every NEWS_UPDATE_HOURS, default 24h):
  1. Fetches live news articles from RSS / GDELT via fetch_live_news.py
  2. Deduplicates against existing training data
  3. Saves balanced articles to src/live_news.csv
  4. Triggers fine_tune_live.py when >= NEWS_MIN_ARTICLES articles accumulate

Weekly full retrain (every NEWS_RETRAIN_DAYS, default 7 days):
  1. Re-runs data_preprocessing.py --live-news auto (merges accumulated live news)
  2. Runs train_model.py from scratch on the enriched, balanced dataset
  3. Ensures the model is periodically retrained on ALL data, not just incremental

Integrated into api.py — starts automatically with the server.
Environment variables:
  NEWS_UPDATE_HOURS   — daily fetch interval in hours  (default: 24)
  NEWS_MIN_ARTICLES   — min articles needed before fine-tuning  (default: 50)
  NEWS_RUN_ON_START   — set to "1" to run a fetch immediately at startup
  NEWS_RETRAIN_DAYS   — full retrain interval in days  (default: 7)
  NEWS_WEEKLY_RETRAIN — set to "0" to disable weekly full retrain
"""

import logging
import os
import subprocess
import sys
import threading

log = logging.getLogger("veritas.scheduler")
log.setLevel(logging.INFO)

# Persist scheduler output to logs/scheduler.log so it survives server restarts
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_fh = logging.FileHandler(os.path.join(_LOG_DIR, "scheduler.log"), encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
log.addHandler(_fh)

SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SRC_DIR, "..")


def fetch_and_finetune(min_new: int = 50) -> None:
    """Fetch live news (with class balancing), then fine-tune if enough articles."""
    log.info("[scheduler] Starting daily live news fetch...")

    # ── Step 1: fetch live news ────────────────────────────────────────────────
    # Pass --balance so the output CSV has equal class representation before
    # fine-tuning; also include --gdelt-history once per day for recent 2022+ data
    try:
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(SRC_DIR, "fetch_live_news.py"),
                "--balance",
                "--balance-strategy", "median",
            ],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=ROOT_DIR,
        )
        if result.returncode != 0:
            log.error("[scheduler] fetch_live_news.py failed:\n%s", result.stderr[-1000:])
            return
        log.info("[scheduler] fetch_live_news.py finished:\n%s", result.stdout[-800:])
    except subprocess.TimeoutExpired:
        log.warning("[scheduler] fetch_live_news.py timed out (300s) — skipping")
        return
    except Exception as exc:
        log.error("[scheduler] fetch_live_news.py error: %s", exc)
        return

    # ── Step 2: check article count ────────────────────────────────────────────
    live_path = os.path.join(SRC_DIR, "live_news.csv")
    if not os.path.exists(live_path):
        log.warning("[scheduler] live_news.csv not found after fetch — skipping fine-tune")
        return

    try:
        import pandas as pd
        count = len(pd.read_csv(live_path))
    except Exception as exc:
        log.error("[scheduler] Cannot read live_news.csv: %s", exc)
        return

    if count < min_new:
        log.info(
            "[scheduler] Only %d articles available (threshold: %d) — skipping fine-tune",
            count, min_new,
        )
        return

    # ── Step 3: fine-tune ─────────────────────────────────────────────────────
    log.info("[scheduler] %d balanced articles ready — starting fine-tune...", count)
    try:
        ft = subprocess.run(
            [sys.executable, os.path.join(SRC_DIR, "fine_tune_live.py")],
            capture_output=True,
            text=True,
            timeout=7200,   # 2 hours max
            cwd=ROOT_DIR,
        )
        if ft.returncode != 0:
            log.error("[scheduler] fine_tune_live.py failed:\n%s", ft.stderr[-1000:])
        else:
            log.info("[scheduler] Daily fine-tune complete:\n%s", ft.stdout[-800:])
    except subprocess.TimeoutExpired:
        log.warning("[scheduler] fine_tune_live.py timed out (2h)")
    except Exception as exc:
        log.error("[scheduler] fine_tune_live.py error: %s", exc)


def full_retrain() -> None:
    """
    Full retraining pipeline:
      1. Re-run data_preprocessing.py merging accumulated live news + class balancing
      2. Re-run train_model.py with Focal Loss for best-in-class balance handling

    This runs weekly so the model is periodically rebuilt on ALL available data,
    not just fine-tuned incrementally.  Focal Loss + oversampling + class weights
    ensure no single label dominates after the rebuild.
    """
    log.info("[scheduler] Starting weekly full retrain...")

    # Step 1: rebuild balanced train/test CSVs with all accumulated live news
    try:
        pp = subprocess.run(
            [
                sys.executable,
                os.path.join(SRC_DIR, "data_preprocessing.py"),
                "--liar",
                "--live-news", "auto",   # merges src/live_news.csv
                "--balance",             # equalises class counts
            ],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=ROOT_DIR,
        )
        if pp.returncode != 0:
            log.error("[scheduler] data_preprocessing.py failed:\n%s", pp.stderr[-1000:])
            return
        log.info("[scheduler] Data preprocessing done:\n%s", pp.stdout[-600:])
    except subprocess.TimeoutExpired:
        log.warning("[scheduler] data_preprocessing.py timed out (10min)")
        return
    except Exception as exc:
        log.error("[scheduler] data_preprocessing.py error: %s", exc)
        return

    # Step 2: full retrain with Focal Loss
    try:
        tr = subprocess.run(
            [
                sys.executable,
                os.path.join(SRC_DIR, "train_model.py"),
                "--focal-loss",          # Focal Loss handles remaining imbalance
                "--epochs", "10",
                "--patience", "4",
            ],
            capture_output=True,
            text=True,
            timeout=21600,   # 6 hours max
            cwd=ROOT_DIR,
        )
        if tr.returncode != 0:
            log.error("[scheduler] train_model.py failed:\n%s", tr.stderr[-1000:])
        else:
            log.info("[scheduler] Weekly full retrain complete:\n%s", tr.stdout[-800:])
    except subprocess.TimeoutExpired:
        log.warning("[scheduler] train_model.py timed out (6h)")
    except Exception as exc:
        log.error("[scheduler] train_model.py error: %s", exc)


def start_scheduler(
    interval_hours: float = 6.0,
    run_on_start: bool = False,
    retrain_days: float = 7.0,
    weekly_retrain: bool = True,
):
    """
    Start the APScheduler background scheduler.

    Parameters
    ----------
    interval_hours : float
        How often to run the daily fetch-and-finetune job (default 24 hours).
    run_on_start : bool
        If True, run the first fetch immediately in a background thread.
    retrain_days : float
        How often to run the weekly full-retrain job (default 7 days).
    weekly_retrain : bool
        Whether to enable the weekly full-retrain job (default True).

    Returns
    -------
    scheduler : BackgroundScheduler | None
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        log.warning(
            "[scheduler] apscheduler not installed — live updates disabled. "
            "Run: pip install apscheduler>=3.10.0"
        )
        return None

    min_articles = int(os.getenv("NEWS_MIN_ARTICLES", "50"))

    scheduler = BackgroundScheduler(daemon=True)

    # Daily fetch + fine-tune job
    scheduler.add_job(
        fetch_and_finetune,
        kwargs={"min_new": min_articles},
        trigger="interval",
        hours=interval_hours,
        id="live_news_update",
        max_instances=1,
        misfire_grace_time=3600,
        replace_existing=True,
    )
    log.info(
        "[scheduler] Daily live-news job scheduled (every %.1fh, min_articles=%d)",
        interval_hours, min_articles,
    )

    # Weekly full retrain job
    if weekly_retrain:
        scheduler.add_job(
            full_retrain,
            trigger="interval",
            days=retrain_days,
            id="weekly_full_retrain",
            max_instances=1,
            misfire_grace_time=7200,
            replace_existing=True,
        )
        log.info("[scheduler] Weekly full-retrain job scheduled (every %.1f days)", retrain_days)

    scheduler.start()

    if run_on_start:
        threading.Thread(
            target=fetch_and_finetune,
            kwargs={"min_new": min_articles},
            daemon=True,
            name="initial-live-fetch",
        ).start()
        log.info("[scheduler] Initial fetch triggered in background thread.")

    return scheduler
