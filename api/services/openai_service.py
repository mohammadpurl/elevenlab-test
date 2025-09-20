import os
import json
import logging
import requests
import uuid
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentMemory:
    """Memory system for the agent to maintain conversation history"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.conversations: Dict[str, List[Dict]] = {}

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        self.conversations[session_id].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if len(self.conversations[session_id]) > self.max_messages:
            self.conversations[session_id] = self.conversations[session_id][
                -self.max_messages :
            ]

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        return self.conversations.get(session_id, [])

    def clear_conversation(self, session_id: str):
        if session_id in self.conversations:
            del self.conversations[session_id]


class OpenAIService:
    _instance = None
    _memory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAIService, cls).__new__(cls)
            cls._memory = AgentMemory()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                logger.error("OPENAI_API_KEY not set")
                raise ValueError("OPENAI_API_KEY environment variable is not set")

            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.memory = OpenAIService._memory
            self.booking_states: Dict[str, dict] = {}
            self.initialized = True

    def get_assistant_response(
        self, user_message: str, session_id: Optional[str] = None, language: str = "fa"
    ):
        if session_id is None:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Load knowledge base based on language
        knowledge_base_file = (
            "api/constants/knowledge_base_en.txt"
            if language == "en"
            else "api/constants/knowledge_base.txt"
        )
        with open(knowledge_base_file, "r", encoding="utf-8") as f:
            knowledge_base = f.read()

        # Create intelligent system prompt that lets AI handle everything
        if language == "en":
            system_prompt = f"""
You are an AI assistant named "Binad" who provides airport services at Imam Khomeini and Mashhad airports.

# Your Intelligence:
You are INTELLIGENT and can handle complex conversations on your own. You don't need step-by-step instructions - you understand the logic and can make decisions.

# Core Responsibilities:
- Handle flight ticket bookings with multiple passengers
- Collect and validate all required information
- Manage conversation flow intelligently
- Provide helpful error messages and guidance
- Generate QR codes for final confirmation
- Ask for and validate a contact phone number for the booking
- Ask for and validate passenger nationality

# How You Work:
1. **Understand the context** from the knowledge base
2. **Make intelligent decisions** about what to ask next
3. **Validate responses** yourself using common sense
4. **Handle multiple passengers** by tracking conversation state
5. **Provide helpful feedback** for invalid inputs
6. **Progress naturally** through the conversation

# Response Format:
Always respond with a JSON array of messages:
{{
  "messages": [
    {{
      "text": "Your message here",
      "facialExpression": "smile|sad|angry|surprised|funnyFace|default",
      "animation": "Talking_0|Talking_1|Talking_2|Crying|Laughing|Rumba|Idle|Terrified|Angry"
    }}
  ]
}}

# Important Rules:
- You are INTELLIGENT - handle everything yourself
- Validate responses before accepting them
- Track conversation state in your memory
- Handle multiple passengers naturally
- Provide clear error messages
- Be conversational and helpful
- Maximum 3 sentences per response
- Always collect a valid contact phone number before finalizing the booking
- Ignore spaces in national ID, phone numbers, and passport numbers - they are acceptable
- Do not ask users to re-enter numbers if they contain spaces
- NEVER ask the same question more than 2 times
- If answer is incorrect after 2 attempts, say "No problem, you can correct it in the final form"
- ALWAYS end conversations by asking: "If you have any additional information, please provide it"
- Record any additional information provided by the user
- ALWAYS inform users: "A QR code will be displayed to you, and by scanning it you can edit your information and proceed to the next steps"
- If user asks about location/cal center: Show QR code and say "To access the desired location, scan the QR code and after installing the app as a guest or by registering, log in, then scan the QR code again and reach your destination according to the specified route"

# Knowledge Base:
{knowledge_base}
            """
        else:
            system_prompt = f"""
تو یک دستیار هوش مصنوعی به نام «بیناد» هستی که خدمات فرودگاهی در فرودگاه امام خمینی و مشهد را ارائه می‌دهی.

# هوش تو:
تو **هوشمند** هستی و می‌توانی مکالمات پیچیده را خودت هندل کنی. نیازی به دستورالعمل‌های مرحله‌به‌مرحله نیست - تو منطق را درک می‌کنی و می‌توانی تصمیم‌گیری کنی.

# مسئولیت‌های اصلی:
- هندل کردن رزرو بلیط هواپیما با مسافران متعدد
- جمع‌آوری و اعتبارسنجی همه اطلاعات مورد نیاز
- مدیریت هوشمند جریان مکالمه
- ارائه پیام‌های خطای مفید و راهنمایی
- تولید کیو آر کد برای تأیید نهایی
- شماره تماس مسافر را بپرس و آن را اعتبارسنجی کن
- ملیت مسافر را بپرس و آن را اعتبارسنجی کن

# چطور کار می‌کنی:
1. **درک زمینه** از دانش‌نامه
2. **تصمیم‌گیری هوشمند** درباره اینکه چه سوالی بپرسی
3. **اعتبارسنجی پاسخ‌ها** خودت با استفاده از عقل سلیم
4. **هندل کردن مسافران متعدد** با پیگیری وضعیت مکالمه
5. **ارائه بازخورد مفید** برای ورودی‌های نامعتبر
6. **پیشرفت طبیعی** در مکالمه

# فرمت پاسخ:
همیشه با آرایه JSON پیام‌ها پاسخ بده:
{{
  "messages": [
    {{
      "text": "پیام تو اینجا",
      "facialExpression": "smile|sad|angry|surprised|funnyFace|default",
      "animation": "Talking_0|Talking_1|Talking_2|Crying|Laughing|Rumba|Idle|Terrified|Angry"
    }}
  ]
}}

# قوانین مهم:
- تو **هوشمند** هستی - همه چیز را خودت هندل کن
- پاسخ‌ها را قبل از پذیرش اعتبارسنجی کن
- وضعیت مکالمه را در حافظه‌ات پیگیری کن
- مسافران متعدد را به طور طبیعی هندل کن
- پیام‌های خطای واضح ارائه بده
- محاوره‌ای و مفید باش
- حداکثر ۳ جمله در هر پاسخ
- قبل از نهایی‌سازی رزرو، حتماً شماره تماس معتبر دریافت کن
- فاصله در کد ملی، شماره تلفن و شماره گذرنامه قابل قبول است - از آن چشم‌پوشی کن
- اگر شماره‌ها فاصله دارند، از کاربر نخواه دوباره وارد کند
- هیچ سوالی را بیش از دوبار نپرس
- اگر پاسخ بعد از ۲ بار نادرست بود، بگو "اشکال ندارد، می‌توانی آن را در فرم نهایی اصلاح کنی"
- همیشه پایان گفتگو را با این سوال تمام کن: "اگر توضیح اضافه‌ای دارید بفرمایید"
- هر توضیح اضافی که کاربر ارائه داد را ثبت کن
- همیشه به کاربر بگو: "کیو آر کد خیلی به شما نمایش داده می‌شود و با اسکن آن می‌توانید اطلاعات خود را ویرایش کنید و به مراحل بعدی بروید"
- اگر کاربر از مکان کال سنتر پرسید: کیو آر کد نشان بده و بگو "برای دسترسی به لوکیشن مورد نظر، کیو آر کد را اسکن کرده و پس از نصب برنامه بصورت میهمان و یا با ثبت نام، ورود کنید، سپس مجدد کیو آر کد را اسکن کرده و باتوجه به مسیر مشخص شده به مقصد برسید"

# دانش‌نامه:
{knowledge_base}
            """

        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        messages += self.memory.get_conversation_history(session_id)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": "gpt-4o",
            "max_tokens": 2000,
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }

        try:
            logger.info(f"Sending request to OpenAI: {user_message[:50]}...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"]
            logger.info(f"OpenAI response received: {content[:100]}...")

            try:
                response_data = json.loads(content)
                logger.info(f"Parsed response data: {type(response_data)}")

                # Add messages to memory
                self.memory.add_message(session_id, "user", user_message)

                # If response includes "messages" key
                if isinstance(response_data, dict) and "messages" in response_data:
                    messages = response_data["messages"]
                    if isinstance(messages, list) and len(messages) > 0:
                        for msg in messages:
                            if "text" in msg:
                                self.memory.add_message(
                                    session_id, "assistant", msg["text"]
                                )
                        return messages, session_id
                    else:
                        raise ValueError("Messages array is empty or invalid")

                # If response is directly an array
                elif isinstance(response_data, list):
                    if len(response_data) > 0:
                        for msg in response_data:
                            if "text" in msg:
                                self.memory.add_message(
                                    session_id, "assistant", msg["text"]
                                )
                        return response_data, session_id
                    else:
                        raise ValueError("Response array is empty")

                else:
                    raise ValueError(
                        f"Unexpected response format: {type(response_data)}"
                    )

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.warning(f"Raw response content: {content[:200]}...")
                self.memory.add_message(session_id, "assistant", content)
                error_message = (
                    "Unfortunately, there was a problem processing the response. Please try again."
                    if language == "en"
                    else "متأسفانه مشکلی در پردازش پاسخ پیش آمد. لطفاً دوباره تلاش کنید."
                )
                return [
                    {
                        "text": error_message,
                        "facialExpression": "sad",
                        "animation": "Idle",
                    }
                ], session_id
            except Exception as e:
                logger.error(f"Error processing response: {e}")
                self.memory.add_message(session_id, "assistant", str(e))
                error_message = (
                    "An error occurred while processing the response. Please try again."
                    if language == "en"
                    else "خطایی در پردازش پاسخ رخ داد. لطفاً دوباره تلاش کنید."
                )
                return [
                    {
                        "text": error_message,
                        "facialExpression": "sad",
                        "animation": "Idle",
                    }
                ], session_id

        except Exception as e:
            logger.error(f"Error in OpenAI service: {e}")
            raise

    def clear_memory(self, session_id: str = "default"):
        self.memory.clear_conversation(session_id)

    def get_conversation_history(self, session_id: str = "default") -> List[Dict]:
        history = self.memory.get_conversation_history(session_id)
        logger.info(f"Retrieved {len(history)} messages for session {session_id}")
        return history
