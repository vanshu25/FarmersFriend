# 🌾 Farmer's Friend — AI-Powered Livestock Triage Assistant

> **UIUC Precision Digital Agriculture Hackathon 2026**
> Track: Smart Livestock — Enhancing animal welfare, health, and productivity with digital monitoring and decision support under real farm constraints.

---

## Problem Statement

### The Core Crisis: Veterinary Shortage
Rural America faces a severe vet shortage — over 200 million Americans live in federally designated Veterinary Shortage Areas. Agricultural vets are retiring faster than replacements enter the field, leaving many rural counties with zero large-animal practitioners.

### What That Causes
Without timely access to veterinary guidance, farmers face a critical 24–72 hour gap between noticing symptoms and getting professional help. In that window:

### Treatable conditions escalate into severe infections
Contagious diseases spread through herds undetected. Farmers can't distinguish "monitor for 48 hours" from "act now"
 
A single mismanaged case can cost $2,000–$3,000. A BRD outbreak can wipe out 5–10% of a herd.
Farmer's Friend fills exactly that gap — not replacing vets, but providing the triage layer that tells farmers what they're looking at, how urgent it is, and what to do right now.

---

## Solution Overview

Farmer's Friend is a conversational AI triage assistant built for farmers. A farmer selects their animal species (cattle or chicken), answers a guided set of symptom questions, optionally uploads a photo, and receives a structured AI-generated health assessment with:

- Ranked list of possible conditions with confidence levels
- Immediate action steps tailored to the symptoms
- A severity rating (LOW / MEDIUM / HIGH / CRITICAL)
- Contextual next steps — monitor and isolate for MEDIUM, immediate vet alert for HIGH/CRITICAL
- A one-click pre-filled email to their veterinarian
- A persistent health dashboard tracking all animals over time

The system is designed for **zero technical overhead on the farmer's side** — no app install, no account, no vet degree required.

---

## Data Acquisition / Inputs

### Structured Symptom Collection
The dialogue engine (`dialogue.py`) collects inputs through a guided Q&A flow rather than free text, eliminating ambiguity:

| Input | Description |
|---|---|
| Species | Cattle or Chicken (single bird or flock) |
| Issue type | Physical / Behavioural / Both |
| Duration | Same-day → over a week |
| Visible signs | Multi-select per species (e.g. limping, bloating, discharge) |
| Eating & drinking status | Normal / Reduced / Not at all |
| Multiple animals affected | Yes / No / Unsure |
| Body area affected | Species-specific (e.g. udder, hooves, respiratory) |
| Dynamic follow-ups | Hoof detail injected for cattle with limping; RESP/DIGEST/NEURO branching for chickens |
| Animal ID | CO1–CO4 for cattle, CH1–CH3 for chickens — links triage to health history |

### Photo Input (Optional Multimodal)
Farmers can upload a photo of the affected animal. The image is base64-encoded and passed as a multimodal content block to Claude alongside the symptom text, enabling visual observations (swelling, discharge colour, posture) to inform the assessment.

### Knowledge Base
Agricultural extension documents and livestock health factsheets are pre-processed and stored as vector embeddings:
- Illinois Extension cattle health guides
- USDA BRD and respiratory disease factsheets
- Poultry health and flock management documents

---

## Processing / Model — Technical Approach

### RAG Pipeline (`rag_chain.py`)

The core inference pipeline uses **Retrieval-Augmented Generation (RAG)** to ground Claude's output in real veterinary literature rather than relying on LLM parametric memory alone.

```
Symptom answers
      │
      ▼
format_answers_for_prompt()         ← structured text summary
      │
      ▼
Query Embedding                     ← all-MiniLM-L6-v2 (384-dim, CPU, normalized)
      │
      ▼
ChromaDB similarity_search(k=4)     ← cosine distance < 1.5 threshold
      │
      ▼
build_user_prompt()                 ← symptom summary + retrieved chunks (---delimited)
      │
      ▼
Claude claude-sonnet-4-20250514              ← multimodal: text + optional image
      │
      ▼
JSON-constrained output             ← structured triage result
```

**Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
- 384-dimensional dense vectors
- Runs fully on CPU — no GPU required
- `normalize_embeddings=True` for cosine similarity

**Vector Store:** ChromaDB
- Persisted locally at `./chroma_db/`
- Collection name: `farmguard_livestock`
- Retrieval: top-4 chunks, cosine distance filtered at threshold 1.5

**Document Ingestion (`ingest.py`):**
- LangChain `RecursiveCharacterTextSplitter`: chunk size 500 tokens, overlap 50 tokens
- Balances context completeness with retrieval precision

**LLM: `claude-sonnet-4-20250514`**
- Anthropic Python SDK
- `max_tokens=1024`
- System prompt enforces: always cite sources, rank 2–3 conditions by likelihood, output valid JSON only, flag uncertainty explicitly, use farmer-friendly language
- Multimodal: image passed as `type: "image"` content block alongside text

### Structured JSON Output Schema

```json
{
  "likely_conditions": [
    { "name": "Foot Rot", "confidence": "HIGH", "explanation": "..." }
  ],
  "immediate_actions": ["Examine hooves for swelling...", "..."],
  "severity": "MEDIUM",
  "escalate_to_vet": false,
  "vet_summary": "Pre-written paragraph for vet email...",
  "cited_sources": ["Agricultural Extension Documents on Cattle Lameness"],
  "uncertainty_note": "Cannot confirm without physical examination...",
  "image_observations": "Visible swelling noted on left rear hoof..."
}
```

### Dynamic Question Branching
The dialogue engine adapts in real time based on prior answers:
- **Cattle + limping answer** → `maybe_insert_hoof_question()` injects a follow-up about hoof condition
- **Chicken single + respiratory signs** → `insert_chicken_detail_if_needed()` adds `CHICKEN_RESP_DETAIL` questions
- Same branching logic for digestive and neurological symptom patterns

### Animal Registry (`animal_registry.py`)
A lightweight flat-file persistence layer (`farm_data.json`) stores all registered animals and triage records with no database dependency:
- Auto-seeded with demo animals on first run (CO1–CO4 cattle, CH1–CH3 chickens)
- ID format: prefix (CO/CH) + farmer-supplied number
- `record_saved` flag prevents double-writes on Streamlit reruns
- All dashboard analytics are derived live from this file

---

## Outputs

### Triage Result Screen
| Output | Description |
|---|---|
| Severity banner | Color-coded: green (LOW), amber (MEDIUM), red (HIGH/CRITICAL) |
| Possible conditions | Ranked list with HIGH/MEDIUM/LOW confidence badges and explanations |
| Immediate actions | Numbered step-by-step farmer instructions |
| Uncertainty note | Explicit statement of what the AI cannot determine without physical exam |
| RAG sources | Document filenames cited in the assessment |
| Image observations | Vision analysis if photo was uploaded |

### Health Dashboard
Per-species analytics filtered by animal ID prefix:
- Total animals registered
- Total health checks performed
- High/critical incident count
- Vet alerts triggered
- Per-animal status table: last check date, severity, top condition, vet alerted flag
- Recent records timeline (last 10 checks), colour-coded by severity

### Farm Incident Report
Auto-generated printable report card containing animal ID, species, timestamp, all symptom answers, triage result, and action steps.

---

## Decision / Action Layer

Severity drives the post-triage UI, not the LLM's `escalate_to_vet` flag (which is used only for registry tracking):

| Severity | Action Card | Vet Contact |
|---|---|---|
| LOW | ✅ General care guidance | Not shown |
| MEDIUM | ⚠️ Monitor & Watch Closely — 4-tile grid: Isolate, Log & Observe, Re-check in 1–2 Days, When to Call Vet Now | 📧 Optional "Send Vet Observation Email" |
| HIGH | 🚨 Vet Consultation Required | 🚨 Mandatory — opens pre-filled mailto: email |
| CRITICAL | 🚨 Vet Consultation Required | 🚨 Mandatory — opens pre-filled mailto: email |

**Alert system (`alert.py`):** RFC-2368 `mailto:` protocol with pre-filled subject and body drawn from the LLM's `vet_summary` field. Zero external dependencies — works in any environment where the farmer has an email client.

---

## Feedback Loop

| Mechanism | Description |
|---|---|
| Health history dashboard | Every completed triage auto-saves to `farm_data.json`, building a longitudinal record per animal. Farmers and vets can see severity trends over time. |
| Re-check in 1–2 days | MEDIUM triage explicitly instructs the farmer to return and submit a new report, creating a follow-up data point. |
| Animal ID continuity | Because each triage is linked to a named animal ID (CO1, CH1 etc.), repeated checks on the same animal accumulate a health timeline visible on the dashboard. |
| Vet-in-the-loop | The pre-filled vet email includes the full symptom history and AI assessment, enabling the vet to review and correct the triage remotely — feeding ground truth back to the farmer. |

---

## Results

The system was tested against the following scenarios using real symptom profiles:

| Scenario | Severity | Top Condition | Source Cited |
|---|---|---|---|
| Cattle — limping, hoof swelling, 3 days | MEDIUM | Foot Rot (HIGH confidence) | Agricultural Extension: Cattle Lameness |
| Cattle — laboured breathing, multiple animals, fever | HIGH | Bovine Respiratory Disease (HIGH confidence) | USDA BRD Factsheet |
| Cattle — mild milk drop, normal eating | LOW | Mild Nutritional Deficiency (MEDIUM confidence) | Extension: Dairy Nutrition |
| Chicken single — lethargy, ruffled feathers, 2 days | MEDIUM | Coccidiosis / Newcastle Disease | Poultry Health Guide |
| Chicken flock — respiratory signs, multiple birds | HIGH | Avian Influenza / IB (escalate to vet) | Poultry Extension Docs |

RAG retrieval consistently returned relevant chunks (cosine distance < 0.9 for condition-specific queries). The JSON output schema was respected across all test runs. Judge Mode (cached HIGH/BRD result) demonstrates the full end-to-end output without an API key.

---

## Run Instructions

### Prerequisites

```bash
python >= 3.10
pip install streamlit anthropic langchain-community langchain-chroma \
            langchain-huggingface sentence-transformers chromadb Pillow
```

### 1. Ingest knowledge documents (one-time setup)

Place your `.pdf` and `.txt` livestock health documents in `./data/`, then run:

```bash
python ingest.py
```

This creates `./chroma_db/` with embedded document chunks. Skip this step if `chroma_db/` already exists.

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="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"
```

Or add it to a `.env` file / Streamlit secrets (for cloud deployment).

### 3. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 4. Judge / Demo Mode

The app launches with **Judge Mode enabled by default** — no API key required. The full triage flow runs using a cached HIGH-severity BRD result that demonstrates every output component. Toggle Judge Mode off in the sidebar to use live Claude inference.

### Cloud Deployment (Streamlit Community Cloud)

1. Push repo to GitHub (commit `farm_data.json` for pre-seeded demo data)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select repo and `app.py`
3. Under Advanced Settings → Secrets, add: `ANTHROPIC_API_KEY = "sk-ant-..."`
4. Deploy — live shareable link in ~3 minutes

### File Structure

```
farmguard-ai/
├── app.py                  # Streamlit UI + session state router
├── animal_registry.py      # Flat-file persistence (farm_data.json)
├── dialogue.py             # Structured question trees per species
├── rag_chain.py            # RAG pipeline: ChromaDB + embeddings + Claude API
├── alert.py                # Vet alert: mailto: + Twilio SMS (optional)
├── ingest.py               # One-time document ingestion → ChromaDB
├── requirements.txt        # Python dependencies
├── farm_data.json          # Auto-created; stores animals + triage records
└── data/                   # Source documents for RAG (PDFs, TXTs)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.32+ |
| LLM | claude-sonnet-4-20250514 (Anthropic SDK) |
| RAG Framework | LangChain Community |
| Vector Store | ChromaDB (local persistence) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384-dim, CPU) |
| Image Analysis | Claude Multimodal Vision (base64 content blocks) |
| Persistence | JSON flat-file (`farm_data.json`) |
| Alert System | RFC-2368 `mailto:` protocol |

---

*Built for the UIUC Precision Digital Agriculture Hackathon 2026 — Smart Livestock Track.*
