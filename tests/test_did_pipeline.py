import sys, os, requests, time
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

print("STEP 1: Deepgram TTS...")
key = os.getenv("DEEPGRAM_API_KEY", "")
output = Path("rag_uploads/tts_cache/test_did_audio.mp3")
output.parent.mkdir(parents=True, exist_ok=True)

resp = requests.post(
    "https://api.deepgram.com/v2/speak?model=flux-hannah-en&speed=1&expressivity=0",
    headers={"Authorization": f"Token {key}", "Content-Type": "application/json"},
    json={"text": "Hello I am Tutivra your AI teacher. Today we will learn about binary search."},
    timeout=30,
)
print(f"  Deepgram status: {resp.status_code}")
resp.raise_for_status()
output.write_bytes(resp.content)
print(f"  Audio saved: {output} ({output.stat().st_size} bytes)")

print()
print("STEP 2: D-ID upload + avatar video (audio_path method)...")
from app.video.avatar_provider import generateAvatarVideo
t0 = time.time()
result = generateAvatarVideo(audio_path=str(output.resolve()))
elapsed = time.time() - t0
print(f"  Status:    {result['status']}")
print(f"  Talk ID:   {result.get('talk_id')}")
print(f"  Video URL: {result.get('video_url')}")
print(f"  Error:     {result.get('error')}")
print(f"  Elapsed:   {elapsed:.1f}s")

if result["status"] == "done" and result.get("video_url"):
    print()
    print("SUCCESS -- video URL returned. Open in browser:")
    print(result["video_url"])
else:
    print()
    print("FAILED -- check D-ID credits / API key.")
