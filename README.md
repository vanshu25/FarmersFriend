# 🌾 FarmGuard AI
**Precision Digital Agriculture Hackathon 2026 — Smart Livestock Track**

> RAG-powered livestock triage for farmers. Tap your animal, answer a few questions, get evidence-backed guidance.

---

## Problem Statement
Farmers managing livestock health face two major friction points: (1) they can't quickly find relevant veterinary guidance across scattered extension publications, and (2) they often don't know when a symptom warrants calling a vet. Delayed action on conditions like BRD, mastitis, or bloat costs lives and money. Existing tools require technical literacy farmers don't have time for.

**Who:** Livestock farmers managing cattle, poultry, swine, or sheep  
**What:** Deciding whether to monitor, treat, or call a vet  
**Why:** Faster, evidence-backed triage reduces animal loss and unnecessary vet costs

---

## Solution Overview

**FarmGuard AI** is a guided, farmer-friendly triage assistant backed by a RAG pipeline over Illinois Extension and USDA livestock health documents.

```
Animal Selection → Guided Symptom Dialogue (yes/no + taps)
    → Optional Photo Upload
    → RAG Retrieval (ChromaDB + sentence-transformers)
    → Claude API (text + vision)
    → Structured Triage Card (conditions, actions, severity, sources)
    → Vet Alert Button (pre-filled email/SMS if HIGH/CRITICAL)
```

---

## Technical Approach

### Baseline
Keyword search (BM25-style) over the same document corpus — raw retrieved text with no LLM generation. Used for evaluation comparison.

### Our Approach
1. **Ingestion:** Illinois Extension livestock PDFs chunked at 400 tokens (50 overlap) with `RecursiveCharacterTextSplitter`
2. **Embeddings:** `all-MiniLM-L6-v2` via sentence-transformers (free, local)
3. **Vector store:** ChromaDB (local persistence, no cloud account needed)
4. **Retrieval:** Top-4 chunks by cosine similarity at query time
5. **Generation:** Claude claude-sonnet-4 with structured JSON output — handles both text symptoms and uploaded images in one API call
6. **Guardrails:** "Not enough evidence" path, uncertainty notes, severity thresholds before escalation

---

## Run Instructions (Judge Mode)

No API key needed for judge mode.

```bash
# 1. Clone and install
git clone <repo-url>
cd farmguard-ai
pip install -r requirements.txt

# 2. Build vector store (uses synthetic fallback if no PDFs added)
python ingest.py

# 3. Run app
streamlit run app.py

# 4. In the app: toggle "Judge mode" in the sidebar
#    This uses cached demo responses — no Anthropic API key required
```

**To run with live API:**
```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
streamlit run app.py
# Leave "Judge mode" OFF in sidebar
```

**To run evaluation:**
```bash
python eval/run_eval.py
# Results saved to eval/eval_results.json
```

---

## Results

| Metric | RAG System | Keyword Baseline |
|--------|-----------|-----------------|
| Avg keyword coverage | see eval_results.json | see eval_results.json |
| Structured output | ✅ JSON with citations | ❌ Raw text |
| Image analysis | ✅ Multimodal | ❌ Not supported |
| Uncertainty handling | ✅ Explicit | ❌ None |
| Escalation pathway | ✅ Vet alert button | ❌ None |

---

## Constraints and Limitations

- **Image analysis** depends on LLM vision, not a fine-tuned classifier — may miss subtle visual signs
- **Corpus size:** Accuracy improves significantly with more Illinois Extension PDFs added to `data/`
- **Hallucination risk:** Mitigated by RAG citations and explicit uncertainty notes, but not eliminated
- **Connectivity:** Requires internet for Claude API call; judge mode bypasses this
- **Next steps:** Add more species, integrate wearable sensor data streams, fine-tune on ag-specific image dataset

---

## Data Sources
- Illinois Extension livestock publications (public): https://extension.illinois.edu/livestock
- USDA livestock topic pages (public): https://www.usda.gov/topics/farming
- Synthetic fallback entries (clearly labeled in metadata)
