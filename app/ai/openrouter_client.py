"""
TUTIVRA — OpenRouter Client (compatibility shim)

This module is kept for backward compatibility.
All logic has moved to app.ai.llm_client which implements
a full OpenRouter → Gemini → Grok fallback chain.

New code should import from app.ai.llm_client directly:
  from app.ai.llm_client import ask_ai, get_provider_status
"""

# Re-export everything from the unified LLM client
from app.ai.llm_client import ask_ai, get_provider_status, LLMError  # noqa: F401

__all__ = ["ask_ai", "get_provider_status", "LLMError"]