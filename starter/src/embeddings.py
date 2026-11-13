"""Choose a real embedding provider (API or local) and implement this contract."""
import os
from typing import Protocol

from sentence_transformers import SentenceTransformer


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Local sentence-transformer adapter for a real embedding model."""

    def __init__(self, model_name: str | None = None) -> None:
        env_model = os.getenv("EMBEDDING_MODEL")
        self.model_name = model_name or env_model or "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.model_name, device="cpu")
        dimension_fn = getattr(self.model, "get_embedding_dimension", None)
        if dimension_fn is None:
            dimension_fn = getattr(self.model, "get_sentence_embedding_dimension", None)
        if dimension_fn is None:
            raise AttributeError("SentenceTransformer model does not expose embedding dimension metadata.")
        self.dimensions = int(dimension_fn())

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
        return [list(map(float, vector)) for vector in vectors]

    def embed_query(self, question: str) -> list[float]:
        vectors = self.model.encode([question], convert_to_numpy=True, normalize_embeddings=False)
        return [float(x) for x in vectors[0]]
