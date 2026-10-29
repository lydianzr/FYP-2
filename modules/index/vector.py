# modules/index/vector.py
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import Dict, Any, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROMA_PATH = os.path.join(PROJECT_ROOT, "data", "chroma_db")


class VectorIndex:
    """Dense vector index using BAAI/bge-m3 embeddings stored in ChromaDB."""

    def __init__(self, db_path: str = CHROMA_PATH, collection_name: str = "logistics_bge"):
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        # Using BAAI/bge-m3 dense embeddings via SentenceTransformers
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-m3"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        self.collection.upsert(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        n_results = min(top_k, max(1, self.collection.count()))
        results = self.collection.query(query_texts=[query], n_results=n_results)
        
        output = []
        if results and results.get("documents") and results["documents"][0]:
            for doc_text, meta, doc_id, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["ids"][0],
                results["distances"][0]
            ):
                output.append({
                    "id": doc_id,
                    "text": doc_text,
                    "metadata": meta,
                    "score": round(1.0 - float(dist), 4)
                })
        return output