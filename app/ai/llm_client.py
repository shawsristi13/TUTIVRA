"""
TUTIVRA — LLM Provider with Fallback Chain
==========================================
Single entry point for all LLM calls. Implements a provider chain:

  OpenRouter → Gemini → Groq → Error

Provider auto-detection:
  - OPENROUTER_API_KEY  → OpenRouter (openrouter.ai)
  - GEMINI_API_KEY      → Google Gemini (google.genai SDK)
  - XAI_API_KEY         → Auto-detected: Groq (gsk_*) or xAI (xai-*)

Fallback ONLY triggers on real provider failures:
  - Authentication failure (401/403)
  - Rate limit (429)
  - Server error (5xx)
  - Network timeout
  - Model not found / unavailable

Fallback does NOT trigger on:
  - Successful responses (even if content is unexpected)
  - Application-level / content errors (ValueError, TypeError, etc.)

Configuration via .env:
  OPENROUTER_API_KEY  + OPENROUTER_MODEL   (default: google/gemini-3.5-flash)
  GEMINI_API_KEY      + GEMINI_MODEL       (default: gemini-2.5-flash)
  XAI_API_KEY         + XAI_MODEL          (default: auto-detected)

Usage:
  from app.ai.llm_client import ask_ai, get_provider_status
  response = ask_ai("Explain recursion.")
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# ERROR CLASSIFICATION
# ════════════════════════════════════════════════════════════

PROVIDER_FAILURE_STATUSES = {401, 402, 403, 404, 408, 429, 500, 502, 503, 504}

PROVIDER_FAILURE_STRINGS = [
    "invalid api key", "authentication failed", "unauthorized",
    "insufficient credits", "quota exceeded", "rate limit",
    "payment required", "requires more credits", "402",
    "model not found", "model unavailable", "no endpoints found",
    "service unavailable", "internal server error",
    "connection error", "timeout", "timed out",
    "no such model", "deactivated", "suspended",
]


def _is_provider_failure(exc: Exception) -> bool:
    """Return True if exception is a real provider/API failure (should trigger fallback)."""
    msg = str(exc).lower()

    import re
    status_match = re.search(r"\b(4\d{2}|5\d{2})\b", msg)
    if status_match:
        code = int(status_match.group())
        if code in PROVIDER_FAILURE_STATUSES:
            return True

    for pattern in PROVIDER_FAILURE_STRINGS:
        if pattern in msg:
            return True

    exc_type = type(exc).__name__.lower()
    if any(t in exc_type for t in [
        "autherror", "authenticationerror", "apierror", "ratelimiterror",
        "serviceunavailable", "timeout", "connectionerror",
        "notfounderror", "permissiondenied", "badgateway",
    ]):
        return True

    return False


# ════════════════════════════════════════════════════════════
# PROVIDER IMPLEMENTATIONS
# ════════════════════════════════════════════════════════════

class _OpenRouterProvider:
    """OpenRouter via OpenAI-compatible API."""
    NAME = "openrouter"

    def __init__(self):
        self._client = None

    def is_configured(self) -> bool:
        return bool(os.getenv("OPENROUTER_API_KEY", ""))

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
            )
        return self._client

    def call(self, messages: list, model: Optional[str] = None, temperature: float = 0.7) -> str:
        client = self._get_client()
        effective_model = model or os.getenv("OPENROUTER_MODEL", "google/gemini-3.5-flash")
        response = client.chat.completions.create(
            model=effective_model,
            messages=messages,
            temperature=temperature,
            extra_headers={
                "HTTP-Referer": "https://tutivra.ai",
                "X-Title": "TUTIVRA AI Teacher",
            },
            timeout=60,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""


class _GeminiProvider:
    """Google Gemini via google.genai SDK (new SDK)."""
    NAME = "gemini"

    def is_configured(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY", ""))

    def call(self, messages: list, model: Optional[str] = None, temperature: float = 0.7) -> str:
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError:
            try:
                # Fallback to older SDK if new one not available
                import google.generativeai as genai_old
                return self._call_old_sdk(genai_old, messages, model, temperature)
            except ImportError:
                raise RuntimeError(
                    "Gemini SDK not installed. Run: pip install google-genai"
                )

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
        effective_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Flatten into a prompt string
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_parts   = [m["content"] for m in messages if m["role"] != "system"]

        full_prompt = ""
        if system_parts:
            full_prompt = "\n\n".join(system_parts) + "\n\n"
        full_prompt += "\n\n".join(user_parts)

        response = client.models.generate_content(
            model=effective_model,
            contents=full_prompt,
            config=genai_types.GenerateContentConfig(temperature=temperature),
        )
        return response.text.strip() if response.text else ""

    def _call_old_sdk(self, genai_old, messages, model, temperature):
        """Fallback to deprecated google.generativeai SDK."""
        genai_old.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
        effective_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_parts   = [m["content"] for m in messages if m["role"] != "system"]
        full_prompt  = ("\n\n".join(system_parts) + "\n\n" if system_parts else "") + "\n\n".join(user_parts)

        model_obj = genai_old.GenerativeModel(
            model_name=effective_model,
            generation_config=genai_old.types.GenerationConfig(temperature=temperature),
        )
        response = model_obj.generate_content(full_prompt)
        return response.text.strip() if response.text else ""


class _GroqProvider:
    """
    Groq (cloud.groq.com) via OpenAI-compatible API.
    Activated when XAI_API_KEY starts with 'gsk_' (Groq key format).
    Also activated when GROQ_API_KEY is set.
    xAI keys (start with 'xai-') use api.x.ai instead.
    """
    NAME = "groq"

    def __init__(self):
        self._client = None
        self._base_url = None
        self._provider_name = None

    def _detect(self):
        """Detect whether XAI_API_KEY is Groq or xAI."""
        key = os.getenv("XAI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        if not key:
            return None, None, None

        if key.startswith("gsk_") or os.getenv("GROQ_API_KEY"):
            return key, "https://api.groq.com/openai/v1", "groq"
        else:
            # True xAI key
            return key, "https://api.x.ai/v1", "xai"

    def is_configured(self) -> bool:
        key, _, _ = self._detect()
        return bool(key)

    def _get_client(self):
        if self._client is None:
            key, base_url, name = self._detect()
            if not key:
                raise ValueError("No XAI_API_KEY or GROQ_API_KEY configured")
            from openai import OpenAI
            self._client = OpenAI(base_url=base_url, api_key=key)
            self._base_url = base_url
            self._provider_name = name
        return self._client

    def _default_model(self) -> str:
        """Pick a model that works for the detected provider."""
        _, _, name = self._detect()
        if name == "groq":
            return os.getenv("XAI_MODEL", "groq/compound-mini")
        else:
            return os.getenv("XAI_MODEL", "grok-3-mini")

    def call(self, messages: list, model: Optional[str] = None, temperature: float = 0.7) -> str:
        client = self._get_client()
        effective_model = model or self._default_model()
        response = client.chat.completions.create(
            model=effective_model,
            messages=messages,
            temperature=temperature,
            timeout=60,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""


# ════════════════════════════════════════════════════════════
# PROVIDER CHAIN
# ════════════════════════════════════════════════════════════

_openrouter = _OpenRouterProvider()
_gemini     = _GeminiProvider()
_grok       = _GroqProvider()

_PROVIDER_CHAIN = [_openrouter, _gemini, _grok]

_last_used_provider: str = "none"
_last_fallback_reason: str = ""


def get_provider_status() -> dict:
    """Return info about configured providers and which was last used."""
    return {
        "active_provider":      _last_used_provider,
        "last_fallback_reason": _last_fallback_reason,
        "openrouter_configured": _openrouter.is_configured(),
        "gemini_configured":     _gemini.is_configured(),
        "grok_configured":       _grok.is_configured(),
        "providers_in_chain": [
            p.NAME for p in _PROVIDER_CHAIN if p.is_configured()
        ],
    }


# ════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════

def ask_ai(
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    _force_provider: Optional[str] = None,
) -> str:
    """
    Send a prompt through the LLM provider chain.

    Fallback triggers ONLY on real provider/API failures.
    Non-provider errors (ValueError, TypeError, etc.) propagate immediately.

    Args:
        prompt:          User message.
        model:           Override model for this call (provider-specific).
        system_prompt:   Optional system instruction prepended to messages.
        temperature:     Sampling temperature (0.0 = deterministic).
        _force_provider: FOR TESTING ONLY — force a specific provider name.

    Returns:
        Response text string.

    Raises:
        LLMError: If all providers in the chain fail.
    """
    global _last_used_provider, _last_fallback_reason

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if _force_provider:
        chain = [p for p in _PROVIDER_CHAIN if p.NAME == _force_provider]
        if not chain:
            raise LLMError(f"Unknown provider: {_force_provider}")
    else:
        chain = [p for p in _PROVIDER_CHAIN if p.is_configured()]

    if not chain:
        raise LLMError(
            "No LLM provider is configured.\n"
            "Add at least one of these to your .env:\n"
            "  OPENROUTER_API_KEY=...\n"
            "  GEMINI_API_KEY=...\n"
            "  XAI_API_KEY=... (Groq gsk_ or xAI xai- keys)\n"
        )

    errors = []

    for i, provider in enumerate(chain):
        try:
            logger.debug("Trying provider: %s", provider.NAME)
            result = provider.call(messages, model=model, temperature=temperature)

            _last_used_provider = provider.NAME
            _last_fallback_reason = (
                f"Fell back from {chain[i-1].NAME}: {errors[-1]}" if i > 0 else ""
            )
            if i > 0:
                logger.warning(
                    "Provider %s failed; used %s as fallback. Reason: %s",
                    chain[i - 1].NAME, provider.NAME, errors[-1],
                )
            return result

        except Exception as exc:
            if _is_provider_failure(exc):
                logger.warning("Provider %s failed: %s", provider.NAME, exc)
                errors.append(f"{provider.NAME}: {exc}")
                if i < len(chain) - 1:
                    continue
            else:
                # Non-provider error — propagate immediately
                _last_used_provider = provider.NAME
                raise

    raise LLMError(
        f"All LLM providers failed:\n" + " | ".join(errors) + "\n\n"
        "Check your API keys and network connection."
    )


class LLMError(Exception):
    """Raised when all LLM providers in the chain fail."""
    pass
