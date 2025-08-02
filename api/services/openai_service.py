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
        """Add a message to the conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        self.conversations[session_id].append(message)

        # Keep only the last max_messages
        if len(self.conversations[session_id]) > self.max_messages:
            self.conversations[session_id] = self.conversations[session_id][
                -self.max_messages :
            ]

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return self.conversations.get(session_id, [])

    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]


class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not set")
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.memory = AgentMemory()

    def get_girlfriend_response(
        self, user_message: str, session_id: Optional[str] = None
    ):
        # Generate session_id if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with open("api/constants/knowledge_base.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()

        # Get conversation history
        conversation_history = self.memory.get_conversation_history(session_id)

        # Build messages array with system prompt and conversation history
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Binad, an AI assistant for airport services at Imam Khomeini and Mashhad airports, as defined in the following knowledge base. "
                    "Follow the rules and steps outlined in the knowledge base strictly, including the conversational tone, step-by-step information gathering, and restrictions. "
                    "Always reply with a JSON array of up to 3 messages. Each message has a text, facialExpression, and animation property. "
                    "Facial expressions: smile, sad, angry, surprised, funnyFace, default. "
                    "Animations: Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, Angry. "
                    "Here is the knowledge base:\n" + system_prompt
                ),
            }
        ]

        # Add conversation history
        messages.extend(conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message or "Hello"})

        payload = {
            "model": "gpt-3.5-turbo-1106",
            "max_tokens": 1000,
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

            # Add user message to memory
            self.memory.add_message(session_id, "user", user_message)

            # Add assistant response to memory
            self.memory.add_message(session_id, "assistant", content)

            response_data = json.loads(content)
            if "messages" in response_data:
                return response_data["messages"], session_id
            return response_data, session_id

        except Exception as e:
            logger.error(f"Error in OpenAI service: {e}")
            raise

    def clear_memory(self, session_id: str = "default"):
        """Clear conversation memory for a session"""
        self.memory.clear_conversation(session_id)

    def get_conversation_history(self, session_id: str = "default") -> List[Dict]:
        """Get conversation history for debugging"""
        return self.memory.get_conversation_history(session_id)
