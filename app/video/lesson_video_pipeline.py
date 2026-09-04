"""
TUTIVRA — Lesson Video Pipeline

Orchestrates the full AI teaching video pipeline:

  Lesson Text
      ↓
  Scene Planner  (LLM → structured scene JSON)
      ↓
  [For each scene]
  TTS Provider   (Fish Audio → audio file per scene)
      ↓
  Avatar Provider (D-ID → avatar video per scene)
      ↓
  Visual Generator (HTML visual per scene)
      ↓
  Scene result bundle

The pipeline returns per-scene bundles that the UI assembles and plays back.
Full FFmpeg video composition is handled if ffmpeg is available,
otherwise the UI plays scenes sequentially.

Usage:
    from app.video.lesson_video_pipeline import run_lesson_pipeline

    result = run_lesson_pipeline(
        topic="Binary Search Trees",
        lesson_text="...",
        student_level="beginner",
        language="en",
    )

    for scene_bundle in result["scenes"]:
        print(scene_bundle["scene"]["narration"])
        print(scene_bundle["audio_path"])
        print(scene_bundle["video_url"])
        print(scene_bundle["visual_html"])
"""

import os
import time
from pathlib import Path
from typing import Optional

from app.video.scene_planner import plan_lesson_scenes, SceneDict
from app.video.tts_provider import generateSpeech
from app.video.avatar_provider import generateAvatarVideo
from app.video.visual_generator import generate_visual


# ── Output directories ───────────────────────────────────────
OUTPUT_DIR = Path("rag_uploads") / "pipeline_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════
# MAIN PIPELINE ENTRY POINT
# ════════════════════════════════════════════════════════════

def run_lesson_pipeline(
    topic: str,
    lesson_text: str,
    student_level: str = "beginner",
    language: str = "en",
    available_time_minutes: int = 10,
    subject_area: str = "",
    learning_objective: str = "",
    generate_audio: bool = True,
    generate_avatar: bool = True,
    session_id: Optional[str] = None,
) -> dict:
    """
    Run the complete teaching video pipeline for a lesson.

    Args:
        topic:                  Main topic.
        lesson_text:            Lesson content (from teaching_engine or RAG).
        student_level:          Student level (beginner/intermediate/advanced).
        language:               BCP-47 language code (e.g. "en", "hi").
        available_time_minutes: Total time budget.
        subject_area:           Optional subject for visual selection.
        learning_objective:     What student should achieve.
        generate_audio:         Whether to call Fish Audio (needs API key).
        generate_avatar:        Whether to call D-ID (needs API key).
        session_id:             Optional ID for organising output files.

    Returns:
        {
          "topic":        str,
          "language":     str,
          "total_scenes": int,
          "scenes":       list[SceneBundle],
          "errors":       list[str],
          "pipeline_status": "complete" | "partial" | "scenes_only",
        }

        SceneBundle = {
          "scene":       SceneDict,       # structured scene data
          "visual_html": str,             # HTML visual for this scene
          "audio_path":  str | None,      # path to MP3 (if generated)
          "video_url":   str | None,      # D-ID video URL (if generated)
          "audio_error": str | None,
          "video_error": str | None,
        }
    """

    errors = []
    sid = session_id or f"session_{int(time.time())}"

    # ── Step 1: Plan scenes ──────────────────────────────────

    scenes: list[SceneDict] = plan_lesson_scenes(
        topic=topic,
        lesson_text=lesson_text,
        student_level=student_level,
        language=_lang_code_to_name(language),
        available_time_minutes=available_time_minutes,
        subject_area=subject_area,
        learning_objective=learning_objective,
    )

    if not scenes:
        errors.append("Scene planner returned no scenes.")
        return {
            "topic": topic,
            "language": language,
            "total_scenes": 0,
            "scenes": [],
            "errors": errors,
            "pipeline_status": "error",
        }

    # ── Step 2: Process each scene ───────────────────────────

    scene_bundles = []

    for i, scene in enumerate(scenes):
        bundle = _process_scene(
            scene=scene,
            scene_index=i,
            subject_area=subject_area,
            language=language,
            session_id=sid,
            generate_audio=generate_audio,
            generate_avatar=generate_avatar,
        )
        scene_bundles.append(bundle)
        if bundle["audio_error"]:
            errors.append(f"Scene {i+1} audio: {bundle['audio_error']}")
        if bundle["video_error"]:
            errors.append(f"Scene {i+1} video: {bundle['video_error']}")

    # ── Step 3: Determine pipeline status ────────────────────

    has_audio = any(b["audio_path"] for b in scene_bundles)
    has_video = any(b["video_url"] for b in scene_bundles)

    if has_video:
        status = "complete"
    elif has_audio:
        status = "partial"  # Audio but no avatar video
    else:
        status = "scenes_only"  # Structured scenes but no media

    return {
        "topic": topic,
        "language": language,
        "total_scenes": len(scenes),
        "scenes": scene_bundles,
        "errors": errors,
        "pipeline_status": status,
    }


# ════════════════════════════════════════════════════════════
# SCENE PROCESSOR
# ════════════════════════════════════════════════════════════

def _process_scene(
    scene: SceneDict,
    scene_index: int,
    subject_area: str,
    language: str,
    session_id: str,
    generate_audio: bool,
    generate_avatar: bool,
) -> dict:
    """Process a single scene: generate visual + audio + avatar video."""

    # ── Visual (always generated, no API needed) ──────────────

    visual_html = generate_visual(
        visual_type=scene.get("visual_type", "none"),
        visual_content=scene.get("visual_content", ""),
        on_screen_text=scene.get("on_screen_text", ""),
        subject_area=subject_area,
    )

    # ── Audio (Fish Audio) ────────────────────────────────────

    audio_path = None
    audio_error = None

    if generate_audio and scene.get("narration"):
        try:
            narration = scene["narration"]
            output_path = str(
                OUTPUT_DIR / session_id / f"scene_{scene_index + 1}_audio.mp3"
            )
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            audio_path = generateSpeech(
                text=narration,
                language=language,
                output_path=output_path,
            )
        except Exception as e:
            audio_error = str(e)

    # ── Avatar Video (D-ID) ───────────────────────────────────

    video_url = None
    video_error = None

    if generate_avatar:
        try:
            avatar_result = generateAvatarVideo(
                audio_path=audio_path,
                script_text=(
                    scene.get("narration")
                    if not audio_path
                    else None
                ),
            )

            if avatar_result["status"] == "done":
                video_url = avatar_result["video_url"]
            else:
                video_error = avatar_result.get("error", "D-ID failed")

        except Exception as e:
            video_error = str(e)

    return {
        "scene": scene,
        "visual_html": visual_html,
        "audio_path": audio_path,
        "video_url": video_url,
        "audio_error": audio_error,
        "video_error": video_error,
    }


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _lang_code_to_name(code: str) -> str:
    """Convert BCP-47 code to language name for scene planner prompts."""
    mapping = {
        "en": "English",
        "hi": "Hindi",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "de": "German",
        "ar": "Arabic",
        "es": "Spanish",
        "pt": "Portuguese",
    }
    return mapping.get(code.lower().split("-")[0], "English")
