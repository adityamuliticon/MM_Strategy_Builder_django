import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

INDEX_PATH = "multi_leg_hedger/rag/store/faiss_index"


class MLHRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        if os.path.exists(INDEX_PATH):
            self._db = FAISS.load_local(INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True)
        else:
            self._db = None

    def get_context(self, query, k=5):
        if not self._db:
            return ""
        docs = self._db.similarity_search(query, k=k)
        return "\n\n".join(d.page_content for d in docs)


mlh_retriever = MLHRetriever()
