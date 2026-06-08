import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

RES_VECTOR_STORE_PATH = "rapid_execution_scalper/rag/store/faiss_index"


class RESRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        if os.path.exists(RES_VECTOR_STORE_PATH):
            self.vector_store = FAISS.load_local(
                RES_VECTOR_STORE_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            self.vector_store = None

    def retrieve(self, query, k=5):
        if not self.vector_store:
            return []
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def get_context(self, query):
        results = self.retrieve(query)
        if not results:
            return "No RES documentation found for this query."
        return "\n---\n".join(results)


res_retriever = RESRetriever()
