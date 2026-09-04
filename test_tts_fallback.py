from dotenv import load_dotenv
load_dotenv()
from app.video.tts_provider import generateSpeech

if __name__ == "__main__":
    try:
        audio_path = generateSpeech("Hello, this is a test of the Deepgram fallback mechanism.", output_path="test_audio.mp3")
        print(f"Success! Audio saved to: {audio_path}")
    except Exception as e:
        print(f"Error: {e}")
