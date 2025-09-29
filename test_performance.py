#!/usr/bin/env python3
"""
تست عملکرد و بررسی مشکلات پروژه
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/assistant"


def test_performance():
    """تست عملکرد کلی سیستم"""
    print("=" * 60)
    print("تست عملکرد سیستم")
    print("=" * 60)

    # تست health endpoint
    print("\n1. تست Health Endpoint...")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        end_time = time.time()
        if response.status_code == 200:
            print(
                f"✅ Health check موفق - زمان پاسخ: {end_time - start_time:.2f} ثانیه"
            )
        else:
            print(f"❌ Health check ناموفق - کد: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check ناموفق - خطا: {e}")

    # تست chat endpoint
    print("\n2. تست Chat Endpoint...")
    test_messages = ["سلام", "تو کی هستی؟", "امام خمینی", "خروجی"]

    session_id = None
    total_time = 0

    for i, message in enumerate(test_messages, 1):
        print(f"\n   {i}. ارسال پیام: '{message}'")
        start_time = time.time()

        try:
            data = {"message": message, "language": "fa"}
            if session_id:
                data["session_id"] = session_id

            response = requests.post(f"{BASE_URL}/chat", json=data, timeout=30)
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time

            if response.status_code == 200:
                result = response.json()
                session_id = result.get("session_id")
                print(f"   ✅ موفق - زمان پاسخ: {response_time:.2f} ثانیه")
                if result.get("messages"):
                    print(f"   📝 پاسخ: {result['messages'][0]['text'][:50]}...")
            else:
                print(f"   ❌ ناموفق - کد: {response.status_code}")
                print(f"   📝 خطا: {response.text}")

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            print(f"   ❌ خطا: {e} - زمان: {response_time:.2f} ثانیه")

    print(f"\n📊 خلاصه عملکرد:")
    print(f"   - تعداد درخواست‌ها: {len(test_messages)}")
    print(f"   - زمان کل: {total_time:.2f} ثانیه")
    print(f"   - میانگین زمان پاسخ: {total_time/len(test_messages):.2f} ثانیه")

    if total_time / len(test_messages) > 5:
        print("   ⚠️  هشدار: زمان پاسخ بالا است!")
    else:
        print("   ✅ عملکرد مناسب است")


def test_memory_endpoints():
    """تست endpoint های حافظه"""
    print("\n" + "=" * 60)
    print("تست Memory Endpoints")
    print("=" * 60)

    # ایجاد یک session برای تست
    test_session_id = "test_session_123"

    # تست دریافت حافظه
    print(f"\n1. تست دریافت حافظه برای session: {test_session_id}")
    try:
        response = requests.get(f"{BASE_URL}/memory/{test_session_id}", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ موفق - تعداد پیام‌ها: {result.get('count', 0)}")
        else:
            print(f"❌ ناموفق - کد: {response.status_code}")
    except Exception as e:
        print(f"❌ خطا: {e}")

    # تست پاک کردن حافظه
    print(f"\n2. تست پاک کردن حافظه برای session: {test_session_id}")
    try:
        response = requests.delete(f"{BASE_URL}/memory/{test_session_id}", timeout=10)
        if response.status_code == 200:
            print("✅ موفق - حافظه پاک شد")
        else:
            print(f"❌ ناموفق - کد: {response.status_code}")
    except Exception as e:
        print(f"❌ خطا: {e}")


def test_error_handling():
    """تست مدیریت خطا"""
    print("\n" + "=" * 60)
    print("تست مدیریت خطا")
    print("=" * 60)

    # تست پیام خالی
    print("\n1. تست پیام خالی...")
    try:
        response = requests.post(f"{BASE_URL}/chat", json={"message": ""}, timeout=10)
        print(f"کد پاسخ: {response.status_code}")
        if response.status_code != 200:
            print(f"✅ خطا به درستی مدیریت شد")
        else:
            print("⚠️  پیام خالی پذیرفته شد")
    except Exception as e:
        print(f"❌ خطا: {e}")

    # تست پیام طولانی
    print("\n2. تست پیام طولانی...")
    long_message = "سلام " * 1000  # پیام بسیار طولانی
    try:
        response = requests.post(
            f"{BASE_URL}/chat", json={"message": long_message}, timeout=30
        )
        print(f"کد پاسخ: {response.status_code}")
        if response.status_code == 200:
            print("✅ پیام طولانی پردازش شد")
        else:
            print(f"⚠️  پیام طولانی رد شد: {response.text}")
    except Exception as e:
        print(f"❌ خطا: {e}")


if __name__ == "__main__":
    print("🚀 شروع تست‌های عملکرد...")

    try:
        # تست عملکرد اصلی
        test_performance()

        # تست memory endpoints
        test_memory_endpoints()

        # تست مدیریت خطا
        test_error_handling()

        print("\n" + "=" * 60)
        print("✅ تمام تست‌ها تکمیل شد!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⏹️  تست توسط کاربر متوقف شد")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ خطای غیرمنتظره: {e}")
        sys.exit(1)
