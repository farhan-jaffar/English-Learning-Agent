from django.db import models
from core.base_models import BaseTimeModel
from core.choices import CEFRLevel, SkillFocus, ExerciseSourceType
from apps.authentication.models import Language

class TopicTag(BaseTimeModel):
    """
    Normalized topic tag for categorizing exercises and analytics (e.g. 'Travel', 'Business').
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Topic Tag'
        verbose_name_plural = 'Topic Tags'

    def __str__(self) -> str:
        return str(self.name)


class Exercise(BaseTimeModel):
    """
    Spoken language practice exercise prompt tied to a target Language.
    """
    # Retained as class references for backwards compatibility; prefer core.choices directly.
    SkillFocus = SkillFocus
    SourceType = ExerciseSourceType


    id = models.BigAutoField(primary_key=True)
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='exercises',
        help_text="Target language of the exercise prompt"
    )
    title = models.CharField(max_length=200)
    prompt_text = models.TextField(help_text="Spoken prompt instructions for the learner")
    skill_focus = models.CharField(
        max_length=20,
        choices=SkillFocus.choices,
        default=SkillFocus.MIXED,
        help_text="Primary skill focus of the prompt"
    )
    cefr_level = models.CharField(
        max_length=2,
        choices=CEFRLevel.choices,
        default=CEFRLevel.B1,
        help_text="Target CEFR level (A1 to C2)"
    )
    topic_tags = models.ManyToManyField(
        TopicTag,
        related_name='exercises',
        blank=True,
        help_text="Normalized topic category tags"
    )
    source = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.STATIC
    )
    vocabulary_hints = models.JSONField(
        default=list,
        blank=True,
        help_text="Target vocabulary list used for prompt context and transcription biasing"
    )
    min_duration_seconds = models.PositiveIntegerField(
        default=15,
        help_text="Suggested minimum speaking duration in seconds"
    )
    max_duration_seconds = models.PositiveIntegerField(
        default=120,
        help_text="Suggested maximum speaking duration in seconds"
    )

    class Meta:
        ordering = ['cefr_level', 'skill_focus', 'id']
        verbose_name = 'Exercise'
        verbose_name_plural = 'Exercises'

    def __str__(self) -> str:
        lang_code = self.language.code if self.language_id else '??'
        return f"[{lang_code} | {self.cefr_level} - {self.get_skill_focus_display()}] {self.title}"

