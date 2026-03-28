import json
import os
import chromadb
from chromadb.utils import embedding_functions

POLICY_DIR = "data/policies"

class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Initialize sentence-transformers embedding
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="climate_policies",
            embedding_function=self.embedding_fn
        )
        self._ingest_data()

    def _ingest_data(self):
        # Ingest only if collection is empty
        if self.collection.count() > 0:
            return

        print("Ingesting policy data into ChromaDB...")
        if not os.path.exists(POLICY_DIR):
            return

        for filename in os.listdir(POLICY_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(POLICY_DIR, filename)
                with open(filepath, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        continue
                
                country = data.get("country")
                if not country:
                    continue

                chunks = []
                metadatas = []
                ids = []

                # Add key positions
                for i, text in enumerate(data.get("key_positions", [])):
                    chunks.append(text)
                    metadatas.append({"country": country, "type": "key_position"})
                    ids.append(f"{country}_pos_{i}")
                
                # Add red lines
                for i, text in enumerate(data.get("red_lines", [])):
                    chunks.append(text)
                    metadatas.append({"country": country, "type": "red_line"})
                    ids.append(f"{country}_red_{i}")

                if chunks:
                    self.collection.add(
                        documents=chunks,
                        metadatas=metadatas,
                        ids=ids
                    )
        print("Data ingestion complete.")

    def get_context(self, query: str, country: str, top_k: int = 2) -> str:
        # Add basic try-except
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"country": country}
            )
            if not results['documents'] or len(results['documents']) == 0 or not results['documents'][0]:
                return "No specific policy points found."
            
            # Combine the chunks into a single context string
            return " ".join(results['documents'][0])
        except Exception:
            return "No specific policy points found."

# Instantiate as singleton
rag_service = RAGService()
