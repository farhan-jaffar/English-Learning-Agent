"""
Adaptive exercise generator creating tailored speaking prompts for remediation and growth.
"""

import logging
from typing import Optional, List, Tuple
from apps.authentication.models import Language
from apps.exercises.models import Exercise, TopicTag
from core.choices import ExerciseSourceType, SkillFocus, CEFRLevel
from ai_engine.config import AIEngineConfig
from ai_engine.exceptions import GenerationError
from ai_engine.providers.gemini import GeminiProvider
from ai_engine.prompts.exercise import (
    EXERCISE_GENERATOR_SYSTEM_PROMPT,
    build_exercise_generation_prompt
)
from ai_engine.schemas.exercise import GeneratedExercise

logger = logging.getLogger(__name__)

class AdaptiveExerciseGenerator:
    """Generates and persists personalized practice exercises targeting learner weaknesses."""

    def __init__(self, provider: Optional[GeminiProvider] = None):
        self.provider = provider or GeminiProvider()

    def generate_and_save(
        self,
        language: Language,
        cefr_level: str = "B1",
        skill_focus: str = "grammar",
        target_weakness: str = "",
        preferred_topic: str = "",
        avoid_recent_titles: Optional[List[str]] = None
    ) -> Exercise:
        """
        Generates an exercise tailored to target weakness and stores it in the database.
        Returns the saved Exercise model instance.
        """
        prompt = build_exercise_generation_prompt(
            cefr_level=cefr_level,
            skill_focus=skill_focus,
            target_weakness=target_weakness,
            preferred_topic=preferred_topic,
            avoid_recent_titles=avoid_recent_titles
        )

        generated_schema: Optional[GeneratedExercise] = None

        if self.provider.is_configured():
            try:
                resp = self.provider.generate_structured(
                    prompt=prompt,
                    response_schema=GeneratedExercise,
                    system_instruction=EXERCISE_GENERATOR_SYSTEM_PROMPT,
                    model=AIEngineConfig.EXERCISE_MODEL,
                    temperature=0.7
                )
                generated_schema = resp.parsed
            except Exception as e:
                logger.warning(f"Gemini exercise generation failed: {e}. Falling back to rule-based template.")

        if not generated_schema:
            generated_schema = self._fallback_exercise(cefr_level, skill_focus, target_weakness)

        # Normalize skill_focus to model choice
        valid_skills = {s.value: s.value for s in SkillFocus}
        skill_val = valid_skills.get(generated_schema.skill_focus.lower(), SkillFocus.MIXED.value)

        # Normalize CEFR
        valid_cefr = {c.value: c.value for c in CEFRLevel}
        cefr_val = valid_cefr.get(generated_schema.cefr_level.upper(), CEFRLevel.B1.value)

        # Persist Exercise instance
        exercise = Exercise.objects.create(
            language=language,
            title=generated_schema.title,
            prompt_text=generated_schema.prompt_text,
            skill_focus=skill_val,
            cefr_level=cefr_val,
            source=ExerciseSourceType.GENERATED,
            vocabulary_hints=generated_schema.vocabulary_hints or [],
            min_duration_seconds=generated_schema.min_duration_seconds or 20,
            max_duration_seconds=generated_schema.max_duration_seconds or 90
        )

        # Link Topic Tag
        topic_name = generated_schema.topic or "Everyday Practice"
        topic_tag, _ = TopicTag.objects.get_or_create(name=topic_name.title())
        exercise.topic_tags.add(topic_tag)

        return exercise

    def _fallback_exercise(
        self,
        cefr_level: str,
        skill_focus: str,
        target_weakness: str
    ) -> GeneratedExercise:
        """Deterministic template when LLM generation is unavailable."""
        weakness_display = target_weakness or "natural flow"
        return GeneratedExercise(
            title=f"Mastering {weakness_display.title()}",
            prompt_text=(
                f"Describe a recent experience where you faced a surprise challenge and how you handled it. "
                f"Pay special attention to using accurate {weakness_display} structures and clear descriptive details."
            ),
            skill_focus=skill_focus if skill_focus in [s.value for s in SkillFocus] else "grammar",
            cefr_level=cefr_level if cefr_level in [c.value for c in CEFRLevel] else "B1",
            vocabulary_hints=["unexpected", "resolved", "collaborated", "ultimately"],
            topic="Personal Experience",
            min_duration_seconds=20,
            max_duration_seconds=90
        )
