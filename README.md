# Veritas AI — Misinformation Detection System

A hybrid misinformation classifier that combines a fine-tuned DistilBERT model, 152 linguistic deception patterns, and an optional RAG fact-checking pipeline to classify text into three severity levels.

**Classes:**
- `Highly Deceptive` — Conspiracy-level fabrication, debunked claims, dangerous health misinformation
- `Misleading` — Exaggerated framing, vague sources, selective facts, sensationalism
- `Legitimate` — Credible, well-sourced, balanced reporting

**Best model performance (v6):** Macro F1 = 0.9008

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For RAG fact-checking (optional):
```bash
pip install -r requirements_rag.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in the optional keys:

```bash
cp .env.example .env
```

```env
# Optional — features degrade gracefully without these
GROQ_API_KEY=        # RAG fact-checking + synthetic data generation (free tier)
GEMINI_API_KEY=      # Google Gemini LLM for RAG fact-checking
GOOGLE_FC_KEY=       # Google Fact Check Tools API (live news fetch)
NEWS_API_KEY=        # NewsAPI (live news fetch)

# Scheduler settings
NEWS_UPDATE_HOURS=6   # How often to fetch live news (hours)
NEWS_MIN_ARTICLES=50  # Min articles before triggering fine-tune
NEWS_RETRAIN_DAYS=7   # Full retrain interval (days)
NEWS_RUN_ON_START=0   # Set to 1 to fetch immediately on startup
```

### 3. Train the model (first run)

```bash
# Step 1 — Prepare training data
python src/data_preprocessing.py --liar

# Step 2 — Train
python src/train_model.py --focal-loss --oversample --output models/final_v5
```

Training options:
```
--epochs 10          Max training epochs (default: 10)
--patience 4         Early stopping patience (default: 4)
--focal-loss         Use Focal Loss (recommended for imbalanced data)
--oversample         Oversample minority classes
--max-length 256     Longer token window (slower but better for long texts)
--resume-from PATH   Resume fine-tuning from an existing checkpoint
```

### 4. Start the server

```bash
# Windows
launch_veritas_ai.bat

# Or directly
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` in your browser.

---

## API Reference

### `POST /predict`
Classify a piece of text.

**Request:**
```json
{ "text": "5G towers are causing cancer and the government is covering it up." }
```

**Response:**
```json
{
  "severity": "Highly Deceptive",
  "confidence": 94.5,
  "type": "Health Misinformation",
  "reasons": ["Claims 5G causes cancer — no peer-reviewed evidence supports this.", "..."],
  "recommendation": "Do not share this content..."
}
```

### `GET /health`
Returns `{"status": "ok"}` — use for uptime checks.

### `GET /scheduler/status`
Returns current state of the live-news background scheduler and next run times.

### `POST /scheduler/trigger`
Manually trigger a live news fetch + fine-tune cycle (runs in background).

### `POST /scheduler/retrain`
Manually trigger a full model retrain from scratch (runs in background).

### RAG Endpoints (requires `requirements_rag.txt`)

| Endpoint | Method | Description |
|---|---|---|
| `/rag/init` | POST | Initialise the RAG pipeline with a chosen LLM provider |
| `/rag/ingest` | POST | Ingest documents into the FAISS vector store |
| `/rag/query` | POST | Retrieve relevant passages and generate an LLM answer |
| `/rag/status` | GET | Check RAG pipeline state |

**`POST /rag/init` body:**
```json
{
  "provider": "groq",
  "api_key": "your-groq-key",
  "store_path": "rag_store",
  "top_k": 5
}
```
Supported providers: `gemini`, `huggingface`, `ollama` (no key needed), `groq`

---

## Data Pipeline

### Add live news data
```bash
python src/fetch_live_news.py                        # RSS + GDELT (no key needed)
python src/fetch_live_news.py --google-fc-key KEY    # + Google Fact Check
python src/fetch_live_news.py --newsapi-key KEY      # + NewsAPI
python src/fetch_live_news.py --gdelt-history        # + historical 2022-2025
```

### Generate synthetic training data
```bash
# Using Groq API (free tier — requires GROQ_API_KEY in .env)
python src/generate_training_data.py

# Built-in (no API key needed)
python src/generate_synthetic_builtin.py
```

### Incremental fine-tune on live news
```bash
python src/fine_tune_live.py
```

### Evaluate the current model
```bash
python src/evaluate_model.py
```

---

## Project Structure

```
misinformation-detection/
├── src/
│   ├── api.py                    FastAPI server
│   ├── predict.py                Hybrid prediction engine
│   ├── train_model.py            DistilBERT training with Focal Loss
│   ├── data_preprocessing.py     Dataset preparation (LIAR + local + synthetic)
│   ├── fetch_live_news.py        Live news RSS/GDELT/API fetcher
│   ├── fine_tune_live.py         Incremental fine-tuning on live news
│   ├── scheduler.py              Background daily/weekly update jobs
│   ├── evaluate_model.py         Test-set evaluation
│   ├── generate_training_data.py Groq-based synthetic data generator
│   ├── generate_synthetic_builtin.py  Built-in synthetic data generator
│   └── rag/                      RAG pipeline (FAISS + DistilBERT encoder + LLM)
├── frontend/                     HTML/CSS/JS web interface
├── models/                       Trained model checkpoints
├── logs/                         Scheduler logs (auto-created)
├── .env.example                  Environment variable template
├── requirements.txt              Core dependencies
├── requirements_rag.txt          RAG-specific dependencies
└── launch_veritas_ai.bat         Windows launcher
```

---

## Model Architecture

- **Base:** `distilbert-base-uncased` (66M params, 40% faster than BERT)
- **Head:** 3-class linear classifier with dropout (0.4)
- **Loss:** Focal Loss (γ=2.0) + class weights + label smoothing (0.1)
- **Optimiser:** AdamW with differential LR — backbone 2e-5, head 1e-4
- **Scheduler:** Cosine with 10% warmup steps
- **Early stopping:** On macro F1 (not validation loss)
- **Training data:** ~51k samples (local Fake/True CSVs + LIAR dataset + synthetic)

---

## Logs

Scheduler activity is persisted to `logs/scheduler.log`. Server logs go to stdout.
