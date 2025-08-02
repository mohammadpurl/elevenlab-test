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
        # گرفتن پیام‌ها از OpenAI با session_id
        logger.info("Getting response from OpenAI")
        session_id = getattr(request, "session_id", None)
        openai_messages, session_id = openai_service.get_girlfriend_response(
            request.message, session_id if session_id else None
        )
        logger.info(
            f"OpenAI returned {len(openai_messages)} messages for session: {session_id}"
        )

        # اضافه کردن session_id به پاسخ
        response = ChatResponse(messages=openai_messages)
        response.session_id = session_id
        return response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
def health():
    logger.info("Health endpoint called")
    return {"status": "ok", "message": "Backend is running!"}


@router.get("/memory/{session_id}")
def get_memory(session_id: str):
    """Get conversation history for a session"""
    try:
        openai_service = OpenAIService()
        history = openai_service.get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory: {str(e)}")


@router.delete("/memory/{session_id}")
def clear_memory(session_id: str):
    """Clear conversation history for a session"""
    try:
        openai_service = OpenAIService()
        openai_service.clear_memory(session_id)
        return {"message": f"Memory cleared for session: {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")
