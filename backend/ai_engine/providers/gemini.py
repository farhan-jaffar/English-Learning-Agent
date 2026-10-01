"""
Google Gemini implementation of LLMProvider using google-genai SDK.
"""

import json
import logging
import time
from typing import Any, Type, TypeVar
from pydantic import BaseModel

from google import genai
from google.genai import types

from ai_engine.config import AIEngineConfig
from ai_engine.exceptions import ProviderError
from .base import LLMProvider, ProviderResponse

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseModel)

class GeminiProvider(LLMProvider):
    """Encapsulates interaction with the Google Gemini API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or AIEngineConfig.GEMINI_API_KEY
        self._client = None

    @property
    def client(self) -> genai.Client:
        """Lazy-initialize GenAI client."""
        if not self.api_key:
            raise ProviderError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your environment or Django settings."
            )
        if self._client is None:
            try:
                self._client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        retry_options=types.HttpRetryOptions(attempts=1)
                    )
                )
            except Exception as e:
                raise ProviderError(f"Failed to initialize Google GenAI Client: {e}") from e
        return self._client

    def is_configured(self) -> bool:
        """Returns True if a real API key is present and not a dummy/placeholder."""
        if not self.api_key or not self.api_key.strip():
            return False
        lower_key = self.api_key.strip().lower()
        dummy_prefixes = ("your-", "dummy-", "test-", "mock-", "example-", "placeholder-")
        return not any(lower_key.startswith(p) for p in dummy_prefixes)

    def _call_with_fallback(self, contents, config, primary_model: str):
        """
        Executes models.generate_content with fast failover across available models.
        Immediately switches to alternative models if a model is overloaded (503) or rate-limited (429),
        avoiding long socket hangs.
        """
        is_audio = False
        if isinstance(contents, list):
            for item in contents:
                if hasattr(item, 'mime_type') and getattr(item, 'mime_type', '').startswith('audio/'):
                    is_audio = True
                    break

        candidate_models = [primary_model]
        if is_audio:
            priority_models = [
                'gemini-3.5-transcribe',
                'gemini-3.6-flash',
                'gemini-3.1-flash-lite',
                'gemini-flash-latest',
                'gemini-3.7-flash',
                'gemini-flash-lite-latest'
            ]
        else:
            priority_models = [
                'gemini-3.6-flash',
                'gemini-3.1-flash-lite',
                'gemini-3.7-flash',
                'gemini-flash-latest',
                'gemini-3.5-flash-lite',
                'gemini-flash-lite-latest'
            ]

        for m in priority_models:
            if m not in candidate_models:
                candidate_models.append(m)

        last_exception = None
        for current_model in candidate_models:
            try:
                call_config = config
                if 'transcribe' in current_model and config:
                    cfg_dict = {}
                    if getattr(config, 'temperature', None) is not None:
                        cfg_dict['temperature'] = config.temperature
                    # gemini-3.5-transcribe does not accept system_instruction or JSON schemas
                    call_config = types.GenerateContentConfig(**cfg_dict)

                response = self.client.models.generate_content(
                    model=current_model,
                    contents=contents,
                    config=call_config
                )
                return response, current_model
            except Exception as e:
                last_exception = e
                err_str = str(e)
                logger.warning(
                    f"[Gemini Failover] Model '{current_model}' failed ({err_str[:70]}...). "
                    f"Instantly switching to next model in pool."
                )
                continue

        if last_exception is not None:
            raise last_exception
        raise ProviderError(f"All candidate models failed: {candidate_models}")

    def generate_text(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str = "",
        temperature: float = 0.7
    ) -> ProviderResponse:
        model_name = model or AIEngineConfig.DEFAULT_MODEL
        start_time = time.perf_counter()

        config_args = {"temperature": temperature}
        if system_instruction:
            config_args["system_instruction"] = system_instruction
        config = types.GenerateContentConfig(**config_args)

        try:
            response, resolved_model = self._call_with_fallback(prompt, config, model_name)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0

            raw_text = response.text or ""
            return ProviderResponse(
                raw_text=raw_text,
                parsed=None,
                model_name=resolved_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Gemini generate_text failed ({model_name}): {e}", exc_info=True)
            raise ProviderError(f"Gemini generate_text error: {e}") from e

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str = "",
        model: str = "",
        temperature: float = 0.2
    ) -> ProviderResponse:
        model_name = model or AIEngineConfig.DEFAULT_MODEL
        start_time = time.perf_counter()

        config_args = {
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_schema": response_schema
        }
        if system_instruction:
            config_args["system_instruction"] = system_instruction
        config = types.GenerateContentConfig(**config_args)

        try:
            response, resolved_model = self._call_with_fallback(prompt, config, model_name)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0

            raw_text = response.text or ""
            parsed_obj = None
            if hasattr(response, 'parsed') and response.parsed is not None:
                parsed_obj = response.parsed
            elif raw_text:
                parsed_obj = response_schema.model_validate_json(raw_text)

            return ProviderResponse(
                raw_text=raw_text,
                parsed=parsed_obj,
                model_name=resolved_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms
            )
        except Exception as e:
            logger.error(f"Gemini generate_structured failed ({model_name}): {e}", exc_info=True)
            raise ProviderError(f"Gemini generate_structured error: {e}") from e

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
        model_name = model or AIEngineConfig.TRANSCRIPTION_MODEL
        start_time = time.perf_counter()

        config_args = {"temperature": temperature}
        if system_instruction:
            config_args["system_instruction"] = system_instruction
        if response_schema is not None:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_args)

        # Build multimodal contents: audio Part + prompt Part
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type or "audio/webm")
        contents = [audio_part, prompt]

        try:
            response, resolved_model = self._call_with_fallback(contents, config, model_name)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0

            raw_text = response.text or ""
            if not raw_text and hasattr(response, 'candidates') and response.candidates:
                for cand in response.candidates:
                    if hasattr(cand, 'content') and hasattr(cand.content, 'parts') and cand.content.parts:
                        for part in cand.content.parts:
                            if hasattr(part, 'text') and part.text:
                                raw_text += part.text
                            elif hasattr(part, 'audio_transcription') and getattr(part.audio_transcription, 'text', None):
                                raw_text += part.audio_transcription.text

            raw_text = raw_text.strip()
            parsed_obj = None
            if response_schema:
                if hasattr(response, 'parsed') and response.parsed is not None:
                    parsed_obj = response.parsed
                elif raw_text:
                    try:
                        parsed_obj = response_schema.model_validate_json(raw_text)
                    except Exception:
                        pass

            return ProviderResponse(
                raw_text=raw_text,
                parsed=parsed_obj,
                model_name=resolved_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms
            )
        except Exception as e:
            logger.error(f"Gemini generate_from_audio failed ({model_name}): {e}", exc_info=True)
            raise ProviderError(f"Gemini generate_from_audio error: {e}") from e

