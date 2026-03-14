"""
Emotion Detector
Rule-based detection of emotional signals from user text.
Detects: frustrated, angry, confused, neutral.
Used to adjust FSM response tone and escalation behavior.
"""
import re
from dataclasses import dataclass
from typing import Tuple


@dataclass
class EmotionResult:
    emotion: str       # "neutral", "frustrated", "angry", "confused"
    intensity: float   # 0.0 to 1.0


# Keyword patterns for each emotion
EMOTION_PATTERNS = {
    "angry": [
        r"\b(furious|outraged|unacceptable|ridiculous|pathetic|terrible|horrible|worst|disgusting)\b",
        r"\b(i am angry|i'm angry|so angry|very angry|extremely angry)\b",
        r"\b(this is a scam|you are cheating|cheated me)\b",
    ],
    "frustrated": [
        r"\b(frustrated|annoyed|irritated|fed up|tired of|sick of|again|still|keep|keeps)\b",
        r"\b(why is it|how long|how many times|already told|already said|told you)\b",
        r"\b(not working|doesn't work|broken|issue|problem|error|wrong|incorrect)\b",
        r"\b(waited|waiting|been waiting|days ago|week ago|long time)\b",
    ],
    "confused": [
        r"\b(confused|don't understand|not sure|what do you mean|unclear|huh|pardon)\b",
        r"\b(what is|explain|can you clarify|not clear|lost)\b",
    ],
}


def detect_emotion(text: str) -> EmotionResult:
    """
    Detect the dominant emotional signal from user text.
    Returns EmotionResult with emotion label and intensity.
    """
    lower = text.lower().strip()
    scores = {"angry": 0, "frustrated": 0, "confused": 0}

    for emotion, patterns in EMOTION_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, lower)
            scores[emotion] += len(matches)

    # Determine dominant emotion
    max_emotion = max(scores, key=scores.get)
    max_score = scores[max_emotion]

    if max_score == 0:
        return EmotionResult(emotion="neutral", intensity=0.0)

    # Clamp intensity to 0-1 range
    intensity = min(1.0, max_score * 0.3)
    return EmotionResult(emotion=max_emotion, intensity=round(intensity, 2))
