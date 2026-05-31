"""
DistilBERT-based encoder for generating dense vector embeddings.

Uses the base distilbert-base-uncased model (not the fine-tuned classifier)
to produce neutral semantic embeddings via the [CLS] token hidden state.
"""

import torch
import numpy as np
from transformers import DistilBertModel, DistilBertTokenizer
from typing import List, Union


class DistilBertEncoder:
    """
    Encodes text into fixed-size dense vectors using DistilBERT.
    Extracts the [CLS] token embedding from the last hidden state.

    Args:
        model_name: HuggingFace model ID. Defaults to distilbert-base-uncased.
        device: "cuda", "cpu", or None for auto-detection.
        batch_size: Number of texts to encode in one forward pass.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        device: str = None,
        batch_size: int = 32,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"[Encoder] Loading {model_name} on {self.device}...")
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        self.model = DistilBertModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        print(f"[Encoder] Ready. Embedding dim: {self.model.config.dim}")

    @property
    def embedding_dim(self) -> int:
        return self.model.config.dim  # 768 for distilbert-base-uncased

    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Encode one or more texts into embeddings.

        Args:
            texts: A single string or a list of strings.
            normalize: If True, L2-normalize the output vectors (recommended for cosine similarity).

        Returns:
            np.ndarray of shape (N, embedding_dim) where N = len(texts).
        """
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}

            with torch.no_grad():
                outputs = self.model(**encoded)
                # [CLS] token is at position 0 of the last hidden state
                cls_embeddings = outputs.last_hidden_state[:, 0, :]  # (batch, 768)

            all_embeddings.append(cls_embeddings.cpu().numpy())

        embeddings = np.vstack(all_embeddings).astype(np.float32)

        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)  # avoid division by zero
            embeddings = embeddings / norms

        return embeddings
