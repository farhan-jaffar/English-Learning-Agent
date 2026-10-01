"""
AI Engine package for FluentFlow / EnglishLearningAgent.
Implements Gemini multimodal transcription, deterministic speech metrics,
linguistic assessment, learner state tracking, and adaptive agent orchestration.
"""

from .config import AIEngineConfig
from .exceptions import AIEngineError, ProviderError, TranscriptionError, AssessmentError
from .providers.gemini import GeminiProvider
from .transcription.gemini_transcriber import GeminiTranscriber
from .speech.metrics import SpeechMetricsCalculator
from .assessment.assessor import LinguisticAssessor
from .learner.state import LearnerStateBuilder
from .learner.weaknesses import WeaknessTracker
from .agent.orchestrator import AdaptiveAgentOrchestrator
from .generation.response_generator import ConversationalResponseGenerator
from .generation.exercise_generator import AdaptiveExerciseGenerator

__all__ = [
    'AIEngineConfig',
    'AIEngineError',
    'ProviderError',
    'TranscriptionError',
    'AssessmentError',
    'GeminiProvider',
    'GeminiTranscriber',
    'SpeechMetricsCalculator',
    'LinguisticAssessor',
    'LearnerStateBuilder',
    'WeaknessTracker',
    'AdaptiveAgentOrchestrator',
    'ConversationalResponseGenerator',
    'AdaptiveExerciseGenerator',
]
