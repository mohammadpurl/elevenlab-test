from fastapi import APIRouter, HTTPException
from api.schemas.chat_schema import ChatRequest, ChatResponse, Message

from api.services.openai_service import OpenAIService
import os
import logging
import tempfile

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


@router.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World!"}


@router.get("/test")
def test():
    logger.info("Test endpoint called")
    return {"status": "ok", "message": "Test route is working!"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    logger.info(f"Chat endpoint called with message: {request.message}")

    openai_service = OpenAIService()
    api_key = get_openai_api_key()

    if not api_key:
        raise HTTPException(status_code=401, detail="OpenAI API key is not set")

    try:
        # گرفتن پیام‌ها از OpenAI
        logger.info("Getting response from OpenAI")
        openai_messages: list = openai_service.get_girlfriend_response(request.message)
        logger.info(f"OpenAI returned {len(openai_messages)} messages")
        return ChatResponse(messages=openai_messages)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
def health():
    logger.info("Health endpoint called")
    return {"status": "ok", "message": "Backend is running!"}
