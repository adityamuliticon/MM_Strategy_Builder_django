import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

SOURCE = "docs/MM - Multi-Leg Hedger.md"
INDEX_PATH = "multi_leg_hedger/rag/store/faiss_index"


def ingest():
    loader = TextLoader(SOURCE)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(chunks, embeddings)
    os.makedirs(INDEX_PATH, exist_ok=True)
    db.save_local(INDEX_PATH)
    print(f"[MLH RAG] Ingested {len(chunks)} chunks -> {INDEX_PATH}")


if __name__ == "__main__":
    ingest()
