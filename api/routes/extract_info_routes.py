from fastapi import APIRouter, HTTPException, Request
from api.schemas.extract_info_schema import (
    ExtractInfoRequest,
    ExtractInfoResponse,
    BookingStateData,
)
from api.services.extract_info_service import call_openai
from api.services.openai_service import OpenAIService
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


@router.get("/booking-state/{session_id}", response_model=BookingStateData)
async def get_booking_state(session_id: str):
    """Get the current booking state including all passenger information for a session"""
    try:
        openai_service = OpenAIService()

        # Check if session exists and has booking state
        if session_id not in openai_service.booking_states:
            raise HTTPException(status_code=404, detail="Session not found")

        booking_state = openai_service.booking_states[session_id]

        # Convert passenger data to the schema format
        passengers_data = []
        for passenger in booking_state.passengers_data:
            passenger_data = {
                "name": passenger.get("passenger_name", ""),
                "nationalId": passenger.get("national_id", ""),
                "passportNumber": passenger.get("passport_number", ""),
                "baggageCount": passenger.get("baggage_count", ""),
                "passengerType": passenger.get("passenger_type", ""),
                "gender": passenger.get("gender", ""),
            }
            passengers_data.append(passenger_data)

        # Create response (flight number is now top-level, not per passenger)
        response = BookingStateData(
            origin_airport=booking_state.collected_data.get("origin_airport", ""),
            travel_type=booking_state.collected_data.get("travel_type", ""),
            travel_date=booking_state.collected_data.get("travel_date", ""),
            flight_number=booking_state.collected_data.get("flight_number", ""),
            passenger_count=booking_state.collected_data.get("passenger_count", ""),
            passengers_data=passengers_data,
            additional_info=booking_state.collected_data.get("additional_info", ""),
        )

        return response

    except Exception as e:
        logger.error(f"Error getting booking state: {str(e)}")
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
