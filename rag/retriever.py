from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import Config
import os

class StrategyRetriever:
    """
    The StrategyRetriever uses semantic search to fetch relevant documentation 
    context from the local FAISS vector store.
    """
    def __init__(self):
        # Initialize the embedding model (all-MiniLM-L6-v2 is fast and lightweight)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Check if the vector store index already exists
        if os.path.exists(Config.VECTOR_STORE_PATH):
            # Load the index from the local filesystem
            self.vector_store = FAISS.load_local(
                Config.VECTOR_STORE_PATH, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            self.vector_store = None

    def retrieve(self, query, k=5):
        """
        Performs a similarity search on the vector store.
        Returns the top 'k' most relevant documentation snippets.
        """
        if not self.vector_store:
            return []
        
        # Search the index for documents matching the user's query
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def get_context(self, query):
        """
        Returns a formatted string containing retrieved context 
        to be injected into the AI's prompt.
        """
        results = self.retrieve(query)
        if not results:
            return "No documentation found for this query."
        return "\n---\n".join(results)

# Singleton instance
retriever = StrategyRetriever()
