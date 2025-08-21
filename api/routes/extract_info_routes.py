from fastapi import APIRouter, HTTPException, Request
from api.schemas.extract_info_schema import (
    ExtractInfoRequest,
    ExtractInfoResponse,
    BookingStateData,
)
from api.services.extract_info_service import call_openai
from api.services.openai_service import OpenAIService
from api.schemas.extract_info_schema import Passenger
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

        # Treat booking_state as a dict and safely access fields
        collected = (
            booking_state.get("collected_data", {})
            if isinstance(booking_state, dict)
            else {}
        )
        raw_passengers = (
            booking_state.get("passengers_data", [])
            if isinstance(booking_state, dict)
            else []
        )

        # Convert passenger dicts to Passenger models, mapping keys safely
        passengers_data: list[Passenger] = []
        for p in raw_passengers:
            if not isinstance(p, dict):
                continue
            passengers_data.append(
                Passenger(
                    name=p.get("name", p.get("passenger_name", "")),
                    lastName=p.get("lastName", p.get("last_name", "")),
                    nationalId=p.get("nationalId", p.get("national_id", "")),
                    passportNumber=p.get(
                        "passportNumber", p.get("passport_number", "")
                    ),
                    luggageCount=p.get("luggageCount", p.get("baggage_count", 0)) or 0,
                    passengerType=p.get("passengerType", p.get("passenger_type", "")),
                    gender=p.get("gender", ""),
                )
            )

        # Create response (flight number is now top-level, not per passenger)
        response = BookingStateData(
            origin_airport=collected.get("origin_airport", ""),
            travel_type=collected.get("travel_type", ""),
            travel_date=collected.get("travel_date", ""),
            flight_number=collected.get("flight_number", ""),
            passenger_count=collected.get("passenger_count", ""),
            passengers_data=passengers_data,
            additional_info=collected.get("additional_info", ""),
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
