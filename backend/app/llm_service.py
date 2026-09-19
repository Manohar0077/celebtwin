"""
Optional LLM service for generating fun commentary on matches.
The LLM does NOT determine the match — only adds entertainment text.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


async def generate_comment(celebrity_name: str, score: float) -> Optional[str]:
    """
    Generate a short, fun comment about the match result.
    Returns None if LLM is not configured or call fails.
    """
    from .config import LLM_API_KEY, LLM_MODEL, LLM_ENABLED
    if not LLM_ENABLED:
        return None

    try:
        import httpx

        score_pct = round(score * 100)
        prompt = (
            f"The user's face has been compared to a celebrity database using face embeddings. "
            f"Their closest visual match is {celebrity_name} with a similarity score of {score_pct}%. "
            f"Write one short (2 sentences max), fun and encouraging comment about this result. "
            f"Make it clear this is based on visual similarity, not identity. Keep it light-hearted."
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{LLM_MODEL}:generateContent?key={LLM_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()

    except Exception as exc:
        logger.warning("LLM comment generation failed: %s", exc)
        return None
