"""
مدیریت کش و تنظیمات بهینه‌سازی برای پروژه
"""

import os
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class CacheManager:
    """مدیریت کش برای بهبود عملکرد"""

    def __init__(self, default_ttl: int = 3600):  # 1 ساعت
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """دریافت مقدار از کش"""
        with self._lock:
            if key not in self._cache:
                return None

            cache_item = self._cache[key]
            if datetime.now() > cache_item["expires_at"]:
                del self._cache[key]
                return None

            return cache_item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """ذخیره مقدار در کش"""
        with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            self._cache[key] = {"value": value, "expires_at": expires_at}

    def clear(self, key: Optional[str] = None) -> None:
        """پاک کردن کش"""
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    def cleanup_expired(self) -> None:
        """پاک کردن آیتم‌های منقضی شده"""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, item in self._cache.items() if now > item["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]


# Instance مشترک برای کل پروژه
cache_manager = CacheManager()


class PerformanceConfig:
    """تنظیمات بهینه‌سازی عملکرد"""

    # تنظیمات OpenAI
    OPENAI_TIMEOUT = 60
    OPENAI_MAX_TOKENS = 2000
    OPENAI_TEMPERATURE = 0.7

    # تنظیمات کش
    KNOWLEDGE_BASE_CACHE_TTL = 3600  # 1 ساعت
    SESSION_CACHE_TTL = 1800  # 30 دقیقه

    # تنظیمات حافظه
    MAX_MEMORY_MESSAGES = 20
    MAX_SESSIONS = 1000

    @classmethod
    def get_openai_config(cls) -> Dict[str, Any]:
        """دریافت تنظیمات OpenAI"""
        return {
            "timeout": cls.OPENAI_TIMEOUT,
            "max_tokens": cls.OPENAI_MAX_TOKENS,
            "temperature": cls.OPENAI_TEMPERATURE,
        }


# تنظیمات محیطی
def get_env_config() -> Dict[str, str]:
    """دریافت تنظیمات محیطی"""
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY", ""),
        "elevenlabs_voice_id": os.getenv("ELEVENLABS_VOICE_ID", ""),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }
