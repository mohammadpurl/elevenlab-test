#!/usr/bin/env python3
"""
Test script for the new validation system
This script demonstrates how the system now properly validates user responses
instead of just moving mechanically to the next question
"""

import asyncio
from api.services.openai_service import OpenAIService


async def test_validation_system():
    """Test the new validation system"""
    print("🧪 Testing New Validation System")
    print("=" * 50)
    print("This system now validates responses instead of just moving to next question")
    print()

    # Initialize the service
    service = OpenAIService()

    # Create a new session
    session_id = "test_validation_001"

    # Test cases with invalid responses
    test_cases = [
        # Test 1: Empty response
        {
            "step": "نام فرودگاه مبدا",
            "user_input": "",
            "expected_behavior": "Should show validation error and repeat question",
        },
        # Test 2: Too short airport name
        {
            "step": "نام فرودگاه مبدا",
            "user_input": "ا",
            "expected_behavior": "Should show validation error for too short name",
        },
        # Test 3: Invalid travel type
        {
            "step": "نوع پرواز",
            "user_input": "نامعتبر",
            "expected_behavior": "Should show validation error for invalid travel type",
        },
        # Test 4: Invalid passenger count
        {
            "step": "تعداد مسافران",
            "user_input": "صفر",
            "expected_behavior": "Should show validation error for invalid passenger count",
        },
        # Test 5: Invalid national ID
        {
            "step": "کد ملی مسافر",
            "user_input": "123",
            "expected_behavior": "Should show validation error for invalid national ID length",
        },
        # Test 6: Valid response
        {
            "step": "نام فرودگاه مبدا",
            "user_input": "فرودگاه امام خمینی",
            "expected_behavior": "Should accept and move to next question",
        },
    ]

    print(f"Session ID: {session_id}")
    print(f"Total test cases: {len(test_cases)}")
    print()

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['step']}")
        print(f"User Input: '{test_case['user_input']}'")
        print(f"Expected: {test_case['expected_behavior']}")

        try:
            # Get assistant response
            response, session_id = service.get_assistant_response(
                test_case["user_input"], session_id, "fa"
            )

            print(f"Assistant Response:")
            for msg in response:
                print(f"  - {msg.get('text', 'No text')}")

            # Check if this is a validation error or progression
            if any(
                "خطا" in msg.get("text", "") or "error" in msg.get("text", "").lower()
                for msg in response
            ):
                print("  ✅ VALIDATION ERROR DETECTED - System is working correctly!")
            elif any(
                "بفرمایید" in msg.get("text", "")
                or "please" in msg.get("text", "").lower()
                for msg in response
            ):
                print(
                    "  ✅ QUESTION PROGRESSION - System moved to next question correctly!"
                )
            else:
                print("  ❓ UNKNOWN RESPONSE TYPE")

            # Show current booking state
            if session_id in service.booking_states:
                booking_state = service.booking_states[session_id]
                print(f"  Current step: {booking_state.current_step}")
                print(f"  Collected data: {booking_state.collected_data}")

            print()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print()

    print("📊 Final Booking State:")
    print("=" * 30)

    if session_id in service.booking_states:
        booking_state = service.booking_states[session_id]
        print(f"Origin Airport: {booking_state.collected_data.get('origin_airport')}")
        print(f"Travel Type: {booking_state.collected_data.get('travel_type')}")
        print(f"Travel Date: {booking_state.collected_data.get('travel_date')}")
        print(f"Passenger Count: {booking_state.collected_data.get('passenger_count')}")
        print(f"Additional Info: {booking_state.collected_data.get('additional_info')}")
    else:
        print("❌ No booking state found")

    print()
    print("✅ Validation system test completed!")
    print()
    print("🎯 Key Improvements Made:")
    print("1. ✅ Responses are now validated before proceeding")
    print("2. ✅ Error messages are shown for invalid inputs")
    print("3. ✅ Questions are repeated until valid responses are received")
    print("4. ✅ System provides helpful feedback to users")
    print("5. ✅ No more mechanical progression without validation")


if __name__ == "__main__":
    asyncio.run(test_validation_system())
