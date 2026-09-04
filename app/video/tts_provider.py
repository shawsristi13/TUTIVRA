"""
TUTIVRA — TTS Provider Abstraction

Provides generateSpeech() — a provider-agnostic TTS interface.

Current provider: Fish Audio
Backend-only: API key is NEVER exposed to the frontend.

Configuration via .env:
  FISH_AUDIO_API_KEY   — required for Fish Audio
  FISH_AUDIO_VOICE_ID  — optional (uses default voice if empty)
  TTS_PROVIDER         — optional, defaults to "fish_audio"

Usage:
    from app.video.tts_provider import generateSpeech
    audio_path = generateSpeech("Hello student!", language="en", output_path="out.mp3")
"""

import os
import re
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

# ── Provider selection ───────────────────────────────────────
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "fish_audio").lower()

# ── Cache dir for generated audio ───────────────────────────
AUDIO_CACHE_DIR = Path("rag_uploads") / "tts_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════

def generateSpeech(
    text: str,
    language: str = "en",
    voice_id: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Convert text to speech audio.

    Args:
        text:        Text to synthesise.
        language:    BCP-47 language code (e.g. "en", "hi", "zh").
        voice_id:    Provider-specific voice ID. Uses env default if None.
        output_path: Where to save the audio file. Auto-generated if None.

    Returns:
        Absolute path to the generated MP3/WAV file.

    Raises:
        ValueError:  If required API keys are missing.
        RuntimeError: If TTS generation fails.
    """

    if not text.strip():
        raise ValueError("TTS text cannot be empty.")

    if output_path is None:
        output_path = _auto_output_path(text)

    if TTS_PROVIDER == "fish_audio":
        try:
            return _fish_audio_tts(text, language, voice_id, output_path)
        except Exception as e:
            logger.warning(f"Fish Audio TTS failed: {e}. Attempting fallback to Deepgram.")
            if os.getenv("DEEPGRAM_API_KEY"):
                return _deepgram_tts(text, language, output_path)
            raise RuntimeError(f"Fish Audio TTS failed and no Deepgram fallback available: {e}")
    else:
        raise ValueError(
            f"Unknown TTS provider: {TTS_PROVIDER}. "
            "Set TTS_PROVIDER=fish_audio in .env"
        )


def get_provider_info() -> dict:
    """Return info about the currently configured TTS provider."""
    return {
        "provider": TTS_PROVIDER,
        "configured": bool(_get_fish_key()),
        "supports_languages": [
            "en", "zh", "ja", "ko", "fr", "de", "ar", "hi",
        ],
    }


# ════════════════════════════════════════════════════════════
# FISH AUDIO IMPLEMENTATION
# ════════════════════════════════════════════════════════════

def _get_fish_key() -> str:
    return os.getenv("FISH_AUDIO_API_KEY", "")


def _fish_audio_tts(
    text: str,
    language: str,
    voice_id: Optional[str],
    output_path: str,
) -> str:
    """
    Call the Fish Audio TTS API.

    Fish Audio SDK: https://github.com/fishaudio/fish-audio-sdk
    API docs:       https://docs.fish.audio/
    """

    api_key = _get_fish_key()
    if not api_key:
        raise ValueError(
            "FISH_AUDIO_API_KEY is missing.\n"
            "Add it to your .env file:\n"
            "  FISH_AUDIO_API_KEY=your_key_here\n"
            "Get a key at: https://fish.audio/"
        )

    # Resolve voice ID
    effective_voice_id = (
        voice_id
        or os.getenv("FISH_AUDIO_VOICE_ID", "")
        or _default_voice_for_language(language)
    )

    try:
        from fish_audio_sdk import Session, TTSRequest

        session = Session(api_key)

        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        tts_request = TTSRequest(
            text=text,
            reference_id=effective_voice_id if effective_voice_id else None,
            # Fish Audio format: mp3
            format="mp3",
            # Latency mode: normal for quality
            latency="normal",
        )

        with open(output_path_obj, "wb") as f:
            for chunk in session.tts(tts_request):
                f.write(chunk)

        if not output_path_obj.exists() or output_path_obj.stat().st_size == 0:
            raise RuntimeError("Fish Audio returned empty audio data.")

        return str(output_path_obj.resolve())

    except ImportError:
        raise RuntimeError(
            "fish-audio-sdk not installed.\n"
            "Run: pip install fish-audio-sdk"
        )
    except Exception as e:
        raise RuntimeError(f"Fish Audio TTS failed: {e}") from e


def _default_voice_for_language(language: str) -> str:
    """
    Return a sensible default Fish Audio reference ID per language.
    These are public voices — override via FISH_AUDIO_VOICE_ID in .env.
    """
    # Fish Audio public voice IDs (reference IDs from the community library)
    # Empty string = Fish Audio will use its built-in default voice
    defaults = {
        "en":  "",  # Fish Audio default English voice
        "hi":  "",  # Hindi — Fish Audio default
        "zh":  "",  # Chinese
        "ja":  "",  # Japanese
        "ko":  "",  # Korean
        "fr":  "",  # French
        "de":  "",  # German
        "ar":  "",  # Arabic
    }
    return defaults.get(language.lower().split("-")[0], "")


# ════════════════════════════════════════════════════════════
# DEEPGRAM FALLBACK IMPLEMENTATION
# ════════════════════════════════════════════════════════════

def _deepgram_tts(
    text: str,
    language: str,
    output_path: str,
) -> str:
    """
    Call the Deepgram TTS API as a fallback.
    """
    api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is missing for fallback.")

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    url = "https://api.deepgram.com/v2/speak?model=flux-hannah-en&speed=1&expressivity=0"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        with open(output_path_obj, "wb") as f:
            f.write(response.content)

        if not output_path_obj.exists() or output_path_obj.stat().st_size == 0:
            raise RuntimeError("Deepgram returned empty audio data.")

        return str(output_path_obj.resolve())

    except Exception as e:
        raise RuntimeError(f"Deepgram TTS fallback failed: {e}") from e


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _auto_output_path(text: str) -> str:
    """Generate a deterministic filename based on text content."""
    hash_str = hashlib.md5(text.encode()).hexdigest()[:12]
    return str(AUDIO_CACHE_DIR / f"tts_{hash_str}.mp3")
