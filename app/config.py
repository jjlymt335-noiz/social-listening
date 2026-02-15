import os

from pydantic_settings import BaseSettings

# Vercel serverless: only /tmp is writable
if os.environ.get("VERCEL"):
    _db_path = "/tmp/social_listening.db"
else:
    _db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "social_listening.db")


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database (SQLite)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_db_path}"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-2.0-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    EMBEDDING_DIMENSIONS: int = 768
    EMBEDDING_BATCH_SIZE: int = 100  # Gemini batchEmbedContents limit
    ANALYSIS_BATCH_SIZE: int = 15

    # Short-Term Engine
    SCAN_INTERVAL_MINUTES: int = 30
    SHORT_TERM_AGG_WINDOW_HOURS: int = 6
    EVENT_LIFECYCLE_HOURS: int = 12
    EVENT_COOLING_THRESHOLD_HOURS: float = 1.5

    # Long-Term Engine
    LONG_TERM_WINDOW_MAX_DAYS: int = 30

    # Clustering
    EMBEDDING_SIM_THRESHOLD: float = 0.85
    MIN_CLUSTER_SIZE: int = 5

    # Severity
    P0_CLUSTER_SIZE: int = 50
    P0_NEG_RATIO: float = 0.7
    P1_CLUSTER_SIZE: int = 20


settings = Settings()
