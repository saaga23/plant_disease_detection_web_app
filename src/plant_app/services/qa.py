"""Question-answering service (OpenAI-backed, optional).

The legacy app used langchain 0.0.302's ``langchain.llms.OpenAI``, an import
path that no longer exists in any maintained langchain release, with a
placeholder key hardcoded in source. This module calls the OpenAI API
directly, reads the key from the environment, and degrades gracefully when it
is absent.

The legacy system prompt claimed the assistant was "an agricultural expert".
That overstated what a language model can safely advise on; the prompt now
positions the assistant as general agricultural information with an explicit
disclaimer that it is not professional agronomic advice.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers general agricultural questions "
    "in plain language. You provide educational information only, not "
    "professional agronomic, veterinary, or legal advice. When a question "
    "concerns a crop disease, pest control, or animal health decision, remind "
    "the user to confirm with a local agricultural extension officer or a "
    "licensed professional."
)


def answer_question(question: str, api_key: str | None, model: str = "gpt-4o-mini") -> tuple[str | None, str]:
    """Return (answer, note). answer is None when the service is unavailable."""
    if not api_key:
        return None, (
            "Question answering is not configured. Set the OPENAI_API_KEY "
            "environment variable (see .env.example) to enable this page."
        )
    question = (question or "").strip()
    if not question:
        return None, "Type a question first."
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            max_tokens=500,
            temperature=0.2,
        )
    except Exception as exc:  # network, auth, quota, or SDK errors
        logger.warning("OpenAI request failed: %s", exc)
        return None, "The question-answering service could not be reached. Check the API key and your internet connection."
    text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not text:
        return None, "The service returned an empty answer. Try rephrasing the question."
    return text, (
        "AI-generated general information - verify against local extension "
        "services before making farm decisions."
    )
