from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from elevenlabs import ElevenLabs, VoiceSettings
import os
import logging
from io import BytesIO
from dotenv import load_dotenv
from api.routes.chat_route import router as chat_router
from api.routes.extract_info_routes import router as extract_info_routes
from api.config.logging_config import setup_logging, get_logger

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیم صحیح لاگینگ
setup_logging(level="INFO")
logger = get_logger(__name__)

app = FastAPI(title="Text-to-Speech API with ElevenLabs")
app.include_router(chat_router, prefix="/assistant")
app.include_router(extract_info_routes, prefix="/extractInfo")


# تنظیمات ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY is not set in environment variables")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


# مدل داده برای درخواست
class TextToSpeechRequest(BaseModel):
    text: str
    # voice_id: str = "pjcYQlDFKMbcOUp6F5GD"  # صدای پیش‌فرض (Adam)
    stability: float = 0.7
    similarity_boost: float = 0.8


@app.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    try:
        # تنظیمات صدا
        voice_settings = VoiceSettings(
            stability=request.stability, similarity_boost=request.similarity_boost
        )

        # تولید فایل صوتی با استفاده از متد جدید
        voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        if not voice_id:
            raise ValueError("ELEVENLABS_VOICE_ID is not set in environment variables")

        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            text=request.text,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings,
        )

        # جمع‌آوری داده‌های صوتی در یک بافر
        audio_buffer = BytesIO()
        for chunk in audio_stream:
            audio_buffer.write(chunk)
        audio_buffer.seek(0)

        # ارسال فایل صوتی به‌صورت استریم
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=output.mp3"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@app.get("/voices")
async def get_voices():
    try:
        # دریافت لیست صداهای موجود
        voices = client.voices.get_all()
        return {
            "voices": [
                {"id": voice.voice_id, "name": voice.name} for voice in voices.voices
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching voices: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
