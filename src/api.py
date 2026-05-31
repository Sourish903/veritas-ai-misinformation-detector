from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
import os
import threading

# Auto-load .env file if present (so GOOGLE_FC_KEY etc. work without manual export)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
except ImportError:
    pass  # python-dotenv not installed — env vars must be set manually

from src.predict import predict
from src.scheduler import fetch_and_finetune, full_retrain, start_scheduler
from src.sports_data import (
    search_matches, get_all_match_texts, get_summary_texts,
    normalise_team, MATCH_DATABASE, ingest_to_rag, CricAPI,
)

log = logging.getLogger("veritas.api")

# RAG dependencies (faiss, google-generativeai, etc.) are optional.
# Import lazily so the server starts even if they are not installed.
try:
    from src.rag.rag_pipeline import RAGPipeline
    _RAG_AVAILABLE = True
except ImportError as _rag_import_err:
    _RAG_AVAILABLE = False
    RAGPipeline = None  # type: ignore

app = FastAPI(title="Veritas AI - Misinformation Detection API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class TextInput(BaseModel):
    text: str

class RAGIngestRequest(BaseModel):
    texts: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None

class RAGQueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    return_sources: Optional[bool] = True

class RAGInitRequest(BaseModel):
    provider: str = "ollama"          # gemini | huggingface | ollama | groq
    api_key: Optional[str] = None     # not required for ollama
    model: Optional[str] = None
    store_path: Optional[str] = "rag_store"
    top_k: Optional[int] = 5

class SportsIngestRequest(BaseModel):
    cricapi_key: Optional[str] = None   # CricAPI key for extra live data
    fetch_series: Optional[List[str]] = None   # e.g. ["IPL 2024", "T20 World Cup 2024"]

class SportsSearchRequest(BaseModel):
    team1: Optional[str] = None
    team2: Optional[str] = None
    tournament: Optional[str] = None
    year: Optional[int] = None
    stage: Optional[str] = None

# ---------------------------------------------------------------------------
# Scheduler singleton
# ---------------------------------------------------------------------------

_scheduler = None

# ---------------------------------------------------------------------------
# RAG singleton — initialised lazily via /rag/init
# ---------------------------------------------------------------------------

_rag: Optional[RAGPipeline] = None


def _get_rag() -> RAGPipeline:
    if _rag is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialised. POST /rag/init first."
        )
    return _rag

# FIX 1: Added a startup health check so you immediately know if
# the model failed to load instead of getting a cryptic 500 error later
@app.on_event("startup")
def startup_check():
    has_final      = os.path.exists("models/config.json")
    has_checkpoint = os.path.exists("models/best_model_checkpoint/config.json")
    if not has_final and not has_checkpoint:
        raise RuntimeError(
            "No trained model found in models/ or models/best_model_checkpoint/. "
            "Please run data_preprocessing.py then train_model.py before starting the API."
        )
    print("[OK] Startup check passed - model files found.")

    # Start live-news background scheduler
    global _scheduler
    interval        = float(os.getenv("NEWS_UPDATE_HOURS",   "6"))
    run_now         = os.getenv("NEWS_RUN_ON_START",          "0") == "1"
    retrain_days    = float(os.getenv("NEWS_RETRAIN_DAYS",    "7"))
    weekly_retrain  = os.getenv("NEWS_WEEKLY_RETRAIN",        "1") != "0"
    _scheduler = start_scheduler(
        interval_hours=interval,
        run_on_start=run_now,
        retrain_days=retrain_days,
        weekly_retrain=weekly_retrain,
    )
    if _scheduler:
        print(f"[OK] Scheduler started — daily fetch every {interval}h, full retrain every {retrain_days}d.")
    else:
        print("[WARN] Scheduler not started (apscheduler not installed).")

    # Warn about missing optional API keys so users know what features are inactive
    _OPTIONAL_KEYS = {
        "GROQ_API_KEY":   "Groq LLM (RAG fact-checking & synthetic data generation)",
        "GEMINI_API_KEY": "Google Gemini LLM (RAG fact-checking)",
        "GOOGLE_FC_KEY":  "Google Fact Check Tools API (live news fetch)",
        "NEWS_API_KEY":   "NewsAPI (live news fetch)",
    }
    for key, desc in _OPTIONAL_KEYS.items():
        if not os.getenv(key):
            print(f"[WARN] {key} not set — {desc} will be unavailable.")


@app.on_event("shutdown")
def shutdown_scheduler():
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        print("[OK] Scheduler stopped.")

# FIX 2: Added a /health endpoint so you can quickly test if the API is alive
@app.get("/health")
def health():
    return {"status": "ok", "model": "loaded"}


@app.get("/scheduler/status")
def scheduler_status():
    """Return current state of the live-news background scheduler."""
    if _scheduler is None:
        return {
            "status": "not_running",
            "reason": "apscheduler not installed or scheduler disabled",
        }
    jobs = _scheduler.get_jobs()
    return {
        "status": "running",
        "jobs": [
            {
                "id": j.id,
                "next_run": str(j.next_run_time),
                "trigger": str(j.trigger),
            }
            for j in jobs
        ],
    }


@app.post("/scheduler/trigger")
def scheduler_trigger():
    """
    Manually trigger an immediate live-news fetch + fine-tune cycle.
    Runs in a background thread — returns immediately.
    """
    min_articles = int(os.getenv("NEWS_MIN_ARTICLES", "50"))
    threading.Thread(
        target=fetch_and_finetune,
        kwargs={"min_new": min_articles},
        daemon=True,
        name="manual-live-fetch",
    ).start()
    return {"status": "triggered", "message": "Live-news fetch started in background."}


@app.post("/scheduler/retrain")
def scheduler_full_retrain():
    """
    Manually trigger a full model retrain:
      1. data_preprocessing.py — merges all live news, balances classes
      2. train_model.py        — trains from scratch with Focal Loss

    Runs in a background thread — returns immediately.
    This is also triggered automatically every NEWS_RETRAIN_DAYS (default 7).
    """
    threading.Thread(
        target=full_retrain,
        daemon=True,
        name="manual-full-retrain",
    ).start()
    return {"status": "triggered", "message": "Full model retrain started in background."}


# Serve frontend pages
# FIX 3: Added os.path.exists check — previously would crash with unhandled
# FileNotFoundError if any frontend HTML file was missing
def serve_file(path: str):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return FileResponse(path, headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"})

@app.get("/")
def home():
    return serve_file("frontend/index.html")

@app.get("/index.html")
def index():
    return serve_file("frontend/index.html")

@app.get("/features.html")
def features():
    return serve_file("frontend/features.html")

@app.get("/faq.html")
def faq():
    return serve_file("frontend/faq.html")

@app.get("/about.html")
def about():
    return serve_file("frontend/about.html")

@app.get("/try-example.html")
def try_example():
    return serve_file("frontend/try-example.html")

@app.get("/how-it-works.html")
def how_it_works():
    return serve_file("frontend/how-it-works.html")

# Prediction endpoint
# FIX 4: Wrapped predict() in try/except so internal model errors return a
# clean JSON error instead of a 500 crash with a stack trace
@app.post("/predict")
def predict_text(input_data: TextInput):
    # FIX 5: Reject empty text early with a clear 400 error
    if not input_data.text or not input_data.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    if len(input_data.text) > 5000:
        raise HTTPException(status_code=400, detail="Input text exceeds 5000 character limit.")

    try:
        label, confidence, reasons, recommendation, content_type = predict(input_data.text, rag=_rag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    return {
        "severity": label,
        "confidence": confidence,
        "type": content_type,
        "reasons": reasons,
        "reason": "; ".join(reasons),
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# RAG endpoints
# ---------------------------------------------------------------------------

@app.post("/rag/init")
def rag_init(req: RAGInitRequest):
    """
    Initialise (or reinitialise) the RAG pipeline.

    Must be called once before /rag/ingest or /rag/query.
    The pipeline is held in memory for the lifetime of the server process.
    """
    if not _RAG_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                f"RAG dependencies are not installed ({_rag_import_err}). "
                "Run: pip install -r requirements.txt"
            ),
        )

    global _rag
    try:
        _rag = RAGPipeline(
            llm_provider=req.provider,
            llm_api_key=req.api_key,
            llm_model=req.model,
            store_path=req.store_path,
            top_k=req.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG init failed: {e}")

    return {
        "status": "ok",
        "provider": req.provider,
        "model": req.model or "default",
        "store_path": req.store_path,
        "documents_loaded": len(_rag.store),
    }


@app.post("/rag/ingest")
def rag_ingest(req: RAGIngestRequest):
    """
    Encode and store documents into the vector store.

    Accepts a list of text strings and optional metadata dicts.
    Chunks are automatically created and persisted to disk.
    """
    rag = _get_rag()

    if not req.texts:
        raise HTTPException(status_code=400, detail="texts list cannot be empty.")

    try:
        n_chunks = rag.ingest(texts=req.texts, metadatas=req.metadatas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return {
        "status": "ok",
        "documents_ingested": len(req.texts),
        "chunks_created": n_chunks,
        "total_documents": len(rag.store),
    }


@app.post("/rag/query")
def rag_query(req: RAGQueryRequest):
    """
    Retrieve relevant chunks and generate an LLM answer.

    Returns the answer and (optionally) the source passages used.
    """
    rag = _get_rag()

    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty.")

    try:
        result = rag.query(
            question=req.question,
            top_k=req.top_k,
            return_sources=req.return_sources,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    return result


@app.get("/rag/status")
def rag_status():
    """Return current RAG pipeline state (documents stored, provider info)."""
    if _rag is None:
        return {"status": "not_initialised", "documents": 0}
    return {
        "status": "ready",
        "llm_provider": repr(_rag.llm),
        "documents": len(_rag.store),
        "top_k": _rag.top_k,
    }


# ---------------------------------------------------------------------------
# Sports endpoints — T20 WC + IPL match verification
# ---------------------------------------------------------------------------

@app.post("/sports/ingest")
def sports_ingest(req: SportsIngestRequest):
    """
    Ingest all built-in cricket match data (T20 WC 2021/2022/2024 + IPL 2020-2024)
    into the RAG vector store so that fact-check queries like
    "did India beat Pakistan in T20 WC 2021?" return accurate answers.

    Optionally fetches additional live data via CricAPI (free tier, 100 calls/day).
    Requires the RAG pipeline to be initialised first via POST /rag/init.
    """
    rag = _get_rag()

    extra_matches = []
    if req.cricapi_key and req.fetch_series:
        try:
            api = CricAPI(req.cricapi_key)
            for series_name in req.fetch_series:
                extra_matches.extend(api.fetch_series_to_database(series_name))
        except Exception as e:
            log.warning(f"CricAPI fetch failed: {e} — continuing with static data only.")

    try:
        n_chunks = ingest_to_rag(rag, extra_matches=extra_matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sports ingestion failed: {e}")

    return {
        "status": "ok",
        "static_matches": len(MATCH_DATABASE),
        "cricapi_matches": len(extra_matches),
        "total_matches": len(MATCH_DATABASE),
        "chunks_created": n_chunks,
        "rag_documents": len(rag.store),
        "message": (
            "Sports data ingested. You can now POST /rag/query with questions like "
            "'Did India beat Pakistan in T20 WC 2021?' or 'Who won IPL 2024?'"
        ),
    }


@app.post("/sports/search")
def sports_search(req: SportsSearchRequest):
    """
    Direct match database lookup — no LLM needed.
    Returns raw match records matching the filters.

    Example: POST /sports/search  {"team1": "India", "team2": "Pakistan", "year": 2021}
    """
    try:
        results = search_matches(
            team1=req.team1,
            team2=req.team2,
            tournament=req.tournament,
            year=req.year,
            stage=req.stage,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    if not results:
        return {
            "count": 0,
            "matches": [],
            "message": "No matches found. Try broader filters or use POST /rag/query for natural-language lookup.",
        }

    return {
        "count": len(results),
        "matches": [
            {
                "tournament": m["tournament"],
                "stage": m["stage"],
                "date": m["date"],
                "venue": m.get("venue", ""),
                "team1": m["team1"],
                "team1_score": m.get("team1_score", ""),
                "team2": m["team2"],
                "team2_score": m.get("team2_score", ""),
                "winner": m["winner"],
                "loser": m["loser"],
                "result": m["result"],
                "notes": m.get("notes", ""),
            }
            for m in results
        ],
    }


@app.get("/sports/status")
def sports_status():
    """Return how many matches are in the static database."""
    from collections import Counter
    by_tournament = Counter(m["tournament"] for m in MATCH_DATABASE)
    return {
        "total_matches": len(MATCH_DATABASE),
        "by_tournament": dict(sorted(by_tournament.items())),
        "rag_loaded": _rag is not None,
        "tip": "POST /sports/ingest to load into RAG, then POST /rag/query to fact-check claims.",
    }
