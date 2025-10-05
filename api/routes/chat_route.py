from fastapi import APIRouter, HTTPException
from api.schemas.chat_schema import ChatRequest, ChatResponse, Message

from api.services.openai_service import OpenAIService
from api.config.logging_config import get_logger
import os

# تنظیم لاگر
logger = get_logger(__name__)

router = APIRouter()

# ایجاد یک instance مشترک از OpenAI Service برای بهبود عملکرد
_openai_service = None


def get_openai_service():
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


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

    api_key = get_openai_api_key()
    if not api_key:
        raise HTTPException(status_code=401, detail="OpenAI API key is not set")

    try:
        # استفاده از instance مشترک برای بهبود عملکرد
        openai_service = get_openai_service()

        # گرفتن پیام‌ها از OpenAI با session_id
        logger.info("Getting response from OpenAI")
        session_id = getattr(request, "session_id", None)
        language = getattr(request, "language", "fa")
        openai_messages, session_id = openai_service.get_assistant_response(
            request.message, session_id if session_id else None, language
        )
        logger.info(
            f"[OpenAI] returned {len(openai_messages)} messages for session: {session_id}"
        )

        # تبدیل پاسخ‌ها به یک Message object
        try:
            combined_text = ""
            combined_facial_expression = "default"
            combined_animation = "StandingIdle"

            if isinstance(openai_messages, list):
                for m in openai_messages:
                    text = m.get("text") if isinstance(m, dict) else None
                    if text:
                        combined_text += str(text) + "\n"
                        # Use the facial expression and animation from the first message
                        if combined_facial_expression == "default" and m.get(
                            "facialExpression"
                        ):
                            combined_facial_expression = m.get("facialExpression")
                        if combined_animation == "StandingIdle" and m.get("animation"):
                            combined_animation = m.get("animation")
            elif isinstance(openai_messages, dict) and "text" in openai_messages:
                combined_text = str(openai_messages["text"])
                combined_facial_expression = openai_messages.get(
                    "facialExpression", "default"
                )
                combined_animation = openai_messages.get("animation", "StandingIdle")

            combined_text = combined_text.strip()

            message_obj = Message(
                text=combined_text,
                facialExpression=combined_facial_expression,
                animation=combined_animation,
            )
            response = ChatResponse(messages=message_obj, session_id=session_id)
            return response
        except Exception as combine_error:
            logger.error(f"Error creating message object: {combine_error}")
            raise HTTPException(
                status_code=500, detail="Failed to create message object"
            )

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
        openai_service = get_openai_service()
        history = openai_service.get_conversation_history(session_id)
        logger.info(
            f"Memory endpoint called for session {session_id}, found {len(history)} messages"
        )
        return {"session_id": session_id, "history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory: {str(e)}")


@router.delete("/memory/{session_id}")
def clear_memory(session_id: str):
    """Clear conversation history for a session"""
    try:
        openai_service = get_openai_service()
        openai_service.clear_memory(session_id)
        return {"message": f"Memory cleared for session: {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")
