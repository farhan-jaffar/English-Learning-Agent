"""
Linguistic assessment orchestrator using Gemini structured output.
Evaluates grammar, vocabulary, fluency, estimated CEFR level, and weakness tags.
"""

import logging
import re
from typing import Optional, Tuple, Dict, Any, List
from ai_engine.config import AIEngineConfig
from ai_engine.exceptions import AssessmentError, ProviderError
from ai_engine.providers.gemini import GeminiProvider
from ai_engine.prompts.assessment import (
    ASSESSMENT_SYSTEM_PROMPT,
    build_assessment_user_prompt
)
from ai_engine.schemas.assessment import (
    LinguisticAssessment,
    GrammarFeedback,
    GrammarCorrection,
    VocabularyFeedback,
    VocabSuggestion
)

logger = logging.getLogger(__name__)

class LinguisticAssessor:
    """Evaluates learner speech transcript using Gemini with validated Pydantic output."""

    def __init__(self, provider: Optional[GeminiProvider] = None):
        self.provider = provider or GeminiProvider()

    def assess(
        self,
        transcript: str,
        prompt_text: str = "",
        current_cefr: str = "B1",
        speech_metrics: Optional[Dict[str, Any]] = None,
        recent_weaknesses: Optional[List[str]] = None
    ) -> Tuple[LinguisticAssessment, Dict[str, Any]]:
        """
        Runs linguistic evaluation on transcript.
        Returns: (LinguisticAssessment, telemetry_dict)
        """
        if not transcript or not transcript.strip():
            raise AssessmentError("Transcript is empty; cannot perform linguistic assessment.")

        user_prompt = build_assessment_user_prompt(
            transcript=transcript,
            prompt_text=prompt_text,
            current_cefr=current_cefr,
            metrics_summary=speech_metrics,
            recent_weaknesses=recent_weaknesses
        )

        if not self.provider.is_configured():
            logger.error("[LinguisticAssessor] GEMINI_API_KEY is not configured.")
            raise AssessmentError("Gemini API key is not configured. Linguistic assessment requires a valid GEMINI_API_KEY.")

        try:
            resp = self.provider.generate_structured(
                prompt=user_prompt,
                response_schema=LinguisticAssessment,
                system_instruction=ASSESSMENT_SYSTEM_PROMPT,
                model=AIEngineConfig.EVALUATION_MODEL,
                temperature=0.2
            )

            assessment: LinguisticAssessment = resp.parsed
            if not assessment:
                raise AssessmentError("Gemini returned null parsed assessment.")

            telemetry = {
                "llm_model_version": resp.model_name,
                "latency_llm_ms": resp.latency_ms,
                "input_tokens": resp.input_tokens,
                "output_tokens": resp.output_tokens,
                "prompt_version": "v2.0-adaptive-eval",
                "raw_llm_response": {"status": "success", "evaluator": resp.model_name}
            }
            return assessment, telemetry

        except ProviderError as e:
            logger.error(f"[LinguisticAssessor] Gemini assessment provider error: {e}")
            raise AssessmentError(f"Linguistic assessment failed: {e}") from e
        except Exception as e:
            logger.error(f"[LinguisticAssessor ERROR] Unexpected error: {e}", exc_info=True)
            raise AssessmentError(f"Assessment failed: {e}") from e
