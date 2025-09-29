"""
تنظیمات لاگینگ برای پروژه
"""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    تنظیم لاگینگ برای کل پروژه

    Args:
        level: سطح لاگینگ (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: مسیر فایل لاگ (اختیاری)
    """
    # فرمت لاگ
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # تنظیمات handler ها
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    # تنظیم لاگینگ اصلی
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers,
        force=True,  # بازنویسی تنظیمات قبلی
    )

    # تنظیم لاگینگ برای کتابخانه‌های خارجی
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # لاگ شروع
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {level}")


def get_logger(name: str) -> logging.Logger:
    """
    دریافت logger برای ماژول مشخص

    Args:
        name: نام ماژول (معمولاً __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
