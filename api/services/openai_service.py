# import os
# import json
# import logging
# import requests
# import uuid
# from typing import List, Dict, Optional
# from datetime import datetime

# logger = logging.getLogger(__name__)


# class BookingState:
#     """Manages the state of booking process for each session"""

#     def __init__(self):
#         self.current_step = 0
#         self.retry_count = 0
#         self.collected_data = {
#             "origin_airport": "",
#             "destination_airport": "",
#             "travel_date": "",
#             "national_id": "",
#             "phone_number": "",
#             "passenger_name": "",
#         }

#     def get_next_question(self) -> tuple:
#         """Returns the next question key and step number"""
#         questions = [
#             "origin_airport",
#             "destination_airport",
#             "travel_date",
#             "national_id",
#             "phone_number",
#             "passenger_name",
#         ]
#         if self.current_step < len(questions):
#             return questions[self.current_step], self.current_step
#         return "completed", self.current_step

#     def update_state(self, key: str, value: str):
#         """Updates the collected data and moves to next step"""
#         if key in self.collected_data:
#             self.collected_data[key] = value
#             self.current_step += 1
#             self.retry_count = 0


# class AgentMemory:
#     """Memory system for the agent to maintain conversation history"""

#     def __init__(self, max_messages: int = 20):
#         self.max_messages = max_messages
#         self.conversations: Dict[str, List[Dict]] = {}

#     def add_message(self, session_id: str, role: str, content: str):
#         """Add a message to the conversation history"""
#         if session_id not in self.conversations:
#             self.conversations[session_id] = []

#         message = {
#             "role": role,
#             "content": content,
#             "timestamp": datetime.now().isoformat(),
#         }

#         self.conversations[session_id].append(message)

#         # Keep only the last max_messages
#         if len(self.conversations[session_id]) > self.max_messages:
#             self.conversations[session_id] = self.conversations[session_id][
#                 -self.max_messages :
#             ]

#     def get_conversation_history(self, session_id: str) -> List[Dict]:
#         """Get conversation history for a session"""
#         return self.conversations.get(session_id, [])

#     def clear_conversation(self, session_id: str):
#         """Clear conversation history for a session"""
#         if session_id in self.conversations:
#             del self.conversations[session_id]


# class OpenAIService:
#     def __init__(self):
#         self.api_key = os.getenv("OPENAI_API_KEY")
#         if not self.api_key:
#             logger.error("OPENAI_API_KEY not set")
#             raise ValueError("OPENAI_API_KEY environment variable is not set")

#         self.api_url = "https://api.openai.com/v1/chat/completions"
#         self.memory = AgentMemory()
#         self.booking_states = {}  # Dictionary to store booking state per session

#     def validate_national_id(self, national_id: str) -> bool:
#         cleaned_id = national_id.replace(" ", "")
#         return cleaned_id.isdigit() and len(cleaned_id) == 10

#     def validate_phone_number(self, phone: str) -> bool:
#         cleaned_phone = phone.replace(" ", "")
#         return cleaned_phone.isdigit() and len(cleaned_phone) == 11

#     def get_assistant_response(
#         self, user_message: str, session_id: Optional[str] = None
#     ):
#         # Generate or retrieve session_id
#         if session_id is None:
#             session_id = str(uuid.uuid4())
#             logger.info(f"Generated new session_id: {session_id}")

#         # Initialize booking state if not exists
#         if session_id not in self.booking_states:
#             self.booking_states[session_id] = BookingState()

#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json",
#         }

#         with open("api/constants/knowledge_base.txt", "r", encoding="utf-8") as f:
#             system_prompt = f.read()

#         # Get conversation history and booking state
#         conversation_history = self.memory.get_conversation_history(session_id)
#         booking_state = self.booking_states[session_id]

#         # Build system prompt with current state
#         system_prompt = (
#             "You are Binad, an AI assistant for airport services at Imam Khomeini and Mashhad airports. "
#             "Follow the rules, tone, and step-by-step process defined in the knowledge base strictly. "
#             "Do not generate any information outside the knowledge base. "
#             "Ask questions in the exact order specified and validate inputs (e.g., national ID, phone number) as instructed. "
#             f"Current booking state: {json.dumps(booking_state.collected_data, ensure_ascii=False)}. "
#             f"Next question to ask: {booking_state.get_next_question()}. "
#             "Respond with a JSON array of up to 3 messages, each with text, facialExpression, and animation as defined. "
#             "Knowledge base:\n" + system_prompt
#         )

#         # Build messages array
#         messages = [
#             {"role": "system", "content": system_prompt},
#             *conversation_history,
#             {"role": "user", "content": user_message or "Hello"},
#         ]

#         payload = {
#             "model": "gpt-4o",
#             "max_tokens": 1000,
#             "temperature": 0.3,  # Reduced for more deterministic responses
#             "response_format": {"type": "json_object"},
#             "messages": messages,
#         }

#         try:
#             logger.info(f"Sending request to OpenAI: {user_message[:50]}...")
#             response = requests.post(
#                 self.api_url,
#                 headers=headers,
#                 json=payload,
#                 timeout=60,
#             )
#             response.raise_for_status()

#             content = response.json()["choices"][0]["message"]["content"]
#             logger.info(f"OpenAI response received: {content[:100]}...")

#             # Parse response
#             response_data = json.loads(content)
#             messages = response_data.get("messages", [])

#             # Validate and update booking state
#             current_step_key = booking_state.get_next_question()[0]
#             if current_step_key in ["national_id", "phone_number"]:
#                 user_input = user_message.replace(" ", "")
#                 if current_step_key == "national_id" and not self.validate_national_id(
#                     user_input
#                 ):
#                     messages = [
#                         {
#                             "text": "لطفاً کد ملی رو با ۱۰ رقم و فقط عدد وارد کن.",
#                             "facialExpression": "default",
#                             "animation": "Talking_0",
#                         }
#                     ]
#                     # Only one retry allowed
#                     if booking_state.retry_count > 0:
#                         messages = [
#                             {
#                                 "text": "اشکالی نداره، می‌تونی کد ملی رو در فرم نهایی اصلاح کنی.",
#                                 "facialExpression": "smile",
#                                 "animation": "Talking_1",
#                             }
#                         ]
#                         booking_state.current_step += 1
#                     booking_state.retry_count += 1
#                 elif (
#                     current_step_key == "phone_number"
#                     and not self.validate_phone_number(user_input)
#                 ):
#                     messages = [
#                         {
#                             "text": "لطفاً شماره تماس رو با ۱۱ رقم و فقط عدد وارد کن (فاصله بین اعداد مشکلی نداره).",
#                             "facialExpression": "default",
#                             "animation": "Talking_0",
#                         }
#                     ]
#                     if booking_state.retry_count > 0:
#                         messages = [
#                             {
#                                 "text": "اشکالی نداره، می‌تونی شماره تماس رو در فرم نهایی اصلاح کنی.",
#                                 "facialExpression": "smile",
#                                 "animation": "Talking_1",
#                             }
#                         ]
#                         booking_state.current_step += 1
#                     booking_state.retry_count += 1
#                 else:
#                     booking_state.update_state(current_step_key, user_input)
#             else:
#                 booking_state.update_state(current_step_key, user_message)

#             # Add special transfer message for Imam Khomeini
#             if booking_state.collected_data["origin_airport"] == "امام خمینی":
#                 messages.append(
#                     {
#                         "text": "راستی اگه الان فرودگاه امام خمینی هستی می‌تونم هماهنگ کنم بچه‌های ترنسفر درب خروجی سوارت کنند و ترنسفرت رو مهمون من باشی، نظرت چیه دوست من؟",
#                         "facialExpression": "smile",
#                         "animation": "Talking_2",
#                     }
#                 )

#             # Add messages to memory
#             self.memory.add_message(session_id, "user", user_message)
#             self.memory.add_message(
#                 session_id, "assistant", json.dumps({"messages": messages})
#             )

#             return messages, session_id

#         except Exception as e:
#             logger.error(f"Error in OpenAI service: {e}")
#             raise

#     def get_conversation_history(self, session_id: str):
#         """Get conversation history for a session"""
#         return self.memory.get_conversation_history(session_id)

#     def clear_memory(self, session_id: str):
#         """Clear conversation history for a session"""
#         self.memory.clear_conversation(session_id)
#         if session_id in self.booking_states:
#             del self.booking_states[session_id]

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


class BookingState:
    """Manages the state of the booking process for each session."""

    def __init__(self):
        self.current_step = 0
        self.retry_count = 0
        self.collected_data: Dict[str, str] = {
            "origin_airport": "",
            "travel_type": "",  # ورودی یا خروجی
            "travel_date": "",
            "passenger_count": "",
            "passenger_name": "",
            "national_id": "",
            "flight_number": "",
            "baggage_count": "",
            "phone_number": "",
        }

    def get_next_question(self) -> tuple:
        """Returns the next question key and step index."""
        questions = [
            "origin_airport",
            "travel_type",
            "travel_date",
            "passenger_count",
            "passenger_name",
            "national_id",
            "flight_number",
            "baggage_count",
            "phone_number",
        ]
        if self.current_step < len(questions):
            return questions[self.current_step], self.current_step
        return "completed", self.current_step

    def update_state(self, key: str, value: str):
        if key in self.collected_data:
            self.collected_data[key] = value
            self.current_step += 1
            self.retry_count = 0


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
            self.booking_states: Dict[str, BookingState] = {}
            self.initialized = True

    def get_assistant_response(
        self, user_message: str, session_id: Optional[str] = None
    ):
        if session_id is None:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with open("api/constants/knowledge_base.txt", "r", encoding="utf-8") as f:
            knowledge_base = f.read()

        # Initialize booking state for this session if not exists
        if session_id not in self.booking_states:
            self.booking_states[session_id] = BookingState()
        booking_state = self.booking_states[session_id]

        system_prompt = f"""
تو یک دستیار هوش مصنوعی به نام «بیناد» هستی که خدمات فرودگاهی در فرودگاه امام خمینی و مشهد را ارائه می‌دهی.

# قوانین مهم:
- همیشه در نقش بمون، فقط درباره موضوعات تعریف‌شده در دانش‌نامه حرف بزن
- در هر بار فقط یک سوال را بپرس و هرگز پیام های غیر مربوط به سوال را نپرس

- پاسخ‌ها باید مرحله‌به‌مرحله، با لحن محاوره‌ای، مهربان و حداکثر ۳ جمله‌ای باشن
- اگر اطلاعاتی ناقص بود، فقط یک بار با احترام تکرارش کن
- **مهم**: حتماً پاسخ را با فرمت JSON صحیح ارائه بده
- هر پاسخ باید شامل آرایه‌ای از حداکثر ۳ پیام باشه. هر پیام شامل:
  - text: متن پیام
  - facialExpression: یکی از (smile, sad, angry, surprised, funnyFace, default)
  - animation: یکی از (Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, Angry)

# فرمت پاسخ اجباری:
{{
  "messages": [
    {{
      "text": "سلام، به فرودگاه امام خوش اومدی!",
      "facialExpression": "smile",
      "animation": "Talking_0"
    }}
  ]
}}

 # وضعیت فعلی رزرو:
 - state: {json.dumps(booking_state.collected_data, ensure_ascii=False)}
 - next_question: {booking_state.get_next_question()}
 - قوانین اعتبارسنجی ویژه:
   - اگر کد ملی ۱۰ رقم نبود یا شامل حروف بود: فقط یک بار محترمانه تذکر بده
   - اگر بار دوم هم اشتباه بود: بگو در فرم نهایی می‌تواند اصلاح کند و به مرحله بعد برو
   - اگر شماره تماس ۱۱ رقم نبود یا شامل حروف بود: فقط یک بار تذکر بده
   - اگر بار دوم هم اشتباه بود: بگو در فرم نهایی می‌تواند اصلاح کند و به مرحله بعد برو

# دانش‌نامه:
{knowledge_base}
        """

        # ساخت پیام‌ها
        messages = [{"role": "system", "content": system_prompt}]
        messages += self.memory.get_conversation_history(session_id)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": "gpt-4o",
            "max_tokens": 1500,
            "temperature": 0.6,
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

            # ذخیره پیام‌ها در حافظه
            self.memory.add_message(session_id, "user", user_message)

            try:
                response_data = json.loads(content)
                logger.info(f"Parsed response data: {type(response_data)}")

                # اگر پاسخ شامل کلید "messages" باشد
                if isinstance(response_data, dict) and "messages" in response_data:
                    messages = response_data["messages"]
                    if isinstance(messages, list) and len(messages) > 0:
                        for msg in messages:
                            if "text" in msg:
                                self.memory.add_message(
                                    session_id, "assistant", msg["text"]
                                )
                        # Apply deterministic booking logic
                        messages = self._apply_booking_logic_and_maybe_override(
                            user_message=user_message,
                            session_id=session_id,
                            booking_state=booking_state,
                            messages=messages,
                        )
                        return messages, session_id
                    else:
                        raise ValueError("Messages array is empty or invalid")

                # اگر پاسخ مستقیماً آرایه باشد
                elif isinstance(response_data, list):
                    if len(response_data) > 0:
                        for msg in response_data:
                            if "text" in msg:
                                self.memory.add_message(
                                    session_id, "assistant", msg["text"]
                                )
                        messages_list = response_data
                        messages_list = self._apply_booking_logic_and_maybe_override(
                            user_message=user_message,
                            session_id=session_id,
                            booking_state=booking_state,
                            messages=messages_list,
                        )
                        return messages_list, session_id
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
                return [
                    {
                        "text": "متأسفانه مشکلی در پردازش پاسخ پیش آمد. لطفاً دوباره تلاش کنید.",
                        "facialExpression": "sad",
                        "animation": "Idle",
                    }
                ], session_id
            except Exception as e:
                logger.error(f"Error processing response: {e}")
                self.memory.add_message(session_id, "assistant", str(e))
                return [
                    {
                        "text": "خطایی در پردازش پاسخ رخ داد. لطفاً دوباره تلاش کنید.",
                        "facialExpression": "sad",
                        "animation": "Idle",
                    }
                ], session_id

        except Exception as e:
            logger.error(f"Error in OpenAI service: {e}")
            raise

    def clear_memory(self, session_id: str = "default"):
        self.memory.clear_conversation(session_id)
        # Also reset booking state if exists
        try:
            if hasattr(self, "booking_states") and session_id in self.booking_states:
                del self.booking_states[session_id]
        except Exception:
            pass

    def get_conversation_history(self, session_id: str = "default") -> List[Dict]:
        history = self.memory.get_conversation_history(session_id)
        logger.info(f"Retrieved {len(history)} messages for session {session_id}")
        return history

    # ---------------- Internal helpers ----------------
    @staticmethod
    def _validate_national_id(national_id: str) -> bool:
        cleaned = national_id.replace(" ", "")
        return cleaned.isdigit() and len(cleaned) == 10

    @staticmethod
    def _validate_phone_number(phone: str) -> bool:
        cleaned = phone.replace(" ", "")
        return cleaned.isdigit() and len(cleaned) == 11

    def _apply_booking_logic_and_maybe_override(
        self,
        user_message: str,
        session_id: str,
        booking_state: BookingState,
        messages: List[Dict],
    ) -> List[Dict]:
        """Apply deterministic validation and step progression for ID/phone.

        If invalid entry is provided twice, proceed to the next step while informing the user.
        """
        current_key, _ = booking_state.get_next_question()

        # Only handle known steps deterministically
        if current_key in ("national_id", "phone_number"):
            cleaned_input = user_message.replace(" ", "")
            is_valid = (
                self._validate_national_id(cleaned_input)
                if current_key == "national_id"
                else self._validate_phone_number(cleaned_input)
            )

            if not is_valid:
                if booking_state.retry_count == 0:
                    # First invalid attempt: ask for correction, do not advance
                    booking_state.retry_count = 1
                    correction_text = (
                        "لطفاً کد ملی رو با ۱۰ رقم و فقط عدد وارد کن."
                        if current_key == "national_id"
                        else "لطفاً شماره تماس رو با ۱۱ رقم و فقط عدد وارد کن (فاصله بین اعداد مشکلی نداره)."
                    )
                    return [
                        {
                            "text": correction_text,
                            "facialExpression": "default",
                            "animation": "Talking_0",
                        }
                    ]
                else:
                    # Second invalid attempt: inform and advance to next step
                    booking_state.current_step += 1
                    booking_state.retry_count = 0
                    skip_text = (
                        "اشکالی نداره، می‌تونی کد ملی رو در فرم نهایی اصلاح کنی."
                        if current_key == "national_id"
                        else "اشکالی نداره، می‌تونی شماره تماس رو در فرم نهایی اصلاح کنی."
                    )
                    next_key, _ = booking_state.get_next_question()
                    next_question_text = self._get_question_text_for_key(next_key)
                    return [
                        {
                            "text": skip_text,
                            "facialExpression": "smile",
                            "animation": "Talking_1",
                        },
                        {
                            "text": next_question_text,
                            "facialExpression": "default",
                            "animation": "Talking_0",
                        },
                    ]
            else:
                # Valid input: save and go next
                booking_state.update_state(current_key, cleaned_input)

        elif current_key != "completed":
            # Save generic input for other steps and move forward
            booking_state.update_state(current_key, user_message)

        # Special transfer message if origin_airport is Imam Khomeini
        try:
            if booking_state.collected_data.get("origin_airport") in [
                "امام خمینی",
                "امام خميني",
                "Imam Khomeini",
            ]:
                messages.append(
                    {
                        "text": "راستی اگه الان فرودگاه امام خمینی هستی می‌تونم هماهنگ کنم بچه‌های ترنسفر درب خروجی سوارت کنند و ترنسفرت رو مهمون من باشی، نظرت چیه دوست من؟",
                        "facialExpression": "smile",
                        "animation": "Talking_2",
                    }
                )
        except Exception:
            pass

        return messages

    @staticmethod
    def _get_question_text_for_key(key: str) -> str:
        mapping: Dict[str, str] = {
            "origin_airport": "نام فرودگاه مبدا رو بفرمایید.",
            "travel_type": "پروازتون ورودی به فرودگاهه یا خروجی؟",
            "travel_date": "تاریخ سفر رو بفرمایید.",
            "passenger_count": "تعداد مسافران رو لطفاً بفرمایید.",
            "passenger_name": "نام و نام خانوادگی مسافر رو بفرمایید.",
            "national_id": "کد ملی مسافر رو بفرمایید.",
            "flight_number": "شماره پرواز رو بفرمایید.",
            "baggage_count": "تعداد چمدان‌ها رو بفرمایید.",
            "phone_number": "شماره تماس رو بفرمایید.",
            "completed": "همه اطلاعات دریافت شد. در پایان پیام تایید و کیوآرکد نمایش داده خواهد شد.",
        }
        return mapping.get(key, "")
