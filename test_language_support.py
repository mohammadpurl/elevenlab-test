#!/usr/bin/env python3
"""
Test script to demonstrate the language support functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/assistant"


def test_chat_endpoint(message, language="fa", session_id=None):
    """Test the chat endpoint with different languages"""
    data = {"message": message, "language": language}
    if session_id:
        data["session_id"] = session_id

    try:
        response = requests.post(f"{BASE_URL}/chat", json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def test_persian_flow():
    """Test the Persian language flow"""
    print("=" * 50)
    print("Testing Persian Language Flow")
    print("=" * 50)

    # Test 1: Initial greeting in Persian
    print("\n1. Testing initial greeting in Persian...")
    result = test_chat_endpoint("سلام", "fa")
    if result:
        print(f"Response: {result['messages'][0]['text']}")
        session_id = result["session_id"]
        print(f"Session ID: {session_id}")

    # Test 2: Provide airport name
    print("\n2. Providing airport name...")
    result = test_chat_endpoint("امام خمینی", "fa", session_id)
    if result:
        print(f"Response: {result['messages'][0]['text']}")

    # Test 3: Provide travel type
    print("\n3. Providing travel type...")
    result = test_chat_endpoint("خروجی", "fa", session_id)
    if result:
        print(f"Response: {result['messages'][0]['text']}")


def test_english_flow():
    """Test the English language flow"""
    print("\n" + "=" * 50)
    print("Testing English Language Flow")
    print("=" * 50)

    # Test 1: Initial greeting in English
    print("\n1. Testing initial greeting in English...")
    result = test_chat_endpoint("Hello", "en")
    if result:
        print(f"Response: {result['messages'][0]['text']}")
        session_id = result["session_id"]
        print(f"Session ID: {session_id}")

    # Test 2: Provide airport name
    print("\n2. Providing airport name...")
    result = test_chat_endpoint("Imam Khomeini", "en", session_id)
    if result:
        print(f"Response: {result['messages'][0]['text']}")

    # Test 3: Provide travel type
    print("\n3. Providing travel type...")
    result = test_chat_endpoint("departure", "en", session_id)
    if result:
        print(f"Response: {result['messages'][0]['text']}")


def test_health_endpoint():
    """Test the health endpoint"""
    print("=" * 50)
    print("Testing Health Endpoint")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"Health check: {response.json()}")
        else:
            print(f"Health check failed: {response.status_code}")
    except Exception as e:
        print(f"Health check failed: {e}")


if __name__ == "__main__":
    print("Starting language support tests...")

    # Test health endpoint first
    test_health_endpoint()

    # Test Persian flow
    test_persian_flow()

    # Test English flow
    test_english_flow()

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)
