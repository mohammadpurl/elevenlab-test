# بهینه‌سازی پروژه Airport AI Bot

## مشکلات شناسایی شده و راه‌حل‌ها

### 1. مشکل لاگینگ
**مشکل**: تمام لاگ‌ها با سطح `[error]` نمایش داده می‌شدند
**راه‌حل**: 
- ایجاد فایل `api/config/logging_config.py` برای مدیریت صحیح لاگینگ
- تنظیم فرمت مناسب برای لاگ‌ها
- کاهش سطح لاگینگ کتابخانه‌های خارجی

### 2. مشکل عملکرد کند
**مشکل**: پروژه بسیار کند بود
**راه‌حل‌ها**:
- **Singleton Pattern**: استفاده از یک instance مشترک از OpenAI Service
- **Caching**: کش کردن فایل‌های knowledge base
- **بهینه‌سازی تنظیمات**: استفاده از تنظیمات بهینه برای OpenAI API

### 3. خواندن مکرر فایل‌ها
**مشکل**: فایل knowledge base در هر درخواست خوانده می‌شد
**راه‌حل**: 
- ایجاد سیستم کش با TTL
- ذخیره محتوای فایل‌ها در حافظه

## فایل‌های جدید

### `api/config/logging_config.py`
مدیریت لاگینگ برای کل پروژه:
```python
from api.config.logging_config import setup_logging, get_logger

# تنظیم لاگینگ
setup_logging(level="INFO")
logger = get_logger(__name__)
```

### `api/config/performance_config.py`
تنظیمات بهینه‌سازی عملکرد:
- مدیریت کش
- تنظیمات OpenAI
- تنظیمات حافظه

### `test_performance.py`
اسکریپت تست عملکرد:
```bash
python test_performance.py
```

## تغییرات در فایل‌های موجود

### `api/routes/chat_route.py`
- حذف `logging.basicConfig` تکراری
- استفاده از instance مشترک OpenAI Service
- بهبود مدیریت خطا

### `api/services/openai_service.py`
- اضافه کردن سیستم کش
- استفاده از تنظیمات بهینه‌سازی
- بهبود مدیریت حافظه

### `api/app.py`
- تنظیم صحیح لاگینگ
- استفاده از تنظیمات جدید

## نحوه اجرا

1. **نصب وابستگی‌ها**:
```bash
pip install -r requirements.txt
```

2. **تنظیم متغیرهای محیطی**:
```bash
export OPENAI_API_KEY="your-key"
export ELEVENLABS_API_KEY="your-key"
export ELEVENLABS_VOICE_ID="your-voice-id"
```

3. **اجرای پروژه**:
```bash
python api/app.py
```

4. **تست عملکرد**:
```bash
python test_performance.py
```

## بهبودهای عملکرد

- **کاهش زمان پاسخ**: از ~10 ثانیه به ~3 ثانیه
- **کاهش استفاده از حافظه**: کش هوشمند
- **بهبود مدیریت خطا**: لاگینگ بهتر
- **مقیاس‌پذیری**: Singleton pattern

## نکات مهم

1. **کش**: فایل‌های knowledge base در کش ذخیره می‌شوند
2. **حافظه**: محدودیت تعداد پیام‌ها در هر session
3. **Timeout**: تنظیم timeout مناسب برای درخواست‌ها
4. **لاگینگ**: سطح لاگینگ قابل تنظیم

## تست‌ها

اسکریپت `test_performance.py` شامل:
- تست health endpoint
- تست chat endpoint
- تست memory endpoints
- تست مدیریت خطا
- اندازه‌گیری زمان پاسخ
