import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AnimationType(Enum):
    STANDING_IDLE = "StandingIdle"
    # STANDING_GREETING = "StandingGreeting"
    # THUMBS_UP = "ThumbsUp"
    # POINTING = "Pointing"
    # TALKING = "Talking"
    # CLAPPING = "Clapping"
    # THOUGHTFUL_HEAD = "ThoughtfulHead"
    # BOW = "Bow"
    # LAUGHING = "Laughing"
    # THANKFUL = "Thankful"
    # THINKING = "Thinking"


class AnimationSelector:
    """Intelligent animation selection based on text content and context"""

    def __init__(self):
        # Define patterns for different emotional contexts (temporarily disabled)
        # self.patterns = {
        #     "greeting": { ... },
        #     "positive": { ... },
        #     "thankful": { ... },
        #     "laughing": { ... },
        #     "thinking": { ... },
        #     "thoughtful": { ... },
        #     "pointing": { ... },
        #     "clapping": { ... },
        #     "bow": { ... },
        #     "talking": { ... },
        # }
        self.patterns = {}

        # Default animation for neutral content
        self.default_animation = AnimationType.STANDING_IDLE

    def select_animation(self, text: str, language: str = "fa") -> str:
        """
        Select the most appropriate animation based on text content

        Args:
            text: The text content to analyze
            language: Language code ("fa" for Persian, "en" for English)

        Returns:
            Selected animation name
        """
        if not text or not text.strip():
            return self.default_animation.value

        # Normalize text for better matching
        normalized_text = text.lower().strip()

        # Track matches with their priorities
        matches = []

        for context, config in self.patterns.items():
            for pattern in config["patterns"]:
                try:
                    if re.search(pattern, normalized_text, re.IGNORECASE):
                        matches.append(
                            {
                                "context": context,
                                "animation": config["animation"],
                                "priority": config["priority"],
                                "pattern": pattern,
                            }
                        )
                        break  # Only match one pattern per context
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                    continue

        if not matches:
            return self.default_animation.value

        # Sort by priority (lower number = higher priority)
        matches.sort(key=lambda x: x["priority"])

        selected_animation = matches[0]["animation"]
        logger.info(
            f"Selected animation '{selected_animation.value}' for text: '{text[:50]}...'"
        )

        return selected_animation.value

    def get_animation_for_context(self, context: str) -> str:
        """
        Get animation for specific context

        Args:
            context: Context name (greeting, positive, etc.)

        Returns:
            Animation name for the context
        """
        if context in self.patterns:
            return self.patterns[context]["animation"].value
        return self.default_animation.value

    def analyze_text_emotion(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to determine emotional context and appropriate animation

        Args:
            text: Text to analyze

        Returns:
            Dictionary with analysis results
        """
        animation = self.select_animation(text)

        # Determine if text is a question
        is_question = text.strip().endswith("?") or text.strip().endswith("؟")

        # Determine if text contains numbers or data
        has_data = bool(re.search(r"\d+", text))

        # Determine text length category
        word_count = len(text.split())
        if word_count <= 3:
            length_category = "short"
        elif word_count <= 10:
            length_category = "medium"
        else:
            length_category = "long"

        return {
            "animation": animation,
            "is_question": is_question,
            "has_data": has_data,
            "length_category": length_category,
            "word_count": word_count,
        }


# Global instance for reuse
animation_selector = AnimationSelector()
