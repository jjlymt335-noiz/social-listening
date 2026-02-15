import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.classifier import classify_country
from app.models.document import Document
from app.pipeline.analysis import analyze_texts
from app.pipeline.embedding import generate_embeddings
from app.pipeline.text_clean import clean_text, detect_language

logger = logging.getLogger(__name__)


async def ingest_documents(
    raw_docs: list[dict],
    session: AsyncSession,
) -> list[str]:
    """Process and ingest raw documents into the database.

    Each raw_doc should have:
        - text: str (raw text)
        - brand: str
        - platform: str
        - country_code: str (ISO 3166-1 alpha-2)
        - created_at: str | datetime (optional, defaults to now)
        - engagement_count: int (optional, defaults to 0)
        - doc_id: str (optional, auto-generated if missing)

    Returns list of ingested doc_ids.
    """
    if not raw_docs:
        return []

    # Step 1: Clean texts
    cleaned_texts = [clean_text(doc["text"]) for doc in raw_docs]
    brand = raw_docs[0]["brand"]

    # Step 2: Generate embeddings
    embeddings = await generate_embeddings(cleaned_texts)

    # Step 3: Analyze sentiment/topic/aspect
    analyses = await analyze_texts(cleaned_texts, brand)

    # Step 4: Build Document objects and insert
    doc_ids: list[str] = []
    for i, raw in enumerate(raw_docs):
        doc_id = raw.get("doc_id", str(uuid.uuid4()))
        geo = classify_country(raw["country_code"])
        language = detect_language(cleaned_texts[i])

        created_at = raw.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        doc = Document(
            doc_id=doc_id,
            brand=raw["brand"],
            platform=raw["platform"],
            created_at=created_at,
            country_code=geo["country_code"],
            region_group=geo["region_group"],
            language=language,
            text_clean=cleaned_texts[i],
            topic_l1=analyses[i]["topic_l1"],
            aspect=analyses[i]["aspect"],
            sentiment=analyses[i]["sentiment"],
            intensity=analyses[i]["intensity"],
            embedding=embeddings[i],
            engagement_count=raw.get("engagement_count", 0),
        )
        session.add(doc)
        doc_ids.append(doc_id)

    await session.commit()
    logger.info("Ingested %d documents for brand=%s", len(doc_ids), brand)
    return doc_ids
