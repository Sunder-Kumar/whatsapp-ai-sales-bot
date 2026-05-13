import chromadb
from sentence_transformers import SentenceTransformer
import os
import json

class RAGManager:
    def __init__(self, db_path: str = "./whatsapp-bot/chroma_db", model_name: str = 'all-MiniLM-L6-v2'):
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.client = None
        self.collection = None

    def _initialize(self):
        """Initializes the embedding model and ChromaDB client."""
        if self.model is None:
            print(f"Loading embedding model ({self.model_name})...")
            self.model = SentenceTransformer(self.model_name)
        
        if self.client is None:
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection("conversations")

    def query_similar_conversations(self, current_message: str, n_results: int = 2):
        """
        Finds the most similar past conversations from ChromaDB.
        """
        self._initialize()
        
        try:
            query_embedding = self.model.encode(current_message).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # The documents are stored as JSON strings
            examples = results.get("documents", [[]])[0]
            return [json.loads(ex) for ex in examples]
        except Exception as e:
            print(f"RAG Query Error: {e}")
            return []

# Global instance
rag_manager = RAGManager()
