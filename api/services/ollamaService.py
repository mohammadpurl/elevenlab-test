import os
import json
import logging
import requests
import uuid
from typing import List, Dict, Optional
from datetime import datetime
import re

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


class OllamaService:
    _instance = None
    _memory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OllamaService, cls).__new__(cls)
            cls._memory = AgentMemory()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.api_url = "http://localhost:11434/api/chat"
            self.model_name = "llama3"  # یا هر مدلی که اجرا کردید
            self.memory = OllamaService._memory
            self.initialized = True

    def get_assistant_response(
        self, user_message: str, session_id: Optional[str] = None
    ):
        if session_id is None:
            session_id = str(uuid.uuid4())

        with open("api/constants/knowledge_base.txt", "r", encoding="utf-8") as f:
            knowledge_base = f.read()

        system_prompt = f"""
تو یک دستیار هوش مصنوعی به نام «نکسا» هستی که خدمات فرودگاهی در فرودگاه امام خمینی را ارائه می‌دهی. 
تو فقط به زبان فارسی صحبت می‌کنی، حتی اگر کاربر به زبان انگلیسی پیام بدهد. پاسخ‌ها باید همیشه فارسی باشند.

# قوانین مهم:
- همیشه در نقش بمون، فقط درباره موضوعات تعریف‌شده در دانش‌نامه حرف بزن
- در هر بار فقط یک سوال را بپرس و هرگز پیام های غیر مربوط به سوال را نپرس

- پاسخ‌ها باید مرحله‌به‌مرحله، با لحن محاوره‌ای، مهربان و حداکثر ۳ جمله‌ای باشن
- اگر اطلاعاتی ناقص بود، فقط یک بار با احترام تکرارش کن
 - اگر کاربر جوک خواست یا خودش جوک گفت، پاسخ کوتاه بده و «facialExpression» را «funnyFace» و در صورت مناسب «animation» را «Laughing» قرار بده.

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

        messages = [{"role": "system", "content": system_prompt}]
        messages += self.memory.get_conversation_history(session_id)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model_name,
            "messages": messages,
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            response_text = response.text
            print("🔍 Ollama raw response:\n", response_text)

            # استخراج خطوط JSON و چسباندن بخش content
            final_content = ""
            for line in response_text.strip().splitlines():
                try:
                    data = json.loads(line)
                    content_part = data.get("message", {}).get("content")
                    if content_part:
                        final_content += content_part
                except json.JSONDecodeError as e:
                    print("⛔ خطای JSON در خط:", line, " ➜ ", e)

            # ذخیره در حافظه
            self.memory.add_message(session_id, "user", user_message)
            self.memory.add_message(session_id, "assistant", final_content)

            # بازگشت متن نهایی به صورت ساده برای تست
            return [
                {
                    "text": final_content,
                    "facialExpression": "default",
                    "animation": "Idle",
                }
            ], session_id

        except Exception as e:
            logger.error(f"Error in Ollama service: {e}")
            return [
                {
                    "text": "متاسفم، مشکلی در پردازش درخواستت پیش اومد.",
                    "facialExpression": "sad",
                    "animation": "Idle",
                }
            ], session_id

    def clear_memory(self, session_id: str = "default"):
        self.memory.clear_conversation(session_id)

    def get_conversation_history(self, session_id: str = "default") -> List[Dict]:
        return self.memory.get_conversation_history(session_id)
