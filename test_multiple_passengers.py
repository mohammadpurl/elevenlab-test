#!/usr/bin/env python3
"""
Test script for multiple passenger functionality
This script simulates a conversation flow to test if the system properly handles multiple passengers
"""

import asyncio
import json
from api.services.openai_service import OpenAIService


async def test_multiple_passengers():
    """Test the multiple passenger functionality"""
    print("🧪 Testing Multiple Passenger Functionality")
    print("=" * 50)

    # Initialize the service
    service = OpenAIService()

    # Create a new session
    session_id = "test_multiple_passengers_001"

    # Simulate conversation flow
    conversation_steps = [
        "فرودگاه امام خمینی",
        "خروجی",
        "۱۵ آگوست ۲۰۲۴",
        "۲ نفر",
        "احمد محمدی",  # Passenger 1 name
        "۱۲۳۴۵۶۷۸۹۰",  # Passenger 1 national ID
        "IR123",  # Passenger 1 flight number
        "A12345678",  # Passenger 1 passport
        "۲",  # Passenger 1 baggage count
        "بزرگسال",  # Passenger 1 type
        "مرد",  # Passenger 1 gender
        "علی احمدی",  # Passenger 2 name
        "۰۹۸۷۶۵۴۳۲۱",  # Passenger 2 national ID
        "IR123",  # Passenger 2 flight number
        "B87654321",  # Passenger 2 passport
        "۱",  # Passenger 2 baggage count
        "بزرگسال",  # Passenger 2 type
        "مرد",  # Passenger 2 gender
        "هیچ توضیح اضافه‌ای ندارم",
    ]

    print(f"Session ID: {session_id}")
    print(f"Total conversation steps: {len(conversation_steps)}")
    print()

    for i, user_message in enumerate(conversation_steps, 1):
        print(f"Step {i}: User says: {user_message}")

        try:
            # Get assistant response
            response, session_id = service.get_assistant_response(
                user_message, session_id, "fa"
            )

            print(f"Assistant response:")
            for msg in response:
                print(f"  - {msg.get('text', 'No text')}")

            # Check booking state
            if session_id in service.booking_states:
                booking_state = service.booking_states[session_id]
                print(f"  Current step: {booking_state.current_step}")
                print(f"  Passenger count: {booking_state.passenger_count}")
                print(
                    f"  Current passenger: {booking_state.get_current_passenger_number()}"
                )
                print(
                    f"  Passengers data: {len(booking_state.passengers_data)} passengers"
                )

                # Show collected data for each passenger
                for j, passenger_data in enumerate(booking_state.passengers_data):
                    print(f"    Passenger {j+1}: {passenger_data}")

            print()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print()

    # Final check - get booking state
    print("📊 Final Booking State:")
    print("=" * 30)

    if session_id in service.booking_states:
        booking_state = service.booking_states[session_id]
        print(f"Origin Airport: {booking_state.collected_data.get('origin_airport')}")
        print(f"Travel Type: {booking_state.collected_data.get('travel_type')}")
        print(f"Travel Date: {booking_state.collected_data.get('travel_date')}")
        print(f"Passenger Count: {booking_state.collected_data.get('passenger_count')}")
        print(f"Additional Info: {booking_state.collected_data.get('additional_info')}")
        print()

        print("Passenger Details:")
        for i, passenger_data in enumerate(booking_state.passengers_data):
            print(f"  Passenger {i+1}:")
            for key, value in passenger_data.items():
                print(f"    {key}: {value}")
            print()
    else:
        print("❌ No booking state found")

    print("✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_multiple_passengers())
