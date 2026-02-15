import json
import logging
from typing import TypedDict

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client


class AnalysisResult(TypedDict):
    topic_l1: str
    aspect: str
    sentiment: str  # pos / neu / neg
    intensity: int  # 1-5


_SYSTEM_PROMPT = """You are a social media analyst. Analyze each post and extract structured information.
Return a JSON array where each element has:
- topic_l1: top-level topic (e.g., "flight", "hotel", "customer_service", "app", "policy", "pricing")
- aspect: specific aspect (e.g., "delay", "cancellation", "refund", "bug", "booking", "check_in")
- sentiment: exactly one of "pos", "neu", "neg"
- intensity: integer 1-5 (1=very mild, 5=very strong)

Return ONLY a JSON object like {"results": [...]}, no other text."""


async def analyze_texts(texts: list[str], brand: str) -> list[AnalysisResult]:
    """Analyze a batch of texts for sentiment, topic, and aspect using Gemini."""
    client = _get_client()
    all_results: list[AnalysisResult] = []
    url = (
        f"{settings.GEMINI_BASE_URL}/models/{settings.GEMINI_CHAT_MODEL}"
        f":generateContent?key={settings.GEMINI_API_KEY}"
    )

    for i in range(0, len(texts), settings.ANALYSIS_BATCH_SIZE):
        batch = texts[i : i + settings.ANALYSIS_BATCH_SIZE]
        numbered = "\n".join(f"[{j+1}] {t}" for j, t in enumerate(batch))

        prompt = f"{_SYSTEM_PROMPT}\n\nBrand: {brand}\n\nPosts:\n{numbered}"

        try:
            response = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0,
                        "maxOutputTokens": 2048,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            text_content = data["candidates"][0]["content"]["parts"][0]["text"]

            # Extract JSON (may be wrapped in ```json...```)
            json_match = text_content
            if "```" in text_content:
                import re
                m = re.search(r"\{[\s\S]*\}", text_content)
                if m:
                    json_match = m.group(0)

            parsed = json.loads(json_match)

            # Handle both {"results": [...]} and [...] formats
            if isinstance(parsed, dict):
                items = parsed.get("results", parsed.get("data", []))
            else:
                items = parsed

            for item in items:
                all_results.append(
                    AnalysisResult(
                        topic_l1=item.get("topic_l1", "unknown"),
                        aspect=item.get("aspect", "unknown"),
                        sentiment=item.get("sentiment", "neu"),
                        intensity=max(1, min(5, int(item.get("intensity", 3)))),
                    )
                )
        except Exception:
            logger.exception("Failed to analyze batch %d", i)
            for _ in batch:
                all_results.append(
                    AnalysisResult(topic_l1="unknown", aspect="unknown", sentiment="neu", intensity=3)
                )

    return all_results
