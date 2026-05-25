"""
Run once to build the ISB FAISS index:
    python -c "from inbound_signal_bridge.rag.ingest import ingest; ingest()"
Or just run:
    python inbound_signal_bridge/rag/ingest.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

MD_FILE = os.path.join(BASE_DIR, "MM - Inbound Signal Bridge.md")
STORE_PATH = os.path.join(BASE_DIR, "inbound_signal_bridge", "rag", "store", "faiss_index")


def ingest():
    loader = TextLoader(MD_FILE, encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(STORE_PATH)

    print(f"Ingested {len(chunks)} chunks into {STORE_PATH}")


if __name__ == "__main__":
    ingest()
