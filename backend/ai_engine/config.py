"""
Central configuration for AI Engine components.
"""

import os
from django.conf import settings

class AIEngineConfig:
    """Config parameters and default model settings for AI services."""
    
    # API credentials
    GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY', '')
    
    # Model versions
    DEFAULT_MODEL = getattr(settings, 'GEMINI_MODEL', 'gemini-3.6-flash')
    TRANSCRIPTION_MODEL = getattr(settings, 'GEMINI_TRANSCRIPTION_MODEL', 'gemini-3.5-transcribe')
    EVALUATION_MODEL = getattr(settings, 'GEMINI_EVALUATION_MODEL', 'gemini-3.6-flash')
    DIALOGUE_MODEL = getattr(settings, 'GEMINI_DIALOGUE_MODEL', 'gemini-3.6-flash')
    EXERCISE_MODEL = getattr(settings, 'GEMINI_EXERCISE_MODEL', 'gemini-3.6-flash')

    # Pedagogical & speech thresholds
    PAUSE_THRESHOLD_SECONDS = 0.45  # Gap >= 450ms considered a pause
    WEAKNESS_PERSISTENCE_THRESHOLD = 3  # Minimum occurrences before marking as persistent weakness
    RECENCY_WINDOW_SESSIONS = 5  # Number of past sessions considered for adaptive decisions
    
    # Common conversational filler words in English
    COMMON_FILLERS = frozenset({
        'um', 'uh', 'er', 'ah', 'like', 'you know', 'so', 'actually', 
        'basically', 'literally', 'i mean', 'sort of', 'kind of', 'right', 'well'
    })
    
    CEFR_LEVELS = ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')
