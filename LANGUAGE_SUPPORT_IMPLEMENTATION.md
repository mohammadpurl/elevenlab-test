# Language Support Implementation

## Overview
This document describes the implementation of multi-language support for the airport AI assistant chatbot. The system now supports both Persian (fa) and English (en) languages.

## Changes Made

### 1. Schema Updates (`api/schemas/chat_schema.py`)
- Added `language` field to `ChatRequest` model
- Default value is "fa" (Persian)
- Accepts "fa" or "en" values

### 2. Service Updates (`api/services/openai_service.py`)
- Modified `get_assistant_response` method to accept `language` parameter
- Added language-specific knowledge base loading
- Updated system prompts for both languages
- Modified question text mapping for both languages
- Updated error messages to be language-aware
- Added language parameter to internal helper methods

### 3. Route Updates (`api/routes/chat_route.py`)
- Modified `/chat` endpoint to extract language from request
- Passes language parameter to OpenAI service

### 4. Knowledge Base Files
- **Persian**: `api/constants/knowledge_base.txt` (existing, updated)
- **English**: `api/constants/knowledge_base_en.txt` (new)

## New Booking Flow

The updated system now collects the following information in order:

1. **Origin Airport Name** (نام فرودگاه مبدا)
2. **Travel Type** (نوع پرواز - ورودی/خروجی)
3. **Travel Date** (تاریخ سفر - میلادی)
4. **Passenger Count** (تعداد مسافران)
5. **For each passenger separately:**
   - Passenger Name (نام مسافر)
   - National ID (کد ملی)
   - Flight Number (شماره پرواز)
   - Passport Number (شماره گذرنامه)
   - Baggage Count (تعداد چمدان)
   - Passenger Type (نوع مسافر - بزرگسال/نوزاد)
   - Gender (جنسیت)
6. **Additional Information** (توضیح اضافه)

## Language-Specific Features

### Persian (fa)
- Uses Persian knowledge base
- Persian system prompts
- Persian question texts
- Persian error messages
- Persian completion messages

### English (en)
- Uses English knowledge base
- English system prompts
- English question texts
- English error messages
- English completion messages

## API Usage

### Request Format
```json
{
  "message": "Hello",
  "language": "en",
  "session_id": "optional-session-id"
}
```

### Response Format
```json
{
  "messages": [
    {
      "text": "Please provide the origin airport name.",
      "facialExpression": "default",
      "animation": "Talking_0"
    }
  ],
  "session_id": "generated-session-id"
}
```

## Testing

A test script (`test_language_support.py`) is provided to verify:
- Health endpoint functionality
- Persian language flow
- English language flow
- Session management
- Multi-step conversation flow

## Key Benefits

1. **Multi-language Support**: Users can interact in their preferred language
2. **Consistent Experience**: Same functionality available in both languages
3. **Localized Content**: All messages, questions, and responses are properly localized
4. **Backward Compatibility**: Existing Persian functionality remains unchanged
5. **Extensible**: Easy to add more languages in the future

## Future Enhancements

1. **Additional Languages**: Can easily add more language support
2. **Language Detection**: Automatic language detection based on user input
3. **Mixed Language Support**: Allow users to switch languages mid-conversation
4. **Localized Knowledge Bases**: Country-specific information for different regions

## Technical Notes

- Language parameter is passed through the entire request chain
- Knowledge base files are loaded based on language parameter
- System prompts are dynamically generated based on language
- Question texts are mapped to appropriate language
- Error handling includes language-specific messages
- Session management works across both languages
