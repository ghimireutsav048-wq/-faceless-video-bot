import os

BRAND_NAME = "THE UNKNOWN FILES"
VIDEO_SECONDS = 60
DEFAULT_VIDEO_COUNT = 5
WIDTH, HEIGHT = 1080, 1920
FPS = 30
# Voices rotate across videos; the same voice is not used twice in one batch if possible.
VOICE_POOL = [
    "en-US-GuyNeural",
    "en-US-DavisNeural",
    "en-US-JaneNeural",
    "en-GB-RyanNeural",
    "en-GB-SoniaNeural",
    "en-AU-WilliamNeural",
]
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_PRIVACY_STATUS = os.getenv("YOUTUBE_PRIVACY_STATUS", "private")
