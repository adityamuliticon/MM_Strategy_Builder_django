import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import Config

def ingest_docs():
    print("Ingesting documentation...")
    
    # Load all markdown files
    loader = DirectoryLoader(Config.DOCS_PATH, glob="**/*.md", loader_cls=TextLoader)
    documents = loader.load()
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    # Use a lightweight embedding model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create and save the vector store
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(Config.VECTOR_STORE_PATH)
    
    print(f"Ingested {len(chunks)} chunks into {Config.VECTOR_STORE_PATH}")

if __name__ == "__main__":
    ingest_docs()
