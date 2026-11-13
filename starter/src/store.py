"""Store and search vectors using PostgreSQL + pgvector."""
import json
from typing import Any

import psycopg

from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        """Retain connection settings and validate the embedding dimension."""
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive.")
        self.database_url = database_url
        self.dimensions = dimensions
        self.conn = psycopg.connect(database_url)

    def create_schema(self) -> None:
        """Create the vector table and metadata columns used for search."""
        with self.conn.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute("DROP TABLE IF EXISTS retrieval_chunks")
            cursor.execute(
                f"""
                CREATE TABLE retrieval_chunks (
                    strategy TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    chapter TEXT,
                    title TEXT,
                    text TEXT NOT NULL,
                    metadata_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding VECTOR({self.dimensions}),
                    PRIMARY KEY (strategy, chunk_id)
                )
                """
            )
        self.conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Validate dimensions and upsert chunk vectors per strategy."""
        if len(chunks) != len(vectors):
            raise ValueError("Chunk count and vector count must match.")

        self.create_schema()
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM retrieval_chunks WHERE strategy = %s", [strategy])
            for chunk, vector in zip(chunks, vectors):
                if len(vector) != self.dimensions:
                    raise ValueError(
                        f"Vector length mismatch for {chunk.chunk_id}: expected {self.dimensions}, got {len(vector)}"
                    )
                payload = {
                    "source": chunk.source,
                    "page": chunk.page,
                    "document_id": chunk.document_id,
                    **chunk.metadata,
                }
                cursor.execute(
                    """
                    INSERT INTO retrieval_chunks (
                        strategy, chunk_id, document_id, source, page, chapter, title, text, metadata_json, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        strategy,
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.source,
                        chunk.page,
                        payload.get("chapter"),
                        payload.get("title"),
                        chunk.text,
                        json.dumps(payload),
                        vector,
                    ],
                )
        self.conn.commit()

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Filter metadata in SQL and return the most relevant chunks."""
        if not query_vector:
            raise ValueError("Query vector cannot be empty.")

        filters = filters or {}
        allowed = {"document_id", "source", "page", "chapter", "title"}
        sql = """
            SELECT chunk_id, document_id, source, page, chapter, title, text, metadata_json,
                   1.0 - (embedding <=> %s::vector) AS score
            FROM retrieval_chunks
            WHERE strategy = %s
        """
        params: list[Any] = [query_vector, strategy]

        for key, value in filters.items():
            if key in allowed:
                sql += f" AND {key} = %s"
                params.append(value)

        sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_vector, top_k])

        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            chunk_id, document_id, source, page, chapter, title, text, metadata_json, score = row
            metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else dict(metadata_json or {})
            results.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "source": source,
                    "page": page,
                    "chapter": chapter,
                    "title": title,
                    "text": text,
                    "metadata": metadata,
                    "score": float(score),
                }
            )
        return results
