import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORE_PATH = os.path.join(BASE_DIR, "inbound_signal_bridge", "rag", "store", "faiss_index")


class ISBRetriever:
    def __init__(self):
        self.retriever = None
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vectorstore = FAISS.load_local(
                STORE_PATH, embeddings, allow_dangerous_deserialization=True
            )
            self.retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        except Exception as e:
            print(f"[ISBRetriever] FAISS index not loaded: {e}")

    def get_context(self, query):
        if not self.retriever:
            return "No ISB documentation found for this query."
        docs = self.retriever.invoke(query)
        return "\n\n".join(doc.page_content for doc in docs)


isb_retriever = ISBRetriever()
