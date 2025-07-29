import os
import json
import logging
import requests

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not set")
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.api_url = "https://api.openai.com/v1/chat/completions"

    def get_girlfriend_response(self, user_message: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with open("api/constants/knowledge_base.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()

        payload = {
            "model": "gpt-3.5-turbo-1106",
            "max_tokens": 1000,
            "temperature": 0.6,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. "
                        "You will always reply with a JSON array of messages. With a maximum of 3 messages. "
                        "Each message has a text, facialExpression, and animation property. "
                        "The different facial expressions are: smile, sad, angry, surprised, funnyFace, and default. "
                        "The different animations are: Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, and Angry. "
                    ),
                },
                {"role": "user", "content": user_message or "Hello"},
            ],
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

            messages = json.loads(content)
            if "messages" in messages:
                return messages["messages"]
            return messages

        except Exception as e:
            logger.error(f"Error in OpenAI service: {e}")
            raise
