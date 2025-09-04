#!/usr/bin/env python3
"""
Test script for the updated extract_info service with English conversation data
"""

import requests
import json

BASE_URL = "http://localhost:8000/extractInfo"


def test_extract_info_english():
    """Test the extract_info endpoint with English conversation data"""

    # Sample English conversation that includes the new fields
    sample_conversation = {
        "messages": [
            {
                "id": "1",
                "text": "Hello, I want to book a flight ticket",
                "sender": "CLIENT",
            },
            {
                "id": "2",
                "text": "Please provide the origin airport name.",
                "sender": "AVATAR",
            },
            {"id": "3", "text": "Imam Khomeini", "sender": "CLIENT"},
            {
                "id": "4",
                "text": "Is your flight arriving at the airport or departing?",
                "sender": "AVATAR",
            },
            {"id": "5", "text": "departure", "sender": "CLIENT"},
            {
                "id": "6",
                "text": "Please provide the travel date (Gregorian calendar).",
                "sender": "AVATAR",
            },
            {"id": "7", "text": "August 15, 2024", "sender": "CLIENT"},
            {
                "id": "8",
                "text": "What is the exact number of passengers?",
                "sender": "AVATAR",
            },
            {"id": "9", "text": "2 people", "sender": "CLIENT"},
            {
                "id": "10",
                "text": "Please provide the passenger's full name.",
                "sender": "AVATAR",
            },
            {"id": "11", "text": "Ali Ahmadi", "sender": "CLIENT"},
            {
                "id": "12",
                "text": "Please provide the passenger's national ID.",
                "sender": "AVATAR",
            },
            {"id": "13", "text": "1234567890", "sender": "CLIENT"},
            {
                "id": "14",
                "text": "Please provide the flight number.",
                "sender": "AVATAR",
            },
            {"id": "15", "text": "IR705", "sender": "CLIENT"},
            {
                "id": "16",
                "text": "Please provide the passenger's passport number.",
                "sender": "AVATAR",
            },
            {"id": "17", "text": "A12345678", "sender": "CLIENT"},
            {
                "id": "18",
                "text": "Please provide the number of bags.",
                "sender": "AVATAR",
            },
            {"id": "19", "text": "2 bags", "sender": "CLIENT"},
            {
                "id": "20",
                "text": "Is the passenger an adult or infant?",
                "sender": "AVATAR",
            },
            {"id": "21", "text": "adult", "sender": "CLIENT"},
            {"id": "22", "text": "What is the passenger's gender?", "sender": "AVATAR"},
            {"id": "23", "text": "male", "sender": "CLIENT"},
            {
                "id": "24",
                "text": "Please provide the second passenger's full name.",
                "sender": "AVATAR",
            },
            {"id": "25", "text": "Fatemeh Ahmadi", "sender": "CLIENT"},
            {
                "id": "26",
                "text": "Please provide the second passenger's national ID.",
                "sender": "AVATAR",
            },
            {"id": "27", "text": "0987654321", "sender": "CLIENT"},
            {
                "id": "28",
                "text": "Please provide the second passenger's flight number.",
                "sender": "AVATAR",
            },
            {"id": "29", "text": "IR705", "sender": "CLIENT"},
            {
                "id": "30",
                "text": "Please provide the second passenger's passport number.",
                "sender": "AVATAR",
            },
            {"id": "31", "text": "B87654321", "sender": "CLIENT"},
            {
                "id": "32",
                "text": "Please provide the second passenger's number of bags.",
                "sender": "AVATAR",
            },
            {"id": "33", "text": "1 bag", "sender": "CLIENT"},
            {
                "id": "34",
                "text": "Is the second passenger an adult or infant?",
                "sender": "AVATAR",
            },
            {"id": "35", "text": "adult", "sender": "CLIENT"},
            {
                "id": "36",
                "text": "What is the second passenger's gender?",
                "sender": "AVATAR",
            },
            {"id": "37", "text": "female", "sender": "CLIENT"},
            {
                "id": "38",
                "text": "Any additional information you would like to provide?",
                "sender": "AVATAR",
            },
            {"id": "39", "text": "We need a wheelchair", "sender": "CLIENT"},
        ]
    }

    try:
        print("Testing extract_info endpoint with English conversation...")
        print("=" * 60)

        response = requests.post(
            f"{BASE_URL}/extract-info", json=sample_conversation, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Extracted information:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # Validate the structure
            print("\n" + "=" * 60)
            print("Validating extracted data structure...")

            required_fields = [
                "airportName",
                "travelType",
                "travelDate",
                "passengerCount",
                "flightNumber",
                "passengers",
                "additionalInfo",
            ]
            for field in required_fields:
                if field in result:
                    print(f"✅ {field}: {result[field]}")
                else:
                    print(f"❌ Missing field: {field}")

            # Validate passenger information
            if "passengers" in result and isinstance(result["passengers"], list):
                print(f"\n✅ Found {len(result['passengers'])} passengers")
                for i, passenger in enumerate(result["passengers"], 1):
                    print(f"\nPassenger {i}:")
                    passenger_fields = [
                        "name",
                        "lastName",
                        "nationalId",
                        "passportNumber",
                        "luggageCount",
                        "passengerType",
                        "gender",
                    ]
                    for field in passenger_fields:
                        if field in passenger:
                            print(f"  ✅ {field}: {passenger[field]}")
                        else:
                            print(f"  ❌ Missing field: {field}")
            else:
                print("❌ No passengers found or invalid format")

        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_extract_info_english()
