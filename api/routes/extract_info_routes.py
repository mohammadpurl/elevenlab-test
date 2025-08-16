from fastapi import APIRouter, HTTPException, Request
from api.schemas.extract_info_schema import ExtractInfoRequest, ExtractInfoResponse
from api.services.extract_info_service import call_openai
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract-info", response_model=ExtractInfoResponse)
async def extract_info(request: ExtractInfoRequest):
    try:
        logger.info(
            f"Received extract_info request with {len(request.messages)} messages"
        )
        logger.info(
            f"First message: {request.messages[0] if request.messages else 'No messages'}"
        )
        result = await call_openai(request)
        return result
    except Exception as e:
        logger.error(f"Error in extract_info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug-extract-info")
async def debug_extract_info(request: Request):
    """Debug endpoint to test JSON parsing"""
    try:
        # Get raw body
        body = await request.body()
        # print(f"Raw body: {body}")

        # Try to parse JSON
        try:
            json_data = await request.json()
            print(f"Parsed JSON: {json_data}")
        except Exception as json_error:
            print(f"JSON parsing error: {json_error}")
            return {"error": "JSON parsing failed", "detail": str(json_error)}

        # Try to validate with Pydantic
        try:
            validated_data = ExtractInfoRequest(**json_data)
            print(f"Validated data: {validated_data}")
            return {"success": True, "data": validated_data.dict()}
        except Exception as validation_error:
            print(f"Validation error: {validation_error}")
            return {"error": "Validation failed", "detail": str(validation_error)}

    except Exception as e:
        print(f"General error: {e}")
        return {"error": "General error", "detail": str(e)}
