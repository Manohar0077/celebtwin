"""
LLM service for generating visual match explanations.
Explains specifically why the user matches with their top celebrity lookalike.
Uses Gemini when LLM_API_KEY is available, with an intelligent dynamic fallback.
"""
import logging
import random
from typing import Optional
from .config import LLM_API_KEY, LLM_MODEL, LLM_ENABLED

logger = logging.getLogger(__name__)


def _get_fallback_explanation(celebrity_name: str, category: str, score_pct: int) -> str:
    """Provides a tailored facial landmark explanation if LLM API is unavailable."""
    cat_lower = category.lower()

    if "cricket" in cat_lower:
        templates = [
            f"Strong brow ridge alignment, high-focus eye contours, and structured jawline symmetry closely mirror {celebrity_name}'s determined athletic intensity.",
            f"Sharp cheekbone contours and defined facial angles reflect {celebrity_name}'s focused, charismatic game-day presence.",
        ]
    elif "actress" in cat_lower or "female" in cat_lower:
        templates = [
            f"Harmonious cheekbone balance, elegant brow arch, and expressive eye spacing capture {celebrity_name}'s photogenic symmetry and radiant screen aura.",
            f"Graceful facial proportions, delicate chin contour, and bright eye alignment create an unmistakable resemblance to {celebrity_name}.",
        ]
    else:
        templates = [
            f"Distinctive jawline structure, balanced mid-face proportions, and a charismatic gaze align closely with {celebrity_name}'s signature on-screen presence.",
            f"Striking cheekbone symmetry, expressive eye depth, and natural facial contours capture the charismatic aura of {celebrity_name}.",
        ]

    # Deterministic selection based on name hash so it stays consistent for the same person
    choice_idx = hash(celebrity_name) % len(templates)
    return templates[choice_idx]


async def generate_comment(celebrity_name: str, score: float, category: str = "Celebrity") -> str:
    """
    Generate an engaging explanation detailing why the user matches with the celebrity.
    """
    score_pct = round(score * 100)

    if LLM_ENABLED and LLM_API_KEY:
        try:
            import httpx

            prompt = (
                f"The user's face was scanned and matched with celebrity {celebrity_name} ({category}) "
                f"with a {score_pct}% facial embedding similarity score. "
                f"Explain in exactly 2 concise, vivid sentences WHY they visually match. "
                f"Highlight shared visual features like jawline contour, brow arch, cheekbone symmetry, eye spacing, or smile aura. "
                f"Be observant, enthusiastic, and flattering. Output only the 2-sentence explanation."
            )

            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{LLM_MODEL}:generateContent?key={LLM_API_KEY}",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        if text:
                            return text
        except Exception as exc:
            logger.warning("LLM call failed, using dynamic explanation fallback: %s", exc)

    return _get_fallback_explanation(celebrity_name, category, score_pct)
