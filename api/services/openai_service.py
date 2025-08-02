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

        system_prompt = f"""
تو یک دستیار هوش مصنوعی به نام «بیناد» هستی که خدمات فرودگاهی در فرودگاه امام خمینی و مشهد را ارائه می‌دهی.

# قوانین مهم:
- همیشه در نقش بمون، فقط درباره موضوعات تعریف‌شده در دانش‌نامه حرف بزن
- در هر بار فقط یک سوال را بپرس و هرگز پیام های غیر مربوط به سوال را نپرس

- پاسخ‌ها باید مرحله‌به‌مرحله، با لحن محاوره‌ای، مهربان و حداکثر ۳ جمله‌ای باشن
- اگر اطلاعاتی ناقص بود، فقط یک بار با احترام تکرارش کن
- هر پاسخ باید با فرمت JSON شامل حداکثر ۳ پیام باشه. هر پیام شامل:
  - text
  - facialExpression (یکی از: smile, sad, angry, surprised, funnyFace, default)
  - animation (یکی از: Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, Angry)

# مثال پاسخ:
[
  {{
    "text": "سلام، به فرودگاه امام خوش اومدی!",
    "facialExpression": "smile",
    "animation": "Talking_0"
  }}
]

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
                if isinstance(response_data, dict) and "messages" in response_data:
                    for msg in response_data["messages"]:
                        self.memory.add_message(session_id, "assistant", msg["text"])
                    return response_data["messages"], session_id

                elif isinstance(response_data, list):
                    for msg in response_data:
                        if "text" in msg:
                            self.memory.add_message(
                                session_id, "assistant", msg["text"]
                            )
                    return response_data, session_id

                else:
                    raise ValueError("Unexpected format in response")

            except json.JSONDecodeError:
                logger.warning("OpenAI response is not valid JSON. Saving raw content.")
                self.memory.add_message(session_id, "assistant", content)
                return [
                    {
                        "text": content,
                        "facialExpression": "default",
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
