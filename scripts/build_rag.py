from sentence_transformers import SentenceTransformer
import chromadb
import json
import os
from glob import glob

# Configuration
DB_PATH = "./chroma_db"
MOCK_DATA_PATH = "data/mock/**/*.json"
REAL_DATA_PATH = "data/real/**/*.json"
MODEL_NAME = 'all-MiniLM-L6-v2'

def build_rag():
    print(f"Initializing ChromaDB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection("conversations")

    print(f"Loading embedding model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # Find all mock conversation files
    files = glob(MOCK_DATA_PATH, recursive=True)
    # To include real production data, uncomment the following line and adjust as needed
    # real_files = glob(REAL_DATA_PATH, recursive=True)
    # files += real_files
    if 'real_files' in locals():
        print(f"Found {len(files)} mock + real conversation files.")
    else:
        print(f"Found {len(files)} mock conversation files.")

    for filepath in files:
        # Skip metadata files if they are not .json
        if not filepath.endswith(".json"):
            continue
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                conversation = json.load(f)
            
            # Normalize supported conversation structures
            def get_messages(conv):
                if isinstance(conv, list):
                    return conv
                if isinstance(conv, dict):
                    if isinstance(conv.get("messages"), list):
                        return conv["messages"]
                    if isinstance(conv.get("conversation"), list):
                        return conv["conversation"]
                raise ValueError("Unsupported conversation structure")

            def get_text(msg):
                if isinstance(msg, str):
                    return msg
                if not isinstance(msg, dict):
                    return ""
                for field in ("content", "text", "message", "body"):
                    value = msg.get(field)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                return ""

            messages = get_messages(conversation)
            summary = " ".join([get_text(m) for m in messages[:4] if get_text(m)])
            if not summary:
                raise ValueError("No text found in conversation messages")

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
