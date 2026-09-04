"""
TUTIVRA — Avatar Video Provider Abstraction

Provides generateAvatarVideo() — a provider-agnostic avatar API interface.

Current provider: D-ID
Backend-only: API key is NEVER exposed to the frontend.

Flow:
  audio_path → D-ID API → avatar video URL/path

Configuration via .env:
  DID_API_KEY         — required
  DID_PRESENTER_ID    — optional (default: amy-Aq6OmGZnMt)
  AVATAR_PROVIDER     — optional, defaults to "did"

D-ID API docs: https://docs.d-id.com/reference/talks
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# ── Provider selection ───────────────────────────────────────
AVATAR_PROVIDER = os.getenv("AVATAR_PROVIDER", "did").lower()

# ── D-ID API config ──────────────────────────────────────────
DID_API_BASE = "https://api.d-id.com"

# Default D-ID presenter (Amy — professional, clear)
DEFAULT_PRESENTER_ID = os.getenv("DID_PRESENTER_ID", "amy-Aq6OmGZnMt")

# D-ID presenter image URL — must be a publicly accessible URL.
# Using D-ID's own public S3 bucket (confirmed working).
DEFAULT_PRESENTER_IMAGE = (
    "https://d-id-public-bucket.s3.us-east-1.amazonaws.com/alice.jpg"
)


# ════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════

def generateAvatarVideo(
    audio_path: Optional[str] = None,
    audio_url: Optional[str] = None,
    script_text: Optional[str] = None,
    avatar_id: Optional[str] = None,
    options: Optional[dict] = None,
    poll_timeout_seconds: int = 120,
) -> dict:
    """
    Generate a talking-head avatar video.

    Provide one of:
      audio_path   — local audio file (uploaded to D-ID)
      audio_url    — publicly accessible audio URL
      script_text  — text for D-ID to synthesise internally (no Fish Audio)

    Args:
        audio_path:           Path to local audio file.
        audio_url:            URL of pre-generated audio.
        script_text:          Text for D-ID TTS (fallback if no audio).
        avatar_id:            D-ID presenter ID. Uses env default if None.
        options:              Extra D-ID API options dict.
        poll_timeout_seconds: Max seconds to wait for video generation.

    Returns:
        {
          "status": "done" | "error",
          "video_url": str,        # URL of the generated video
          "talk_id":   str,        # D-ID talk ID
          "error":     str | None, # Error message if failed
        }
    """

    if AVATAR_PROVIDER == "did":
        return _did_generate(
            audio_path=audio_path,
            audio_url=audio_url,
            script_text=script_text,
            avatar_id=avatar_id or DEFAULT_PRESENTER_ID,
            options=options or {},
            poll_timeout=poll_timeout_seconds,
        )
    else:
        raise ValueError(
            f"Unknown avatar provider: {AVATAR_PROVIDER}. "
            "Set AVATAR_PROVIDER=did in .env"
        )


def get_avatar_provider_info() -> dict:
    return {
        "provider": AVATAR_PROVIDER,
        "configured": bool(_get_did_key()),
        "default_avatar": DEFAULT_PRESENTER_ID,
    }


# ════════════════════════════════════════════════════════════
# D-ID IMPLEMENTATION
# ════════════════════════════════════════════════════════════

def _get_did_key() -> str:
    return os.getenv("DID_API_KEY", "")


def _did_headers() -> dict:
    key = _get_did_key()
    if not key:
        raise ValueError(
            "DID_API_KEY is missing.\n"
            "Add it to your .env file:\n"
            "  DID_API_KEY=your_key_here\n"
            "Get a key at: https://www.d-id.com/"
        )
    return {
        "Authorization": f"Basic {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _did_generate(
    audio_path: Optional[str],
    audio_url: Optional[str],
    script_text: Optional[str],
    avatar_id: str,
    options: dict,
    poll_timeout: int,
) -> dict:
    """
    Full D-ID talks pipeline:
    1. (Optional) Upload audio file → get URL
    2. POST /talks → get talk_id
    3. Poll GET /talks/{id} until done or timeout
    """

    headers = _did_headers()

    # ── Step 1: Resolve audio source ─────────────────────────

    resolved_audio_url = None

    if audio_path:
        resolved_audio_url = _did_upload_audio(audio_path, headers)
    elif audio_url:
        resolved_audio_url = audio_url

    # ── Step 2: Build request payload ────────────────────────

    if resolved_audio_url:
        # Use pre-generated audio (Fish Audio output)
        script = {
            "type": "audio",
            "audio_url": resolved_audio_url,
        }
    elif script_text:
        # Fallback: let D-ID synthesise the voice
        script = {
            "type": "text",
            "input": script_text,
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural",
            },
        }
    else:
        raise ValueError(
            "Must provide audio_path, audio_url, or script_text."
        )

    payload = {
        "source_url": DEFAULT_PRESENTER_IMAGE,
        "script": script,
        "config": {
            "fluent": True,
            "pad_audio": 0.0,
            "stitch": True,
        },
        **options,
    }

    # ── Step 3: Create the talk ───────────────────────────────

    try:
        resp = requests.post(
            f"{DID_API_BASE}/talks",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return {
            "status": "error",
            "video_url": "",
            "talk_id": "",
            "error": f"D-ID create talk failed: {e}",
        }

    talk_data = resp.json()
    talk_id = talk_data.get("id", "")

    if not talk_id:
        return {
            "status": "error",
            "video_url": "",
            "talk_id": "",
            "error": f"D-ID did not return a talk ID. Response: {talk_data}",
        }

    # ── Step 4: Poll for completion ───────────────────────────

    return _did_poll(talk_id, headers, poll_timeout)


def _did_upload_audio(audio_path: str, headers: dict) -> str:
    """
    Upload a local audio file to D-ID and return its URL.
    D-ID accepts audio via the /audios endpoint.
    """

    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    upload_headers = {
        "Authorization": headers["Authorization"],
        "Accept": "application/json",
    }

    try:
        with open(audio_file, "rb") as f:
            resp = requests.post(
                f"{DID_API_BASE}/audios",
                files={"audio": (audio_file.name, f, "audio/mpeg")},
                headers=upload_headers,
                timeout=60,
            )
            resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"D-ID audio upload failed: {e}") from e

    upload_data = resp.json()
    audio_url = upload_data.get("url", "")

    if not audio_url:
        raise RuntimeError(
            f"D-ID audio upload did not return a URL. Response: {upload_data}"
        )

    return audio_url


def _did_poll(
    talk_id: str,
    headers: dict,
    timeout: int,
) -> dict:
    """Poll D-ID until the talk is done or timeout."""

    start = time.time()
    poll_interval = 3  # seconds

    while time.time() - start < timeout:
        try:
            resp = requests.get(
                f"{DID_API_BASE}/talks/{talk_id}",
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            return {
                "status": "error",
                "video_url": "",
                "talk_id": talk_id,
                "error": f"D-ID poll failed: {e}",
            }

        data = resp.json()
        status = data.get("status", "")

        if status == "done":
            video_url = data.get("result_url", "")
            return {
                "status": "done",
                "video_url": video_url,
                "talk_id": talk_id,
                "error": None,
                "duration": data.get("duration"),
            }

        if status in ("error", "rejected"):
            return {
                "status": "error",
                "video_url": "",
                "talk_id": talk_id,
                "error": data.get("error", {}).get("description", "D-ID error"),
            }

        time.sleep(poll_interval)

    return {
        "status": "error",
        "video_url": "",
        "talk_id": talk_id,
        "error": f"D-ID talk timed out after {timeout}s",
    }
