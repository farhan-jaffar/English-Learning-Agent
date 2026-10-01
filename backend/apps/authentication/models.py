from typing import TYPE_CHECKING, Any
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import warnings
from core.base_models import BaseTimeModel
from core.choices import CEFRLevel

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class Language(BaseTimeModel):
    """
    Supported natural language (e.g. English, Spanish).
    Used to normalize language across user profiles, exercises, and weakness tags.
    """
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="IETF language tag, e.g. 'en-US', 'es-ES'"
    )
    name = models.CharField(max_length=100, help_text="Human-readable language name")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

class User(AbstractUser, BaseTimeModel):
    """
    Custom user model decoupled from specific language proficiency.
    Language-specific proficiency is managed explicitly via UserLanguage relationships.
    """
    # Retained as class reference for backwards compatibility; prefer core.choices.CEFRLevel directly.
    CEFRLevel = CEFRLevel

    if TYPE_CHECKING:
        user_languages: Any

    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    # is_active inherited from AbstractUser (defaults to True)
    # Note: Use is_active=False for soft deletes instead of hard CASCADE deletion.

    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        return str(self.username)


    @property
    def primary_user_language(self):
        """Retrieve the learner's primary active learning language profile."""
        return self.user_languages.filter(is_primary=True).select_related('language').first()

    @property
    def cefr_level(self):
        """
        Deprecated: Access user.primary_user_language.current_cefr_level explicitly instead.
        """
        primary = self.primary_user_language
        return primary.current_cefr_level if primary else CEFRLevel.B1

    @property
    def target_goal(self):
        """
        Deprecated: Access user.primary_user_language.target_goal explicitly instead.
        """
        primary = self.primary_user_language
        return primary.target_goal if primary else 'General Fluency'

    @property
    def native_language(self):
        """
        Deprecated: Access user's native UserLanguage relation directly instead.
        """
        native = self.user_languages.filter(is_native=True).select_related('language').first()
        return native.language.name if native else ''

class UserLanguage(BaseTimeModel):
    """
    Normalized relation between a User and a Language.
    Tracks proficiency, goals, and practice metrics atomically.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='user_languages'
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name='user_languages',
        help_text="Protected from deletion if active user language records reference it"
    )
    current_cefr_level = models.CharField(
        max_length=2,
        choices=CEFRLevel.choices,
        default=CEFRLevel.B1,
        help_text="Current CEFR proficiency level in this language"
    )
    target_goal = models.CharField(
        max_length=100,
        blank=True,
        default='General Fluency',
        help_text="Learner goal (e.g. 'Job Interview', 'IELTS', 'General Fluency')"
    )
    is_native = models.BooleanField(default=False, help_text="True if this is the learner's native tongue")
    is_learning = models.BooleanField(default=True, help_text="True if currently actively studying this language")
    is_primary = models.BooleanField(default=False, help_text="Designates learner's primary focus language")
    total_practice_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Accumulated practice time in seconds (must update via atomic F() expressions)"
    )
    total_sessions_completed = models.PositiveIntegerField(
        default=0,
        help_text="Total completed practice sessions (must update via atomic F() expressions)"
    )

    class Meta:
        ordering = ['user', '-is_primary', 'language']
        verbose_name = 'User Language'
        verbose_name_plural = 'User Languages'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'language'],
                name='unique_user_language'
            ),
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_primary=True),
                name='unique_primary_user_language'
            ),
        ]

    def __str__(self) -> str:
        role_label = "Primary" if self.is_primary else ("Native" if self.is_native else "Learning")
        return f"{self.user.username} - {self.language.code} [{self.current_cefr_level}] ({role_label})"

    def record_session_completion(self, duration_seconds: int = 0):
        """
        Atomically updates practice statistics using DB F() expressions to prevent race conditions.
        """
        duration = max(0, duration_seconds)
        UserLanguage.objects.filter(pk=self.pk).update(
            total_sessions_completed=models.F('total_sessions_completed') + 1,
            total_practice_seconds=models.F('total_practice_seconds') + duration,
            updated_at=timezone.now()
        )
        self.refresh_from_db(fields=['total_sessions_completed', 'total_practice_seconds', 'updated_at'])

