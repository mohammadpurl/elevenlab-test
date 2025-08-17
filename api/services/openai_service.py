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
            "passport_number": "",
            "baggage_count": "",
            "passenger_type": "",  # بزرگسال یا نوزاد
            "gender": "",  # جنسیت
            "additional_info": "",
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
            "passport_number",
            "baggage_count",
            "passenger_type",
            "gender",
            "additional_info",
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

            # Initialize booking state for this session if not exists
        if session_id not in self.booking_states:
            self.booking_states[session_id] = BookingState()
        booking_state = self.booking_states[session_id]

        # Create language-specific system prompt
        if language == "en":
            system_prompt = f"""
You are an AI assistant named "Binad" who provides airport services at Imam Khomeini and Mashhad airports.

# Important Rules:
- Always stay in character, only talk about topics defined in the knowledge base
- Ask only one question at a time and never ask messages unrelated to the question

- Responses should be step-by-step, with conversational, friendly tone and maximum 3 sentences
- If information is incomplete, respectfully repeat it only once
- **Important**: Always provide the response in correct JSON format
- Each response should include an array of maximum 3 messages. Each message includes:
  - text: message text
  - facialExpression: one of (smile, sad, angry, surprised, funnyFace, default)
  - animation: one of (Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, Angry)

# Required Response Format:
{{
  "messages": [
    {{
      "text": "Hello, welcome to Imam Airport!",
      "facialExpression": "smile",
      "animation": "Talking_0"
    }}
  ]
}}

# Current Booking State:
- state: {json.dumps(booking_state.collected_data, ensure_ascii=False)}
- next_question: {booking_state.get_next_question()}

# Exact Question Texts (must use):
- Number of passengers: "What is the exact number of passengers?"
- Passenger name: "Please provide the passenger's full name."
- National ID: "Please provide the passenger's national ID."
- Flight number: "Please provide the flight number."
- Passport number: "Please provide the passenger's passport number."
- Number of bags: "Please provide the number of bags."
- Passenger type: "Is the passenger an adult or infant?"
- Gender: "What is the passenger's gender?"
- Additional info: "Any additional information you would like to provide?"

# Important Note:
- After asking for passenger count, you must collect ALL information for EACH passenger separately
- For each passenger, ask: name, national ID, passport number, baggage count, passenger type (adult/infant), and gender
- Make it very clear that you are asking for each passenger individually

# Knowledge Base:
{knowledge_base}
            """
        else:
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

# متن دقیق سوالات (حتماً استفاده کن):
- تعداد مسافران: "تعداد دقیق مسافران چند نفر است؟"
- نام مسافر: "نام و نام خانوادگی مسافر رو بفرمایید."
- کد ملی: "کد ملی مسافر رو بفرمایید."
- شماره پرواز: "شماره پرواز رو بفرمایید."
- شماره گذرنامه: "شماره گذرنامه مسافر رو بفرمایید."
- تعداد چمدان: "تعداد چمدان‌ها رو بفرمایید."
- نوع مسافر: "نوع مسافر بزرگسال است یا نوزاد؟"
- جنسیت: "جنسیت مسافر چیه؟"
- توضیح اضافه: "توضیح اضافه‌ای که می‌خواید بگید؟"

# نکته مهم:
- بعد از پرسیدن تعداد مسافران، باید اطلاعات همه مسافران را جداگانه و به صورت واضح جمع‌آوری کنی
- برای هر مسافر، بپرس: نام، کد ملی، شماره گذرنامه، تعداد چمدان، نوع مسافر (بزرگسال/نوزاد) و جنسیت
- حتماً واضح بگو که برای هر مسافر جداگانه سوال می‌کنی

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

            try:
                response_data = json.loads(content)
                logger.info(f"Parsed response data: {type(response_data)}")

                # Check if this is a new session and we need to ask the first question
                conversation_history = self.memory.get_conversation_history(session_id)
                current_key, _ = booking_state.get_next_question()

                # If this is a new session (no conversation history) and we're at the first step
                if len(conversation_history) == 0 and current_key == "origin_airport":
                    first_question_text = self._get_question_text_for_key(
                        "origin_airport", language
                    )
                    # ذخیره پیام‌ها در حافظه
                    self.memory.add_message(session_id, "user", user_message)
                    self.memory.add_message(
                        session_id, "assistant", first_question_text
                    )
                    return [
                        {
                            "text": first_question_text,
                            "facialExpression": "default",
                            "animation": "Talking_0",
                        }
                    ], session_id

                # ذخیره پیام‌ها در حافظه
                self.memory.add_message(session_id, "user", user_message)

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
                            language=language,
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
                            language=language,
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

    def _apply_booking_logic_and_maybe_override(
        self,
        user_message: str,
        session_id: str,
        booking_state: BookingState,
        messages: List[Dict],
        language: str = "fa",
    ) -> List[Dict]:
        """Apply step progression without validation for any input."""
        current_key, _ = booking_state.get_next_question()
        logger.info(f"Current booking step: {current_key}")

        # Save input and move to next step for all questions
        if current_key != "completed":
            logger.info(f"Processing input for {current_key}")
            booking_state.update_state(current_key, user_message)

            # Get the next question
            next_key, _ = booking_state.get_next_question()
            if next_key != "completed":
                next_question_text = self._get_question_text_for_key(next_key, language)
                return [
                    {
                        "text": next_question_text,
                        "facialExpression": "default",
                        "animation": "Talking_0",
                    }
                ]
            else:
                # All questions completed - show completion message
                completion_message = self._get_question_text_for_key(
                    "completed", language
                )
                return [
                    {
                        "text": completion_message,
                        "facialExpression": "smile",
                        "animation": "Talking_1",
                    }
                ]

        # Special transfer message if origin_airport is Imam Khomeini
        # Only show this message when all steps are completed
        try:
            if current_key == "completed" and booking_state.collected_data.get(
                "origin_airport"
            ) in [
                "امام خمینی",
                "امام خميني",
                "Imam Khomeini",
            ]:
                transfer_message = (
                    "By the way, if you're currently at Imam Khomeini Airport, I can arrange for the transfer team to pick you up at the exit door and your transfer will be my treat, what do you think my friend?"
                    if language == "en"
                    else "راستی اگه الان فرودگاه امام خمینی هستی می‌تونم هماهنگ کنم بچه‌های ترنسفر درب خروجی سوارت کنند و ترنسفرت رو مهمون من باشی، نظرت چیه دوست من؟"
                )
                messages.append(
                    {
                        "text": transfer_message,
                        "facialExpression": "smile",
                        "animation": "Talking_2",
                    }
                )
        except Exception:
            pass

        # Add final QR code message when conversation is completed
        if current_key == "completed":
            qr_message = (
                "You can view and modify the information in the form through the QR code."
                if language == "en"
                else "از طریق کیو آر کد می‌توانی اطلاعات را در فرم ببینی و آن را اصلاح کنی."
            )
            messages.append(
                {
                    "text": qr_message,
                    "facialExpression": "smile",
                    "animation": "Talking_1",
                }
            )

        return messages

    @staticmethod
    def _get_question_text_for_key(key: str, language: str = "fa") -> str:
        if language == "en":
            en_mapping: Dict[str, str] = {
                "origin_airport": "Please provide the origin airport name.",
                "travel_type": "Is your flight arriving at the airport or departing?",
                "travel_date": "Please provide the travel date (Gregorian calendar).",
                "passenger_count": "What is the exact number of passengers?",
                "passenger_name": "Please provide the passenger's full name.",
                "national_id": "Please provide the passenger's national ID.",
                "flight_number": "Please provide the flight number.",
                "passport_number": "Please provide the passenger's passport number.",
                "baggage_count": "Please provide the number of bags.",
                "passenger_type": "Is the passenger an adult or infant?",
                "gender": "What is the passenger's gender?",
                "additional_info": "Any additional information you would like to provide?",
                "completed": "Excellent! All your information has been received. You can now view and modify the information through the QR code if needed.",
            }
            return en_mapping.get(key, "")
        else:
            fa_mapping: Dict[str, str] = {
                "origin_airport": "نام فرودگاه مبدا رو بفرمایید.",
                "travel_type": "پروازتون ورودی به فرودگاهه یا خروجی؟",
                "travel_date": "تاریخ سفر رو به میلادی بفرمایید.",
                "passenger_count": "تعداد دقیق مسافران چند نفر است؟",
                "passenger_name": "نام و نام خانوادگی مسافر رو بفرمایید.",
                "national_id": "کد ملی مسافر رو بفرمایید.",
                "flight_number": "شماره پرواز رو بفرمایید.",
                "passport_number": "شماره گذرنامه مسافر رو بفرمایید.",
                "baggage_count": "تعداد چمدان‌ها رو بفرمایید.",
                "passenger_type": "نوع مسافر بزرگسال است یا نوزاد؟",
                "gender": "جنسیت مسافر چیه؟",
                "additional_info": "توضیح اضافه‌ای که می‌خواید بگید؟",
                "completed": "عالی! همه اطلاعات شما دریافت شد. حالا می‌توانید از طریق کیو آر کد اطلاعات را مشاهده و در صورت نیاز اصلاح کنید.",
            }
            return fa_mapping.get(key, "")
