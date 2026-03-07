# rag_chain.py
# Core RAG pipeline:
#   1. Load ChromaDB vectorstore
#   2. Retrieve top-k relevant chunks based on symptom query
#   3. Call Claude API with retrieved context + optional image
#   4. Parse and return structured triage JSON

import os
import json
import base64
from pathlib import Path
from typing import Optional

import anthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── Config ────────────────────────────────────────────────────────────────────

CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "farmguard_livestock"
EMBED_MODEL = "all-MiniLM-L6-v2"
RETRIEVAL_K = 4          # number of doc chunks to retrieve
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are FarmGuard, an AI livestock health assistant designed for farmers.
Your job is to provide evidence-backed triage recommendations based on retrieved veterinary 
and agricultural extension knowledge.

Critical rules:
- ALWAYS cite the sources you used (from the context provided)
- NEVER give a single definitive diagnosis — always present 2-3 possible conditions ranked by likelihood
- If confidence is LOW or evidence is insufficient, say so explicitly
- Recommend calling a vet for any HIGH or CRITICAL severity
- Keep language simple and farmer-friendly — avoid medical jargon
- If the image shows something that contradicts the described symptoms, note the discrepancy
"""

# ── User prompt template ──────────────────────────────────────────────────────

def build_user_prompt(symptom_summary: str, context_chunks: list[str]) -> str:
    context_text = "\n\n---\n\n".join(context_chunks) if context_chunks else "No specific documents retrieved."
    
    return f"""A farmer has reported the following about their livestock:

{symptom_summary}

---
RETRIEVED KNOWLEDGE FROM AGRICULTURAL EXTENSION DOCUMENTS:
{context_text}
---

Based on the reported symptoms and the retrieved knowledge above, provide a triage assessment.

Respond ONLY with a valid JSON object — no preamble, no markdown, no explanation outside the JSON.
Use exactly this structure:

{{
  "likely_conditions": [
    {{"name": "Condition Name", "confidence": "HIGH", "explanation": "Brief reason"}}
  ],
  "immediate_actions": [
    "Action 1 the farmer should take right now",
    "Action 2"
  ],
  "severity": "LOW",
  "escalate_to_vet": false,
  "vet_summary": "One paragraph summary a farmer could send to their vet describing the situation",
  "cited_sources": ["Source 1", "Source 2"],
  "uncertainty_note": "What we don't know or why confidence is limited",
  "image_observations": "What was observed in the uploaded photo, or 'No image provided'"
}}

Severity scale: LOW (monitor at home), MEDIUM (act today), HIGH (call vet today), CRITICAL (emergency vet now)
"""

# ── Load vectorstore ──────────────────────────────────────────────────────────

_vectorstore = None  # module-level cache so we don't reload on every call

def get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            "ChromaDB not found. Run: python ingest.py"
        )
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    
    _vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    return _vectorstore


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_context(query: str) -> tuple[list[str], list[str]]:
    """
    Retrieve top-k relevant chunks from ChromaDB.
    Returns (chunk_texts, source_names)
    """
    try:
        vs = get_vectorstore()
        results = vs.similarity_search_with_score(query, k=RETRIEVAL_K)
        
        chunks = []
        sources = []
        for doc, score in results:
            if score < 1.5:  # cosine distance threshold — skip irrelevant chunks
                chunks.append(doc.page_content)
                source = doc.metadata.get("source", "Unknown source")
                # Clean up path to just filename
                source = Path(source).name if "/" in source or "\\" in source else source
                if source not in sources:
                    sources.append(source)
        
        return chunks, sources
    
    except Exception as e:
        print(f"⚠️  Retrieval error: {e}")
        return [], []


# ── Image encoding ────────────────────────────────────────────────────────────

def encode_image(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Encode image bytes to base64 for Claude API."""
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": b64,
        }
    }


# ── Main triage call ──────────────────────────────────────────────────────────

def run_triage(
    symptom_summary: str,
    image_bytes: Optional[bytes] = None,
    image_media_type: str = "image/jpeg",
) -> dict:
    """
    Main entry point. Takes formatted symptom text + optional image bytes.
    Returns a parsed triage dict.
    """
    # 1. Retrieve relevant context
    chunks, sources = retrieve_context(symptom_summary)
    
    # 2. Build prompt
    user_prompt_text = build_user_prompt(symptom_summary, chunks)
    
    # 3. Build message content (text + optional image)
    content = []
    
    if image_bytes:
        content.append(encode_image(image_bytes, image_media_type))
        content.append({
            "type": "text",
            "text": user_prompt_text + "\n\nNote: An image has been provided above. Include your observations in the 'image_observations' field."
        })
    else:
        content.append({"type": "text", "text": user_prompt_text})
    
    # 4. Call Claude API
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set.")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    
    raw_text = response.content[0].text.strip()
    
    # 5. Parse JSON response
    try:
        # Strip markdown code fences if model wraps response
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        triage = json.loads(raw_text)
        
        # Inject retrieved sources if model didn't cite any
        if not triage.get("cited_sources"):
            triage["cited_sources"] = sources if sources else ["No sources retrieved"]
        
        return triage
    
    except json.JSONDecodeError:
        # Graceful fallback if JSON parsing fails
        return {
            "likely_conditions": [{"name": "Unable to parse", "confidence": "LOW", "explanation": raw_text[:300]}],
            "immediate_actions": ["Please consult your veterinarian directly."],
            "severity": "MEDIUM",
            "escalate_to_vet": True,
            "vet_summary": raw_text[:500],
            "cited_sources": sources,
            "uncertainty_note": "Response parsing failed — showing raw output.",
            "image_observations": "N/A"
        }


# ── Keyword baseline (for RAGAS eval comparison) ─────────────────────────────

def keyword_baseline(query: str) -> str:
    """
    Simple keyword search baseline — used in eval to compare against RAG.
    Returns concatenated raw chunks without any LLM generation.
    """
    chunks, sources = retrieve_context(query)
    if not chunks:
        return "No relevant documents found for keyword search."
    return f"[Keyword baseline — raw retrieved text]\n\n" + "\n---\n".join(chunks[:2])
