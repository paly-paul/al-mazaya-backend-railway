"""
LangChain Google Gemini model helpers for the Mazaya FM agent.
"""
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings


def get_chat_model() -> ChatGoogleGenerativeAI:
    """Create the configured Google Gemini chat model."""
    kwargs: dict[str, Any] = {
        "model": settings.gemini_model,
        "temperature": 1.0,
        "max_tokens": None,
        "timeout": 20,
        "max_retries": 1,
    }
    if settings.gemini_api_key:
        kwargs["api_key"] = settings.gemini_api_key
    return ChatGoogleGenerativeAI(**kwargs)
