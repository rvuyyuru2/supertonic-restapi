"""
OpenAI voice names → Supertonic style names (F1-F5 female, M1-M5 male).
Maps all 13 OpenAI TTS voices to Supertonic's 10 voice styles.
"""

# OpenAI voice names → Supertonic style names
OPENAI_TO_SUPERTONIC = {
    # Original 6
    "alloy": "F1",
    "echo": "M1",
    "fable": "M2",
    "onyx": "M3",
    "nova": "F2",
    "shimmer": "F3",
    # Extended (ash, ballad, cedar, coral, marin, sage, verse)
    "ash": "F4",
    "ballad": "F4",
    "cedar": "M4",
    "coral": "F5",
    "marin": "F5",
    "sage": "M4",
    "verse": "M5",
}

OPENAI_VOICE_NAMES = list(OPENAI_TO_SUPERTONIC.keys())
