"""
FAISS-backed vector store for document retrieval.

Stores document texts alongside their DistilBERT embeddings.
Supports incremental ingestion, persistence to disk, and top-k retrieval.
"""

import os
import json
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple


class FAISSVectorStore:
    """
    Vector store using FAISS IndexFlatIP (inner product on L2-normalized vectors
    == cosine similarity).

    Args:
        embedding_dim: Size of each embedding vector (768 for DistilBERT base).
        index_path: Directory where the FAISS index and metadata are persisted.
    """

    def __init__(self, embedding_dim: int = 768, index_path: str = "rag_store"):
        self.embedding_dim = embedding_dim
        self.index_path = index_path
        self._faiss_file = os.path.join(index_path, "index.faiss")
        self._meta_file = os.path.join(index_path, "metadata.pkl")

        self.documents: List[Dict[str, Any]] = []  # [{text, metadata, id}]
        self.index = faiss.IndexFlatIP(embedding_dim)  # cosine sim via normalized vectors

        if os.path.exists(self._faiss_file) and os.path.exists(self._meta_file):
            self._load()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def add(self, texts: List[str], embeddings: np.ndarray, metadatas: List[Dict] = None):
        """
        Add documents and their embeddings to the store.

        Args:
            texts: Raw text strings.
            embeddings: L2-normalized embeddings, shape (N, embedding_dim).
            metadatas: Optional list of dicts with extra info per document.
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]

        assert len(texts) == len(embeddings) == len(metadatas), \
            "texts, embeddings, and metadatas must have the same length"

        embeddings = np.array(embeddings, dtype=np.float32)
        self.index.add(embeddings)

        start_id = len(self.documents)
        for i, (text, meta) in enumerate(zip(texts, metadatas)):
            self.documents.append({"id": start_id + i, "text": text, "metadata": meta})

        print(f"[VectorStore] Added {len(texts)} document(s). Total: {len(self.documents)}")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Return the top-k most similar documents for a query embedding.

        Args:
            query_embedding: Shape (1, embedding_dim) or (embedding_dim,).
            top_k: Number of results to return.

        Returns:
            List of dicts: [{id, text, metadata, score}]
        """
        if len(self.documents) == 0:
            return []

        q = np.array(query_embedding, dtype=np.float32)
        if q.ndim == 1:
            q = q[np.newaxis, :]

        k = min(top_k, len(self.documents))
        scores, indices = self.index.search(q, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            doc = dict(self.documents[idx])
            doc["score"] = float(score)
            results.append(doc)

        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self):
        """Persist the FAISS index and document metadata to disk."""
        os.makedirs(self.index_path, exist_ok=True)
        faiss.write_index(self.index, self._faiss_file)
        with open(self._meta_file, "wb") as f:
            pickle.dump(self.documents, f)
        print(f"[VectorStore] Saved {len(self.documents)} documents to {self.index_path}/")

    def _load(self):
        """Load a previously saved index from disk."""
        self.index = faiss.read_index(self._faiss_file)
        with open(self._meta_file, "rb") as f:
            self.documents = pickle.load(f)
        print(f"[VectorStore] Loaded {len(self.documents)} documents from {self.index_path}/")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.documents)

    def clear(self):
        """Remove all documents and reset the index."""
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.documents = []
        print("[VectorStore] Cleared.")
