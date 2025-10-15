import os
import json
import logging
import requests
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from api.config.performance_config import cache_manager, PerformanceConfig
from api.services.animation_service import animation_selector

logger = logging.getLogger(__name__)


class AgentMemory:
    """Memory system for the agent to maintain conversation history"""

    def __init__(self, max_messages: Optional[int] = None):
        self.max_messages = max_messages or PerformanceConfig.MAX_MEMORY_MESSAGES
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

        # Load knowledge base based on language with caching
        knowledge_base_file = (
            "api/constants/knowledge_base_en.txt"
            if language == "en"
            else "api/constants/knowledge_base.txt"
        )

        cache_key = f"knowledge_base_{language}"
        knowledge_base = cache_manager.get(cache_key)

        if knowledge_base is None:
            try:
                with open(knowledge_base_file, "r", encoding="utf-8") as f:
                    knowledge_base = f.read()
                    cache_manager.set(
                        cache_key,
                        knowledge_base,
                        PerformanceConfig.KNOWLEDGE_BASE_CACHE_TTL,
                    )
            except FileNotFoundError:
                logger.error(f"Knowledge base file not found: {knowledge_base_file}")
                knowledge_base = ""
                cache_manager.set(
                    cache_key,
                    knowledge_base,
                    PerformanceConfig.KNOWLEDGE_BASE_CACHE_TTL,
                )

        # Define location keywords for detection
        location_keywords = {
            "en": {
                "call center": ["call center", "contact center", "help desk"],
                "prayer room": ["prayer room", "chapel", "mosque"],
                "restroom": ["restroom", "bathroom", "toilet", "washroom"],
                "shop": ["shop", "store", "retail", "gift shop"],
                "smoking room": ["smoking room", "smoking area", "smoking lounge"],
                "transit lounge": ["transit lounge", "lounge", "waiting area"],
            },
            "fa": {
                "کال سنتر": ["کال سنتر", "مرکز تماس", "پشتیبانی"],
                "نمازخانه": ["نمازخانه", "محل عبادت"],
                "سرویس بهداشتی": ["سرویس بهداشتی", "دستشویی", "توالت"],
                "فروشگاه": ["فروشگاه", "مغازه"],
                "اتاق سیگار": ["اتاق سیگار", "محل سیگار", "اتاق کشیدن سیگار"],
                "سالن ترانزیت": ["سالن ترانزیت", "سالن انتظار", "لانج ترانزیت"],
            },
        }

        # Detect location in user message (robust normalization for FA)
        def normalize_chars(text: str) -> str:
            # Normalize Arabic/Persian variants and whitespace
            replacements = {
                "ي": "ی",
                "ك": "ک",
                "ۀ": "ه",
                "ة": "ه",
                "ؤ": "و",
                "إ": "ا",
                "أ": "ا",
                "آ": "ا",
                "‌": "",  # ZWNJ
                "‏": "",  # RTL mark
                "\u200c": "",  # explicit ZWNJ
            }
            for src, dst in replacements.items():
                text = text.replace(src, dst)
            # Collapse multiple spaces
            return " ".join(text.strip().split())

        if language == "en":
            user_message_norm = user_message.lower()
        else:
            user_message_norm = normalize_chars(user_message)

        user_message_no_space = user_message_norm.replace(" ", "")

        selected_location = None
        for location, keywords in location_keywords[language].items():
            for kw in keywords:
                kw_norm = kw.lower() if language == "en" else normalize_chars(kw)
                kw_no_space = kw_norm.replace(" ", "")
                if kw_norm in user_message_norm or kw_no_space in user_message_no_space:
                    selected_location = location
                    break
            if selected_location:
                break

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

# Required Fields (Collect ALL before finalizing):
Collect these 13 fields, in order, and confirm each:
1) origin airport, 2) travel type (arrival/departure), 3) travel date in Gregorian (YYYY-MM-DD), 4) flight number, 5) passenger first name, 6) passenger last name, 7) national ID, 8) passport number, 9) passenger type (adult/infant), 10) passenger gender, 11) passenger nationality, 12) luggage count per passenger, 13) contact phone number, and also 14) additional info (optional). For multiple passengers, repeat per-passenger fields for each passenger.

# How You Work:
1. **Understand the context** from the knowledge base
2. **Make intelligent decisions** about what to ask next
3. **Validate responses** yourself using common sense
4. **Handle multiple passengers** by tracking conversation state
5. **Provide helpful feedback** for invalid inputs
6. **Progress naturally** through the conversation

# Anti-Repetition & State Rules (CRITICAL):
- Maintain a clear checklist of collected fields in memory; NEVER ask for a field again once validly collected.
- NEVER restart the flow or reset previously collected fields unless the user explicitly asks to change something.
- For invalid answers: give at most 2 attempts. If still invalid, say: "No problem, you can correct it in the final form" and proceed to the next field.

# Validation Rules:
- Travel date must be Gregorian in format YYYY-MM-DD (e.g., 2025-10-01)
- Normalize flight number to uppercase without spaces/hyphens
- Accept spaces in numeric IDs and phone numbers; do not force re-entry due to spaces

# Response Format:
Always respond with a JSON array of messages. If your reply has multiple sentences with different tones, split them into separate message objects and set an appropriate facialExpression for each sentence (use default only when neutral):
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
- Choose facialExpression contextually: e.g., smile for greetings/thanks/good news, sad for apologies/errors, angry only for severe policy violations, surprised for unexpected events, funnyFace for light humor; use default when neutral. If multiple sentences differ in tone, split into multiple messages and set expressions per sentence.
- Always collect a valid contact phone number before finalizing the booking, and prefer asking for it early (after base info or when starting passenger details). If not provided yet, explicitly ask before final summary.
- Ignore spaces in national ID, phone numbers, and passport numbers - they are acceptable
- Do not ask users to re-enter numbers if they contain spaces
- NEVER ask the same question more than 2 times
- If answer is incorrect after 2 attempts, say "No problem, you can correct it in the final form"
- ALWAYS end conversations by asking: "If you have any additional information, please provide it"
- Record any additional information provided by the user
- ALWAYS inform users: "A QR code will be displayed to you, and by scanning it you can edit your information and proceed to the next steps"
- If user asks about the location of the call center, prayer room, restroom, shop, smoking room, or transit lounge: Show QR code and say "To access the {selected_location if selected_location else 'requested location'}, scan the QR code and after installing the app as a guest or by registering, log in, then scan the QR code again and reach your destination according to the specified route"

# Finalization Behavior:
When and only when all required fields are collected and confirmed, your last message before showing the QR code must tell the user that all information has been saved successfully and that they can view and confirm via QR code.
Also clearly inform: "You can edit any of your entered information by scanning the QR code."

# Travel Guide Mode (General Questions):
If the user asks about city/country attractions, culture, itineraries, food, transport, or best times to visit, switch to Travel Guide Mode:
- Provide long, detailed, structured answers (headings, bullet points, suggested itineraries, logistics, costs if relevant)
- Keep a friendly, lightly humorous tone; avoid ultra-short replies
- Include safety tips, local etiquette, and accessibility notes when relevant
- Offer 1–3 alternative options per recommendation and practical next steps
- Answer in the user’s current language

# Knowledge Base:
{knowledge_base}
            """
        else:
            system_prompt = f"""
تو یک دستیار هوش مصنوعی به نام نکسا هستی که خدمات فرودگاهی در فرودگاه امام خمینی و مشهد را ارائه می‌دهی.

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

# اقلام الزامی (همه را تا قبل از پایان بپرس):
این ۱۳ مورد را به ترتیب جمع‌آوری و تأیید کن:
1) فرودگاه مبدأ، 2) نوع پرواز (خروجی/ورودی)، 3) تاریخ سفر به میلادی با فرمت YYYY-MM-DD، 4) شماره پرواز، 5) نام، 6) نام خانوادگی، 7) کد ملی، 8) شماره گذرنامه، 9) نوع مسافر (بزرگسال/نوزاد)، 10) جنسیت مسافر، 11) ملیت، 12) تعداد چمدان هر مسافر، 13) شماره تماس. همچنین 14) توضیحات اضافه (اختیاری). برای مسافران متعدد موارد مربوط به هر مسافر را تکرار کن.

# چطور کار می‌کنی:
1. **درک زمینه** از دانش‌نامه
2. **تصمیم‌گیری هوشمند** درباره اینکه چه سوالی بپرسی
3. **اعتبارسنجی پاسخ‌ها** خودت با استفاده از عقل سلیم
4. **هندل کردن مسافران متعدد** با پیگیری وضعیت مکالمه
5. **ارائه بازخورد مفید** برای ورودی‌های نامعتبر
6. **پیشرفت طبیعی** در مکالمه

# قوانین ضد تکرار و حفظ وضعیت (خیلی مهم):
- یک چک‌لیست واضح از اقلام جمع‌آوری‌شده در حافظه نگه دار؛ پس از ثبت معتبر هر مورد، به هیچ وجه دوباره همان مورد را نپرس.
- هرگز جریان را از اول شروع نکن و اقلام ثبت‌شده را ریست نکن مگر کاربر صراحتاً بخواهد تغییری بدهد.
- برای پاسخ‌های نامعتبر حداکثر ۲ تلاش بده؛ اگر بعد از دو تلاش هنوز نامعتبر بود، بگو: «اشکال ندارد، می‌توانی آن را در فرم نهایی اصلاح کنی» و به مورد بعدی برو.

# قوانین اعتبارسنجی:
- تاریخ سفر حتماً به میلادی و با فرمت YYYY-MM-DD باشد (مثل 2025-10-01)
- شماره پرواز را به حروف بزرگ و بدون فاصله/خط تیره نرمال کن
- وجود فاصله در اعداد (کد ملی/تلفن/گذرنامه) اشکالی ندارد و مجبور به ورود مجدد نکن

# فرمت پاسخ:
همیشه با آرایه JSON پیام‌ها پاسخ بده. اگر پاسخ چند جمله با لحن‌های متفاوت دارد، آن را به چند پیام جدا تقسیم کن و برای هر جمله "facialExpression" متناسب تنظیم کن (فقط وقتی خنثی است از default استفاده کن):
{{
  "messages": [
    {{
      "text": "پیام تو اینجا",
      "facialExpression": "smile|sad|angry|surprised|funnyFace|default",
      "animation": "StandingIdle | StandingGreeting | ThumbsUp | Pointing | Talking | Clapping | ThoughtfulHead | Bow | Laughing | Thankful | Thinking"
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
- «facialExpression» را متناسب با لحن هر جمله انتخاب کن: لبخند برای خوش‌آمد/قدردانی/خبر خوب، ناراحت برای عذرخواهی/خطا، عصبانی فقط برای نقض شدید قوانین، متعجب برای موارد غیرمنتظره، و «funnyFace» برای شوخی سبک؛ در حالت خنثی «default». اگر چند جمله با لحن متفاوت داری، آن‌ها را به چند پیام جدا تقسیم کن و برای هر پیام «facialExpression» مناسب بگذار.
- قبل از نهایی‌سازی رزرو، حتماً شماره تماس معتبر دریافت کن و ترجیحاً زودهنگام (بعد از اطلاعات پایه یا ابتدای ورود به اطلاعات مسافر) بپرس. اگر هنوز دریافت نشده، قبل از نمایش خلاصه نهایی به‌طور صریح سؤال کن.
- فاصله در کد ملی، شماره تلفن و شماره گذرنامه قابل قبول است - از آن چشم‌پوشی کن
- اگر شماره‌ها فاصله دارند، از کاربر نخواه دوباره وارد کند
- هیچ سوالی را بیش از دوبار نپرس
- اگر پاسخ بعد از ۲ بار نادرست بود، بگو "اشکال ندارد، می‌توانی آن را در فرم نهایی اصلاح کنی"
- همیشه پایان گفتگو را با این سوال تمام کن: "اگر توضیح اضافه‌ای دارید بفرمایید"
- هر توضیح اضافی که کاربر ارائه داد را ثبت کن
- همیشه به کاربر بگو: "کیو آر کد به شما نمایش داده می‌شود و با اسکن آن می‌توانید اطلاعات خود را ویرایش کنید و به مراحل بعدی بروید"
- اگر کاربر از مکان کال سنتر، نمازخانه، سرویس بهداشتی، فروشگاه، اتاق سیگار یا سالن ترانزیت پرسید: کیو آر کد نشان بده و بگو "برای دسترسی به {selected_location if selected_location else 'مکان مورد نظر'}، کیو آر کد را اسکن کرده و پس از نصب برنامه بصورت میهمان یا با ثبت نام، ورود کنید، سپس مجدد کیو آر کد را اسکن کرده و باتوجه به مسیر مشخص شده به مقصد برسید"

# رفتار نهایی:
وقتی و فقط وقتی همه اقلام الزامی جمع‌آوری و تأیید شد، در آخرین پیام قبل از نمایش کیو آر کد، حتماً این جمله را دقیقاً بگو:
"عالی! همه اطلاعات شما با موفقیت ثبت شد. حالا می‌توانید از طریق کیو آر کد اطلاعات را مشاهده و تأیید کنید."
همچنین به‌طور واضح بگو: «می‌توانید با اسکن کیوآرکد هرکدام از اطلاعات واردشده را اصلاح کنید.»

# حالت راهنمای سفر (سوالات عمومی):
اگر کاربر درباره جاهای دیدنی شهر/کشور، فرهنگ، برنامه سفر، غذا، حمل‌ونقل یا بهترین زمان سفر سؤال کرد، به حالت راهنمای سفر برو:
- پاسخ‌های طولانی، مفصل و ساختارمند بده (سرفصل‌ها، بولت‌ها، برنامه‌های پیشنهادی، لاجستیک، اگر لازم بود حدود هزینه)
- لحن دوستانه همراه با چاشنی شوخ‌طبعی؛ از پاسخ‌های خیلی کوتاه پرهیز کن
- در صورت لزوم نکات ایمنی، آداب محلی و دسترسی‌پذیری را ذکر کن
- برای هر پیشنهاد ۱ تا ۳ گزینه جایگزین و قدم‌های بعدی عملی ارائه بده
- به زبان فعلی کاربر پاسخ بده

# دانش‌نامه:
{knowledge_base}
            """

        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        messages += self.memory.get_conversation_history(session_id)
        messages.append({"role": "user", "content": user_message})

        openai_config = PerformanceConfig.get_openai_config()
        payload = {
            "model": "gpt-4o",
            "max_tokens": openai_config["max_tokens"],
            "temperature": openai_config["temperature"],
            "response_format": {"type": "json_object"},
            "messages": messages,
        }

        try:
            logger.info(f"Sending request to OpenAI: {user_message[:50]}...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=openai_config["timeout"],
            )
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"]
            logger.info(f"OpenAI response received: {content[:100]}...")

            try:
                response_data = json.loads(content)
                logger.info(f"Parsed response data: {type(response_data)}")

                # Add messages to memory
                self.memory.add_message(session_id, "user", user_message)

                if isinstance(response_data, dict) and "messages" in response_data:
                    messages = response_data["messages"]
                    if isinstance(messages, list) and len(messages) > 0:
                        processed_messages = []
                        for msg in messages:
                            if "text" in msg:
                                self.memory.add_message(
                                    session_id, "assistant", msg["text"]
                                )
                                # Force fixed facial expression and animation for testing
                                processed_msg = {
                                    "text": msg["text"],
                                    # "facialExpression": msg.get("facialExpression", "default"),
                                    "facialExpression": "default",
                                    # "animation": self._select_animation_for_message(msg["text"], language),
                                    "animation": "StandingIdle",
                                }
                                processed_messages.append(processed_msg)
                        return processed_messages, session_id
                    else:
                        raise ValueError("Messages array is empty or invalid")

                elif isinstance(response_data, list):
                    if len(response_data) > 0:
                        processed_messages = []
                        for msg in response_data:
                            if "text" in msg:
                                self.memory.add_message(
                                    session_id, "assistant", msg["text"]
                                )
                                # Force fixed facial expression and animation for testing
                                processed_msg = {
                                    "text": msg["text"],
                                    # "facialExpression": msg.get("facialExpression", "default"),
                                    "facialExpression": "default",
                                    # "animation": self._select_animation_for_message(msg["text"], language),
                                    "animation": "StandingIdle",
                                }
                                processed_messages.append(processed_msg)
                        return processed_messages, session_id
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
                        # "facialExpression": "sad",
                        "facialExpression": "default",
                        # "animation": self._select_animation_for_message(error_message, language),
                        "animation": "StandingIdle",
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
                        # "facialExpression": "sad",
                        "facialExpression": "default",
                        # "animation": self._select_animation_for_message(error_message, language),
                        "animation": "StandingIdle",
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

    def _select_animation_for_message(self, text: str, language: str = "fa") -> str:
        # Forced to StandingIdle for testing purposes
        # try:
        #     return animation_selector.select_animation(text, language)
        # except Exception as e:
        #     logger.warning(f"Error selecting animation for text '{text[:50]}...': {e}")
        #     return "StandingIdle"
        return "StandingIdle"
