import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AnimationType(Enum):
    STANDING_IDLE = "StandingIdle"
    STANDING_GREETING = "StandingGreeting"
    THUMBS_UP = "ThumbsUp"
    POINTING = "Pointing"
    TALKING = "Talking"
    CLAPPING = "Clapping"
    THOUGHTFUL_HEAD = "ThoughtfulHead"
    BOW = "Bow"
    LAUGHING = "Laughing"
    THANKFUL = "Thankful"
    THINKING = "Thinking"


class AnimationSelector:
    """Intelligent animation selection based on text content and context"""

    def __init__(self):
        # Define patterns for different emotional contexts
        self.patterns = {
            # Greeting patterns
            "greeting": {
                "patterns": [
                    r"سلام|خوش آمدید|خوش آمدی|welcome|hello|hi|good morning|good afternoon|good evening",
                    r"چطورید|چطوری|how are you|how do you do",
                    r"بفرمایید|please come|please sit",
                ],
                "animation": AnimationType.STANDING_GREETING,
                "priority": 1,
            },
            # Positive/Approval patterns
            "positive": {
                "patterns": [
                    r"عالی|ممتاز|بسیار خوب|excellent|great|perfect|wonderful|fantastic",
                    r"درست|صحیح|correct|right|yes|بله|آره",
                    r"موافقم|agree|exactly|precisely",
                    r"ممنون|تشکر|thank you|thanks|appreciate",
                ],
                "animation": AnimationType.THUMBS_UP,
                "priority": 2,
            },
            # Thankful/Grateful patterns
            "thankful": {
                "patterns": [
                    r"ممنونم|متشکرم|تشکر می‌کنم|thank you very much|many thanks",
                    r"قدردانی|appreciation|grateful|appreciate",
                    r"لطف کردید|kind of you|very kind",
                ],
                "animation": AnimationType.THANKFUL,
                "priority": 2,
            },
            # Laughing/Humor patterns
            "laughing": {
                "patterns": [
                    r"هاها|ههه|خخخ|haha|hehe|lol|funny|joke",
                    r"خنده|laugh|smile|خندیدن",
                    r"شوخی|joke|humor|funny",
                ],
                "animation": AnimationType.LAUGHING,
                "priority": 3,
            },
            # Thinking/Processing patterns
            "thinking": {
                "patterns": [
                    r"بگذارید فکر کنم|let me think|let me see|ببینم",
                    r"در حال بررسی|checking|processing|بررسی می‌کنم",
                    r"لحظه|moment|wait|صبر کنید",
                    r"think about|considering|processing|analyzing",
                ],
                "animation": AnimationType.THINKING,
                "priority": 4,
            },
            # Thoughtful/Consideration patterns
            "thoughtful": {
                "patterns": [
                    r"فکر می‌کنم|I think|I believe|I suppose",
                    r"احتمالاً|probably|maybe|perhaps|شاید",
                    r"نظر|opinion|consider|در نظر بگیرید",
                ],
                "animation": AnimationType.THOUGHTFUL_HEAD,
                "priority": 5,
            },
            # Pointing/Instruction patterns
            "pointing": {
                "patterns": [
                    r"این|this|that|آن|here|there|اینجا|آنجا",
                    r"نگاه کنید|look|see|ببینید|please look|check this",
                    r"به سمت|toward|direction|مسیر",
                    r"فرم|form|صفحه|page|section|fill out|complete this",
                ],
                "animation": AnimationType.POINTING,
                "priority": 6,
            },
            # Clapping/Celebration patterns
            "clapping": {
                "patterns": [
                    r"تبریک|congratulations|congrats|well done",
                    r"موفقیت|success|achievement|کامیابی",
                    r"تمام شد|finished|completed|done|تمام",
                ],
                "animation": AnimationType.CLAPPING,
                "priority": 7,
            },
            # Bow/Respect patterns
            "bow": {
                "patterns": [
                    r"عذرخواهی|apologize|sorry|ببخشید",
                    r"احترام|respect|honor|تکریم",
                    r"خداحافظ|goodbye|farewell|خداحافظی",
                ],
                "animation": AnimationType.BOW,
                "priority": 8,
            },
            # Talking/Explanation patterns
            "talking": {
                "patterns": [
                    r"توضیح|explain|description|شرح",
                    r"بگویم|tell you|inform|اطلاع",
                    r"نکته|point|important|مهم",
                    r"راهنمایی|guide|help|کمک",
                    r"information|details|about|regarding",
                ],
                "animation": AnimationType.TALKING,
                "priority": 9,
            },
        }

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
