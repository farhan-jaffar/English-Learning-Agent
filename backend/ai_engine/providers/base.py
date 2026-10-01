"""
Abstract Base Provider contract for LLM operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class ProviderResponse:
    """Wrapper encapsulating completion result, parsed payload, and telemetry metrics."""
    def __init__(
        self,
        raw_text: str,
        parsed: Any = None,
        model_name: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0
    ):
        self.raw_text = raw_text
        self.parsed = parsed
        self.model_name = model_name
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.latency_ms = latency_ms

class LLMProvider(ABC):
    """Abstract interface decoupling business logic from upstream AI providers."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str = "",
        temperature: float = 0.7
    ) -> ProviderResponse:
        """Generate unstructured text completion."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str = "",
        model: str = "",
        temperature: float = 0.2
    ) -> ProviderResponse:
        """Generate structured completion validated against a Pydantic schema."""
        pass

    @abstractmethod
    def generate_from_audio(
        self,
        audio_bytes: bytes,
        mime_type: str,
        prompt: str,
        response_schema: Type[T] = None,
        system_instruction: str = "",
        model: str = "",
        temperature: float = 0.2
    ) -> ProviderResponse:
        """Process multimodal audio input and return text or structured output."""
        pass
