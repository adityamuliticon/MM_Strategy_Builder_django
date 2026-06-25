import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store", "faiss_index")


class CommonRetriever:
    """Single shared FAISS index built from all 5 module docs."""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        if os.path.exists(STORE_PATH):
            self._db = FAISS.load_local(
                STORE_PATH, self.embeddings, allow_dangerous_deserialization=True
            )
        else:
            self._db = None

    def get_context(self, query, k=5):
        if not self._db:
            return "No documentation found for this query."
        docs = self._db.similarity_search(query, k=k)
        return "\n\n".join(d.page_content for d in docs)


common_retriever = CommonRetriever()
