# ingest.py
# Run this ONCE before launching the app.
# It loads PDFs from data/, chunks them, embeds with sentence-transformers,
# and stores everything in a local ChromaDB collection.
#
# Usage:
#   python ingest.py
#
# Expected folder structure:
#   data/
#     illinois_extension/   ← put your downloaded PDFs here
#     usda_pages/           ← optional: .txt files from USDA pages

import os
import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR = Path("data")
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "farmguard_livestock"

CHUNK_SIZE = 400        # tokens per chunk (good balance for ag docs)
CHUNK_OVERLAP = 50      # overlap to preserve context across chunks
EMBED_MODEL = "all-MiniLM-L6-v2"   # free, local, fast

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_documents():
    """Load all PDFs and .txt files from the data directory."""
    docs = []
    
    # Load PDFs from all subdirectories
    pdf_dirs = list(DATA_DIR.rglob("*.pdf"))
    if not pdf_dirs:
        print("No PDF files found in data/. Add Illinois Extension PDFs there.")
        print("    Download from: https://extension.illinois.edu/livestock")
    else:
        for pdf_path in pdf_dirs:
            print(f"  Loading: {pdf_path.name}")
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs.extend(loader.load())
            except Exception as e:
                print(f"   Skipping {pdf_path.name}: {e}")
    
    # Load .txt files (e.g. scraped USDA pages)
    txt_files = list(DATA_DIR.rglob("*.txt"))
    for txt_path in txt_files:
        print(f"  Loading: {txt_path.name}")
        try:
            loader = TextLoader(str(txt_path), encoding="utf-8")
            docs.extend(loader.load())
        except Exception as e:
            print(f"  Skipping {txt_path.name}: {e}")
    
    return docs


def chunk_documents(docs):
    """Split docs into chunks suitable for retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],  # respect paragraph breaks
    )
    chunks = splitter.split_documents(docs)
    print(f"\n Created {len(chunks)} chunks from {len(docs)} pages")
    return chunks


def build_vectorstore(chunks):
    """Embed chunks and store in ChromaDB."""
    print(f"\n  Loading embedding model: {EMBED_MODEL}")
    print("     (First run downloads ~90MB — subsequent runs use cache)")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    
    print(f"  Building ChromaDB at: {CHROMA_DIR}/")
    
    # Wipe existing collection if reingest
    if CHROMA_DIR.exists():
        import shutil
        shutil.rmtree(CHROMA_DIR)
        print("  Cleared existing ChromaDB (fresh ingest)")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )
    
    vectorstore.persist()
    return vectorstore


def add_synthetic_fallback(vectorstore):
    """
    Add a small set of synthetic livestock health facts as fallback.
    This ensures the RAG pipeline works even before real PDFs are added.
    These are based on common extension knowledge — clearly labeled as synthetic.
    """
    from langchain_core.documents import Document
    
    synthetic_docs = [
        Document(
            page_content=(
                "Bovine Respiratory Disease (BRD) in cattle is one of the most common and costly diseases. "
                "Signs include nasal discharge, labored breathing, fever above 104°F, depression, and reduced appetite. "
                "Immediate action: separate the animal, check temperature, consult a vet if multiple animals affected."
            ),
            metadata={"source": "synthetic_fallback", "animal": "cow", "topic": "respiratory"}
        ),
        Document(
            page_content=(
                "Mastitis in dairy cows is inflammation of the udder, often caused by bacterial infection. "
                "Signs: swollen or hard udder, abnormal milk (clumps, blood, watery), drop in milk production, cow may kick when milked. "
                "Action: isolate cow, do California Mastitis Test (CMT) if available, contact vet for antibiotic treatment."
            ),
            metadata={"source": "synthetic_fallback", "animal": "cow", "topic": "mastitis"}
        ),
        Document(
            page_content=(
                "Lameness in cattle is commonly caused by foot rot, sole ulcers, or white line disease. "
                "Signs: limping, reluctance to bear weight, swelling between toes, foul smell. "
                "Action: clean the hoof, trim if possible, copper sulfate foot bath, consult vet for severe cases."
            ),
            metadata={"source": "synthetic_fallback", "animal": "cow", "topic": "lameness"}
        ),
        Document(
            page_content=(
                "Newcastle Disease in poultry is a highly contagious viral disease. "
                "Signs: sudden death, gasping, nasal discharge, green diarrhea, paralysis of wings or legs, twisted neck. "
                "CRITICAL: Newcastle is a reportable disease. Contact your vet and state animal health official immediately."
            ),
            metadata={"source": "synthetic_fallback", "animal": "chicken", "topic": "newcastle"}
        ),
        Document(
            page_content=(
                "Coccidiosis is a common intestinal disease in chickens, especially young birds. "
                "Signs: bloody or watery diarrhea, lethargy, ruffled feathers, pale comb, reduced feed intake. "
                "Action: treat with coccidiostat medication in water, improve sanitation, isolate sick birds."
            ),
            metadata={"source": "synthetic_fallback", "animal": "chicken", "topic": "coccidiosis"}
        ),
        Document(
            page_content=(
                "Porcine Epidemic Diarrhea (PED) spreads rapidly in swine herds. "
                "Signs: profuse watery diarrhea (often yellow), vomiting, rapid weight loss, high mortality in piglets. "
                "Action: isolate affected pigs, provide electrolytes, contact vet immediately — mortality in young pigs can be near 100%."
            ),
            metadata={"source": "synthetic_fallback", "animal": "pig", "topic": "ped"}
        ),
        Document(
            page_content=(
                "Foot rot (Footrot) in sheep is a contagious disease caused by bacteria infecting the hoof. "
                "Signs: severe lameness, foul smell from affected foot, separation of hoof horn, reluctance to walk. "
                "Action: trim hoof, zinc sulfate foot bath, penicillin injection for severe cases, isolate affected animals."
            ),
            metadata={"source": "synthetic_fallback", "animal": "sheep", "topic": "footrot"}
        ),
        Document(
            page_content=(
                "Bloat in cattle and sheep is accumulation of gas in the rumen that cannot be released. "
                "Signs: distended left side of abdomen, labored breathing, animal appears distressed, kicking at belly. "
                "URGENT: walk the animal, do not let it lie down. Call vet immediately — severe bloat can be fatal within hours."
            ),
            metadata={"source": "synthetic_fallback", "animal": "cow/sheep", "topic": "bloat"}
        ),
    ]
    
    vectorstore.add_documents(synthetic_docs)
    vectorstore.persist()
    print(f"  Added {len(synthetic_docs)} synthetic fallback entries")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("🌾 FarmGuard AI — Document Ingestion")
    print("=" * 45)
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "illinois_extension").mkdir(exist_ok=True)
    (DATA_DIR / "usda_pages").mkdir(exist_ok=True)
    
    print(f"\nLoading documents from: {DATA_DIR}/")
    docs = load_documents()
    
    if docs:
        print(f"\nChunking {len(docs)} pages...")
        chunks = chunk_documents(docs)
        print(f"\nBuilding vector store...")
        vectorstore = build_vectorstore(chunks)
        add_synthetic_fallback(vectorstore)
    else:
        print("\nNo real docs found — building with synthetic fallback data only.")
        print("    This is enough to demo! Add real PDFs later for better accuracy.\n")
        # Build empty vectorstore then add fallback
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR),
        )
        add_synthetic_fallback(vectorstore)
    
    # Verify
    count = vectorstore._collection.count()
    print(f"\nDone! ChromaDB contains {count} vectors at: {CHROMA_DIR}/")
    print("\nNext step: run the app with:")
    print("  streamlit run app.py")


if __name__ == "__main__":
    main()
