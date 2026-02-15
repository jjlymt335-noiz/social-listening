import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Gemini text-embedding-004 batchEmbedContents API."""
    client = _get_client()
    all_embeddings: list[list[float]] = []
    url = (
        f"{settings.GEMINI_BASE_URL}/models/{settings.GEMINI_EMBEDDING_MODEL}"
        f":batchEmbedContents?key={settings.GEMINI_API_KEY}"
    )

    for i in range(0, len(texts), settings.EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + settings.EMBEDDING_BATCH_SIZE]
        requests_body = [
            {
                "model": f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                "content": {"parts": [{"text": t}]},
            }
            for t in batch
        ]

        try:
            response = await client.post(url, json={"requests": requests_body})
            response.raise_for_status()
            data = response.json()

            for emb in data["embeddings"]:
                all_embeddings.append(emb["values"])
        except Exception:
            logger.exception("Failed to generate embeddings for batch %d", i)
            raise

    return all_embeddings


async def generate_single_embedding(text: str) -> list[float]:
    """Generate embedding for a single text."""
    client = _get_client()
    url = (
        f"{settings.GEMINI_BASE_URL}/models/{settings.GEMINI_EMBEDDING_MODEL}"
        f":embedContent?key={settings.GEMINI_API_KEY}"
    )

    response = await client.post(
        url,
        json={
            "model": f"models/{settings.GEMINI_EMBEDDING_MODEL}",
            "content": {"parts": [{"text": text}]},
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["embedding"]["values"]
