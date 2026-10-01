"""
Custom exceptions for the AI Engine.
"""

class AIEngineError(Exception):
    """Base exception for all AI Engine errors."""
    pass

class ProviderError(AIEngineError):
    """Raised when upstream LLM/ASR provider (e.g., Gemini) returns an error or fails."""
    pass

class TranscriptionError(AIEngineError):
    """Raised when audio transcription or word timestamp extraction fails."""
    pass

class AssessmentError(AIEngineError):
    """Raised when linguistic evaluation or parsing fails."""
    pass

class AgentDecisionError(AIEngineError):
    """Raised when the adaptive agent fails to formulate a valid decision."""
    pass

class GenerationError(AIEngineError):
    """Raised when exercise or conversation generation fails."""
    pass
