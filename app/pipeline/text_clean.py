import re

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

# Patterns to remove
_URL_PATTERN = re.compile(r"https?://\S+")
_MENTION_PATTERN = re.compile(r"@\w+")
_HASHTAG_CLEAN = re.compile(r"#(\w+)")  # Keep the word, remove #
_MULTI_SPACE = re.compile(r"\s+")
_HTML_TAG = re.compile(r"<[^>]+>")


def clean_text(raw_text: str) -> str:
    """Clean raw social media text."""
    text = raw_text
    text = _HTML_TAG.sub("", text)
    text = _URL_PATTERN.sub("", text)
    text = _MENTION_PATTERN.sub("", text)
    text = _HASHTAG_CLEAN.sub(r"\1", text)
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


def detect_language(text: str) -> str:
    """Detect language of text. Returns ISO 639-1 code or 'unknown'."""
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"
