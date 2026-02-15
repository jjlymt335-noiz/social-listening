"""Fetch real posts from Reddit's public JSON API (no auth required)."""

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None

HEADERS = {
    "User-Agent": "SocialListeningBot/1.0 (research project)",
}


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0, headers=HEADERS, follow_redirects=True)
    return _client


async def search_reddit(query: str, subreddit: str | None = None, limit: int = 50) -> list[dict]:
    """Search Reddit for posts matching the query.

    Returns a list of dicts with keys:
        id, author, title, selftext, subreddit, created_utc, score, num_comments, permalink, url
    """
    client = _get_client()

    if subreddit:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "restrict_sr": "on", "sort": "new", "limit": min(limit, 100), "t": "month"}
    else:
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "sort": "new", "limit": min(limit, 100), "t": "month"}

    posts = []
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            posts.append({
                "id": post.get("id", ""),
                "author": post.get("author", "[deleted]"),
                "title": post.get("title", ""),
                "selftext": post.get("selftext", ""),
                "subreddit": post.get("subreddit", ""),
                "created_utc": post.get("created_utc", 0),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "permalink": post.get("permalink", ""),
                "url": post.get("url", ""),
            })

        logger.info("Fetched %d posts from Reddit for query '%s'", len(posts), query)
    except Exception:
        logger.exception("Failed to fetch Reddit posts for query '%s'", query)

    return posts


async def fetch_subreddit_posts(subreddit: str, sort: str = "new", limit: int = 50) -> list[dict]:
    """Fetch recent posts from a specific subreddit."""
    client = _get_client()
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    params = {"limit": min(limit, 100)}

    posts = []
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            posts.append({
                "id": post.get("id", ""),
                "author": post.get("author", "[deleted]"),
                "title": post.get("title", ""),
                "selftext": post.get("selftext", ""),
                "subreddit": post.get("subreddit", ""),
                "created_utc": post.get("created_utc", 0),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "permalink": post.get("permalink", ""),
                "url": post.get("url", ""),
            })

        logger.info("Fetched %d posts from r/%s", len(posts), subreddit)
    except Exception:
        logger.exception("Failed to fetch posts from r/%s", subreddit)

    return posts


async def fetch_post_comments(permalink: str, limit: int = 20) -> list[dict]:
    """Fetch top-level comments for a specific post."""
    client = _get_client()
    url = f"https://www.reddit.com{permalink}.json"
    params = {"limit": limit, "sort": "top"}

    comments = []
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2:
            for child in data[1].get("data", {}).get("children", []):
                comment = child.get("data", {})
                if child.get("kind") != "t1":
                    continue
                comments.append({
                    "id": comment.get("id", ""),
                    "author": comment.get("author", "[deleted]"),
                    "body": comment.get("body", ""),
                    "score": comment.get("score", 0),
                    "created_utc": comment.get("created_utc", 0),
                })

        logger.info("Fetched %d comments for %s", len(comments), permalink)
    except Exception:
        logger.exception("Failed to fetch comments for %s", permalink)

    return comments


def reddit_ts_to_datetime(utc_ts: float) -> datetime:
    """Convert Reddit UTC timestamp to timezone-aware datetime."""
    return datetime.fromtimestamp(utc_ts, tz=timezone.utc)
