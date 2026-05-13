from sentence_transformers import SentenceTransformer
import chromadb
import json
import os
from glob import glob

# Configuration
DB_PATH = "./whatsapp-bot/chroma_db"
MOCK_DATA_PATH = "whatsapp-bot/data/mock/**/*.json"
MODEL_NAME = 'all-MiniLM-L6-v2'

def build_rag():
    print(f"Initializing ChromaDB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection("conversations")

    print(f"Loading embedding model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # Find all mock conversation files
    files = glob(MOCK_DATA_PATH, recursive=True)
    print(f"Found {len(files)} mock conversation files.")

    for filepath in files:
        # Skip metadata files if they are not .json
        if not filepath.endswith(".json"):
            continue
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                conversation = json.load(f)
            
            # Create a summary for embedding (first 4 turns)
            summary = " ".join([m["content"] for m in conversation[:4]])
            embedding = model.encode(summary).tolist()
            
            # Use filepath as ID
            file_id = os.path.basename(filepath)
            
            print(f"Adding {file_id} to vector store...")
            collection.add(
                ids=[file_id],
                embeddings=[embedding],
                documents=[json.dumps(conversation)],
                metadatas=[{"source": filepath}]
            )
        except Exception as e:
            print(f"Failed to process {filepath}: {e}")

    print("RAG Vector Store built successfully!")

if __name__ == "__main__":
    build_rag()
