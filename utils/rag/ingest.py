"""
Build the shared FAISS index for all 5 modules.

Run:
    python utils/rag/ingest.py
"""
import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store", "faiss_index")

DOCS = [
    "docs/MM - Unified Strategy Builder Plugin.md",
    "docs/MM - Multi-Leg Hedger.md",
    "docs/MM - Rapid Execution Scalper.md",
    "docs/MM - Inbound Signal Bridge.md",
    "docs/MM - Indicator Signal Engine.md",
]


def ingest():
    splitter   = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    all_chunks = []

    for rel_path in DOCS:
        full_path = os.path.join(BASE_DIR, rel_path)
        if not os.path.exists(full_path):
            print(f"[CommonRAG] SKIP — not found: {rel_path}")
            continue
        docs   = TextLoader(full_path, encoding="utf-8").load()
        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)
        print(f"[CommonRAG] {os.path.basename(rel_path):<45}  {len(chunks):>3} chunks")

    if not all_chunks:
        print("[CommonRAG] No documents found — index not built.")
        return

    print(f"\n[CommonRAG] Building FAISS index from {len(all_chunks)} total chunks...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = FAISS.from_documents(all_chunks, embeddings)
    os.makedirs(STORE_PATH, exist_ok=True)
    db.save_local(STORE_PATH)
    print(f"[CommonRAG] Saved → {STORE_PATH}")


if __name__ == "__main__":
    ingest()
