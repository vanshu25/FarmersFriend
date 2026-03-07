# eval/run_eval.py
# Runs a small evaluation comparing RAG triage vs. keyword baseline.
# This is what you show judges to prove your system works.
#
# Usage: python eval/run_eval.py

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_chain import retrieve_context, keyword_baseline

# ── 10 test questions ─────────────────────────────────────────────────────────
# Format: question, expected_keywords (words that should appear in a good answer)

TEST_QUESTIONS = [
    {
        "question": "My cow has labored breathing and nasal discharge for 2 days",
        "animal": "cow",
        "expected_keywords": ["respiratory", "BRD", "temperature", "vet", "separate"],
        "should_escalate": True,
    },
    {
        "question": "Dairy cow with swollen hard udder and bloody milk",
        "animal": "cow",
        "expected_keywords": ["mastitis", "udder", "antibiotic", "isolate", "milk"],
        "should_escalate": True,
    },
    {
        "question": "Cow limping on front leg, foul smell from hoof",
        "animal": "cow",
        "expected_keywords": ["lameness", "foot rot", "hoof", "trim", "copper"],
        "should_escalate": False,
    },
    {
        "question": "Chicken with ruffled feathers, bloody droppings, lethargy",
        "animal": "chicken",
        "expected_keywords": ["coccidiosis", "droppings", "isolate", "medication"],
        "should_escalate": True,
    },
    {
        "question": "Several chickens sneezing, gasping, twisted neck",
        "animal": "chicken",
        "expected_keywords": ["Newcastle", "contagious", "reportable", "vet", "quarantine"],
        "should_escalate": True,
    },
    {
        "question": "Pig vomiting and severe yellow diarrhea, piglets dying",
        "animal": "pig",
        "expected_keywords": ["PED", "diarrhea", "piglets", "electrolytes", "vet"],
        "should_escalate": True,
    },
    {
        "question": "Cow with distended left side, won't eat, kicking at belly",
        "animal": "cow",
        "expected_keywords": ["bloat", "rumen", "gas", "walk", "urgent"],
        "should_escalate": True,
    },
    {
        "question": "Sheep limping badly, bad smell from foot",
        "animal": "sheep",
        "expected_keywords": ["footrot", "hoof", "zinc", "bacteria", "isolate"],
        "should_escalate": False,
    },
    {
        "question": "Cow acting depressed, not eating for 3 days, mild temperature",
        "animal": "cow",
        "expected_keywords": ["infection", "temperature", "separate", "monitor"],
        "should_escalate": True,
    },
    {
        "question": "Chicken stopped laying eggs, losing feathers, seems healthy otherwise",
        "animal": "chicken",
        "expected_keywords": ["molt", "stress", "nutrition", "light", "layer"],
        "should_escalate": False,
    },
]


def keyword_score(text: str, keywords: list[str]) -> float:
    """What fraction of expected keywords appear in the response?"""
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords) if keywords else 0


def run_eval():
    print("=" * 55)
    print("  FarmGuard AI — RAG Evaluation vs. Keyword Baseline")
    print("=" * 55)
    
    rag_scores = []
    baseline_scores = []
    rag_retrieval_counts = []
    
    for i, test in enumerate(TEST_QUESTIONS, 1):
        q = test["question"]
        expected = test["expected_keywords"]
        
        # RAG: retrieve context
        chunks, sources = retrieve_context(q)
        rag_text = " ".join(chunks)
        rag_score = keyword_score(rag_text, expected)
        rag_scores.append(rag_score)
        rag_retrieval_counts.append(len(chunks))
        
        # Baseline: keyword search (just the raw chunks, no LLM)
        baseline_text = keyword_baseline(q)
        baseline_score = keyword_score(baseline_text, expected)
        baseline_scores.append(baseline_score)
        
        # Print result
        delta = rag_score - baseline_score
        delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
        print(f"\n[{i:02d}] {q[:55]}...")
        print(f"     RAG score:      {rag_score:.2f}  ({len(chunks)} chunks, sources: {', '.join(sources[:2]) or 'none'})")
        print(f"     Baseline score: {baseline_score:.2f}")
        print(f"     Delta:          {delta_str}")
    
    # Summary
    avg_rag = sum(rag_scores) / len(rag_scores)
    avg_baseline = sum(baseline_scores) / len(baseline_scores)
    avg_chunks = sum(rag_retrieval_counts) / len(rag_retrieval_counts)
    
    print("\n" + "=" * 55)
    print("  SUMMARY")
    print("=" * 55)
    print(f"  Avg RAG keyword coverage:      {avg_rag:.2f} ({avg_rag*100:.0f}%)")
    print(f"  Avg Baseline keyword coverage: {avg_baseline:.2f} ({avg_baseline*100:.0f}%)")
    print(f"  Avg chunks retrieved per query: {avg_chunks:.1f}")
    print(f"  RAG improvement over baseline: {(avg_rag - avg_baseline)*100:+.0f} percentage points")
    print("=" * 55)
    
    # Save results to JSON
    results = {
        "summary": {
            "avg_rag_score": round(avg_rag, 3),
            "avg_baseline_score": round(avg_baseline, 3),
            "improvement": round(avg_rag - avg_baseline, 3),
            "n_questions": len(TEST_QUESTIONS),
        },
        "per_question": [
            {
                "question": t["question"],
                "rag_score": round(rag_scores[i], 3),
                "baseline_score": round(baseline_scores[i], 3),
                "retrieved_chunks": rag_retrieval_counts[i],
            }
            for i, t in enumerate(TEST_QUESTIONS)
        ]
    }
    
    out_path = Path(__file__).parent / "eval_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n  Results saved to: {out_path}")
    print("\n  ✅ Include eval_results.json in your README for judges.")


if __name__ == "__main__":
    run_eval()
