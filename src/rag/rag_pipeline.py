"""
RAG Pipeline: ties together the encoder, vector store, and LLM provider.

Flow:
  Ingest  → chunk text → encode with DistilBERT → store in FAISS
  Query   → encode query → retrieve top-k chunks → build prompt → LLM → answer
"""

import textwrap
from typing import List, Dict, Any, Optional

from .encoder import DistilBertEncoder
from .vector_store import FAISSVectorStore
from .llm_provider import BaseLLMProvider, get_llm_provider


# ---------------------------------------------------------------------------
# Default prompt template
# ---------------------------------------------------------------------------

_DEFAULT_SYSTEM_PROMPT = """\
You are a fact-checking assistant. Use ONLY the provided context passages to answer \
the question. If the context does not contain enough information, say so explicitly \
instead of making things up. Be concise and cite which passage supports your answer.\
"""

_DEFAULT_PROMPT_TEMPLATE = """\
{system_prompt}

--- CONTEXT ---
{context}
--- END CONTEXT ---

Question: {question}

Answer:"""


# ---------------------------------------------------------------------------
# RAGPipeline
# ---------------------------------------------------------------------------

class RAGPipeline:
    """
    Full RAG pipeline for misinformation-aware question answering.

    Args:
        llm_provider:  A BaseLLMProvider instance or provider name string.
        llm_api_key:   API key (used when llm_provider is a string).
        llm_model:     Override model name for the provider.
        encoder_model: HuggingFace model ID for the DistilBERT encoder.
        store_path:    Directory to persist the FAISS vector store.
        top_k:         Number of chunks to retrieve per query.
        chunk_size:    Max words per document chunk during ingestion.
        chunk_overlap: Word overlap between consecutive chunks.
        system_prompt: System instruction prepended to every LLM prompt.
    """

    def __init__(
        self,
        llm_provider: Any = "gemini",
        llm_api_key: str = None,
        llm_model: str = None,
        encoder_model: str = "distilbert-base-uncased",
        store_path: str = "rag_store",
        top_k: int = 5,
        chunk_size: int = 150,
        chunk_overlap: int = 20,
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ):
        # Encoder (DistilBERT)
        self.encoder = DistilBertEncoder(model_name=encoder_model)

        # Vector store (FAISS)
        self.store = FAISSVectorStore(
            embedding_dim=self.encoder.embedding_dim,
            index_path=store_path,
        )

        # LLM provider
        if isinstance(llm_provider, str):
            self.llm = get_llm_provider(
                provider=llm_provider,
                api_key=llm_api_key,
                model=llm_model,
            )
        elif isinstance(llm_provider, BaseLLMProvider):
            self.llm = llm_provider
        else:
            raise TypeError("llm_provider must be a provider name string or a BaseLLMProvider instance.")

        self.top_k = top_k
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.system_prompt = system_prompt

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, texts: List[str], metadatas: List[Dict] = None, auto_save: bool = True):
        """
        Chunk, encode, and store a list of documents.

        Args:
            texts: Raw document strings.
            metadatas: Optional metadata dicts (one per document).
            auto_save: Persist the index after ingestion.

        Returns:
            Number of chunks added.
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]

        all_chunks: List[str] = []
        all_metas: List[Dict] = []

        for doc_idx, (text, meta) in enumerate(zip(texts, metadatas)):
            chunks = self._chunk_text(text)
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metas.append({**meta, "doc_idx": doc_idx, "chunk_idx": chunk_idx})

        if not all_chunks:
            print("[RAG] No chunks produced — nothing ingested.")
            return 0

        embeddings = self.encoder.encode(all_chunks, normalize=True)
        self.store.add(all_chunks, embeddings, all_metas)

        if auto_save:
            self.store.save()

        print(f"[RAG] Ingested {len(texts)} document(s) → {len(all_chunks)} chunk(s).")
        return len(all_chunks)

    def ingest_one(self, text: str, metadata: Dict = None, auto_save: bool = True) -> int:
        """Convenience wrapper for ingesting a single document."""
        return self.ingest([text], [metadata or {}], auto_save=auto_save)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def query(
        self,
        question: str,
        top_k: int = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        return_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant chunks and generate an answer using the LLM.

        Args:
            question: Natural language question.
            top_k: Override the default retrieval count.
            max_tokens: Max tokens for LLM output.
            temperature: LLM sampling temperature.
            return_sources: Include retrieved chunks in the response.

        Returns:
            Dict with keys: answer, sources (if requested), question.
        """
        k = top_k or self.top_k

        # 1. Encode the query
        q_embedding = self.encoder.encode(question, normalize=True)  # (1, 768)

        # 2. Retrieve top-k chunks
        results = self.store.search(q_embedding, top_k=k)

        if not results:
            return {
                "question": question,
                "answer": "No documents have been ingested yet. Please add documents first.",
                "sources": [],
            }

        # 3. Build context string
        context_parts = []
        for i, r in enumerate(results, 1):
            score_pct = round(r["score"] * 100, 1)
            context_parts.append(f"[{i}] (relevance {score_pct}%) {r['text']}")
        context = "\n\n".join(context_parts)

        # 4. Build and send prompt
        prompt = _DEFAULT_PROMPT_TEMPLATE.format(
            system_prompt=self.system_prompt,
            context=context,
            question=question,
        )

        answer = self.llm.generate(prompt, max_tokens=max_tokens, temperature=temperature)

        response: Dict[str, Any] = {"question": question, "answer": answer}
        if return_sources:
            response["sources"] = [
                {
                    "text": r["text"],
                    "score": round(r["score"], 4),
                    "metadata": r.get("metadata", {}),
                }
                for r in results
            ]

        return response

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping word-level chunks.
        Falls back to returning the full text if it's shorter than chunk_size.
        """
        words = text.split()
        if len(words) <= self.chunk_size:
            return [text.strip()]

        chunks = []
        step = self.chunk_size - self.chunk_overlap
        for start in range(0, len(words), step):
            chunk_words = words[start : start + self.chunk_size]
            if chunk_words:
                chunks.append(" ".join(chunk_words))
            if start + self.chunk_size >= len(words):
                break

        return chunks

    def __repr__(self) -> str:
        return (
            f"<RAGPipeline llm={self.llm} "
            f"docs={len(self.store)} "
            f"top_k={self.top_k}>"
        )
