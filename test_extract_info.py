#!/usr/bin/env python3
"""
Test script for the updated extract_info service
"""

import requests
import json

BASE_URL = "http://localhost:8000/extractInfo"


def test_extract_info():
    """Test the extract_info endpoint with sample conversation data"""

    # Sample conversation that includes the new fields
    sample_conversation = {
        "messages": [
            {
                "id": "1",
                "text": "سلام، می‌خوام بلیط هواپیما رزرو کنم",
                "sender": "CLIENT",
            },
            {"id": "2", "text": "نام فرودگاه مبدا رو بفرمایید.", "sender": "AVATAR"},
            {"id": "3", "text": "امام خمینی", "sender": "CLIENT"},
            {
                "id": "4",
                "text": "پروازتون ورودی به فرودگاهه یا خروجی؟",
                "sender": "AVATAR",
            },
            {"id": "5", "text": "خروجی", "sender": "CLIENT"},
            {"id": "6", "text": "تاریخ سفر رو به میلادی بفرمایید.", "sender": "AVATAR"},
            {"id": "7", "text": "۱۵ آگوست ۲۰۲۴", "sender": "CLIENT"},
            {"id": "8", "text": "تعداد دقیق مسافران چند نفر است؟", "sender": "AVATAR"},
            {"id": "9", "text": "۲ نفر", "sender": "CLIENT"},
            {
                "id": "10",
                "text": "نام و نام خانوادگی مسافر رو بفرمایید.",
                "sender": "AVATAR",
            },
            {"id": "11", "text": "علی احمدی", "sender": "CLIENT"},
            {"id": "12", "text": "کد ملی مسافر رو بفرمایید.", "sender": "AVATAR"},
            {"id": "13", "text": "۱۲۳۴۵۶۷۸۹۰", "sender": "CLIENT"},
            {"id": "14", "text": "شماره پرواز رو بفرمایید.", "sender": "AVATAR"},
            {"id": "15", "text": "IR۷۰۵", "sender": "CLIENT"},
            {
                "id": "16",
                "text": "شماره گذرنامه مسافر رو بفرمایید.",
                "sender": "AVATAR",
            },
            {"id": "17", "text": "A۱۲۳۴۵۶۷۸", "sender": "CLIENT"},
            {"id": "18", "text": "تعداد چمدان‌ها رو بفرمایید.", "sender": "AVATAR"},
            {"id": "19", "text": "۲ تا", "sender": "CLIENT"},
            {"id": "20", "text": "نوع مسافر بزرگسال است یا نوزاد؟", "sender": "AVATAR"},
            {"id": "21", "text": "بزرگسال", "sender": "CLIENT"},
            {"id": "22", "text": "جنسیت مسافر چیه؟", "sender": "AVATAR"},
            {"id": "23", "text": "مرد", "sender": "CLIENT"},
            {
                "id": "24",
                "text": "نام و نام خانوادگی مسافر دوم رو بفرمایید.",
                "sender": "AVATAR",
            },
            {"id": "25", "text": "فاطمه احمدی", "sender": "CLIENT"},
            {"id": "26", "text": "کد ملی مسافر دوم رو بفرمایید.", "sender": "AVATAR"},
            {"id": "27", "text": "۰۹۸۷۶۵۴۳۲۱", "sender": "CLIENT"},
            {
                "id": "28",
                "text": "شماره پرواز مسافر دوم رو بفرمایید.",
                "sender": "AVATAR",
            },
            {"id": "29", "text": "IR۷۰۵", "sender": "CLIENT"},
            {
                "id": "30",
                "text": "شماره گذرنامه مسافر دوم رو بفرمایید.",
                "sender": "AVATAR",
            },
            {"id": "31", "text": "B۸۷۶۵۴۳۲۱", "sender": "CLIENT"},
            {
                "id": "32",
                "text": "تعداد چمدان‌های مسافر دوم رو بفرمایید.",
                "sender": "AVATAR",
            },
            {"id": "33", "text": "۱ تا", "sender": "CLIENT"},
            {
                "id": "34",
                "text": "نوع مسافر دوم بزرگسال است یا نوزاد؟",
                "sender": "AVATAR",
            },
            {"id": "35", "text": "بزرگسال", "sender": "CLIENT"},
            {"id": "36", "text": "جنسیت مسافر دوم چیه؟", "sender": "AVATAR"},
            {"id": "37", "text": "زن", "sender": "CLIENT"},
            {"id": "38", "text": "توضیح اضافه‌ای که می‌خواید بگید؟", "sender": "AVATAR"},
            {"id": "39", "text": "نیاز به ویلچر داریم", "sender": "CLIENT"},
        ]
    }

    try:
        print("Testing extract_info endpoint...")
        print("=" * 50)

        response = requests.post(
            f"{BASE_URL}/extract-info", json=sample_conversation, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Extracted information:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # Validate the structure
            print("\n" + "=" * 50)
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
    test_extract_info()
