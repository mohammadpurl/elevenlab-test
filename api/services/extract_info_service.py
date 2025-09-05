import os
import httpx
import json
import logging
from typing import List
from api.schemas.extract_info_schema import ExtractInfoRequest

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


async def call_openai(messages: ExtractInfoRequest):
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set")
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    prompt = (
        "Extract all passenger and ticket information from the following conversation for an airline booking. "
        "Return a JSON object with these fields:\n"
        "{\n"
        '  "airportName": string,\n'
        '  "travelType": string (either "arrival" or "departure"),\n'
        '  "travelDate": string,\n'
        '  "passengerCount": number,\n'
        '  "flightNumber": string,\n'
        '  "passengers": [\n'
        "    {\n"
        '      "name": string,\n'
        '      "lastName": string,\n'
        '      "nationalId": string,\n'
        '      "passportNumber": string,\n'
        '      "luggageCount": number,\n'
        '      "passengerType": string (either "adult" or "infant"),\n'
        '      "gender": string\n'
        "    }\n"
        "  ],\n"
        '  "additionalInfo": string (optional)\n'
        "}\n"
        "Important: Extract information for each passenger separately. Each passenger should have their own complete set of information.\n"
        "If the flight number contains letters that were spoken or written using Persian letters (e.g., 'کیو آر'), convert them to English Latin letters (e.g., 'QR'). Also normalize any Persian/Arabic digits to Western digits. Return the normalized flight number (uppercase, no spaces or hyphens).\n"
        "If any field is missing, use an empty string or 0. Only return the JSON object, nothing else.\n\n"
        "Conversation:\n"
        + "\n".join(f"{m.sender}: {m.text}" for m in messages.messages)
    )

    logger.info(f"Processing {len(messages.messages)} messages with OpenAI")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert information extraction assistant for airline ticket bookings. Your task is to carefully analyze conversations and extract structured booking information including passenger details, flight information, and travel preferences. Be thorough and accurate in your extraction.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENAI_API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            text = result["choices"][0]["message"]["content"]

            logger.info(f"OpenAI response: {text}")

            try:
                print("extract_info_service", text)
                extracted = json.loads(text)

                # Normalize flight number: convert Persian/Arabic digits, uppercase, remove spaces/hyphens
                def normalize_flight_number(value: str) -> str:
                    if not isinstance(value, str):
                        return ""
                    # Map Persian and Arabic-Indic digits to Western digits
                    digit_map = str.maketrans(
                        {
                            "۰": "0",
                            "۱": "1",
                            "۲": "2",
                            "۳": "3",
                            "۴": "4",
                            "۵": "5",
                            "۶": "6",
                            "۷": "7",
                            "۸": "8",
                            "۹": "9",
                            "٠": "0",
                            "١": "1",
                            "٢": "2",
                            "٣": "3",
                            "٤": "4",
                            "٥": "5",
                            "٦": "6",
                            "٧": "7",
                            "٨": "8",
                            "٩": "9",
                        }
                    )
                    normalized = value.translate(digit_map)
                    normalized = normalized.replace(" ", "").replace("-", "").upper()
                    return normalized

                if isinstance(extracted, dict) and "flightNumber" in extracted:
                    extracted["flightNumber"] = normalize_flight_number(
                        extracted.get("flightNumber", "")
                    )

                return extracted
            except json.JSONDecodeError:
                import re

                match = re.search(r"\{[\s\S]*\}", text)
                if match:
                    extracted = json.loads(match.group(0))

                    def normalize_flight_number(value: str) -> str:
                        if not isinstance(value, str):
                            return ""
                        digit_map = str.maketrans(
                            {
                                "۰": "0",
                                "۱": "1",
                                "۲": "2",
                                "۳": "3",
                                "۴": "4",
                                "۵": "5",
                                "۶": "6",
                                "۷": "7",
                                "۸": "8",
                                "۹": "9",
                                "٠": "0",
                                "١": "1",
                                "٢": "2",
                                "٣": "3",
                                "٤": "4",
                                "٥": "5",
                                "٦": "6",
                                "٧": "7",
                                "٨": "8",
                                "٩": "9",
                            }
                        )
                        normalized = value.translate(digit_map)
                        normalized = (
                            normalized.replace(" ", "").replace("-", "").upper()
                        )
                        return normalized

                    if isinstance(extracted, dict) and "flightNumber" in extracted:
                        extracted["flightNumber"] = normalize_flight_number(
                            extracted.get("flightNumber", "")
                        )

                    return extracted
                raise ValueError("Failed to parse OpenAI response")

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
        raise ValueError(f"OpenAI API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error calling OpenAI: {str(e)}")
        raise ValueError(f"Error calling OpenAI: {str(e)}")
