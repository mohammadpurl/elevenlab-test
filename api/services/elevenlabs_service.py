import os
import requests
import logging

logger = logging.getLogger(__name__)


class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not self.api_key:
            logger.error("ELEVEN_LABS_API_KEY not set")
            raise ValueError("ELEVEN_LABS_API_KEY environment variable is not set")

        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.base_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        logger.info("ElevenLabs service initialized successfully")

    def text_to_speech(self, text: str, file_name: str):
        try:
            logger.info(f"Converting text to speech: {text[:50]}...")
            logger.info(f"Output file: {file_name}")

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "text": text,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            }

            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()

            with open(file_name, "wb") as f:
                f.write(response.content)

            logger.info(f"Audio file created successfully: {file_name}")

        except Exception as e:
            logger.error(f"Error in ElevenLabs text-to-speech: {e}")
            raise
