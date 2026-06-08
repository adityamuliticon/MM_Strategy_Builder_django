import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

RES_DOC_PATH = "docs/MM - Rapid Execution Scalper.md"
RES_VECTOR_STORE_PATH = "rapid_execution_scalper/rag/store/faiss_index"


def ingest_docs():
    print("Ingesting RES documentation...")

    loader = TextLoader(RES_DOC_PATH)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_store = FAISS.from_documents(chunks, embeddings)
    os.makedirs(os.path.dirname(RES_VECTOR_STORE_PATH), exist_ok=True)
    vector_store.save_local(RES_VECTOR_STORE_PATH)

    print(f"Ingested {len(chunks)} chunks into {RES_VECTOR_STORE_PATH}")


if __name__ == "__main__":
    ingest_docs()
