"""
Learner state builder synthesizing compact pedagogical state from database models.
"""

from typing import Optional
from apps.authentication.models import User, UserLanguage, Language
from apps.exercises.models import Exercise
from apps.recordings.models import AnalysisResult
from ai_engine.schemas.learner import LearnerState
from .weaknesses import WeaknessTracker

class LearnerStateBuilder:
    """Builds a compact LearnerState object for prompt injection and policy evaluation."""

    @staticmethod
    def build(user: User, language_code: Optional[str] = None) -> LearnerState:
        # Resolve target user language profile
        if language_code:
            user_language = user.user_languages.filter(
                language__code=language_code
            ).select_related('language').first()
        else:
            user_language = user.primary_user_language

        if not user_language:
            # Fallback to English
            english = Language.objects.filter(code='en-US').first()
            if not english:
                english, _ = Language.objects.get_or_create(code='en-US', defaults={'name': 'English (US)'})
            user_language, _ = UserLanguage.objects.get_or_create(
                user=user,
                language=english,
                defaults={'is_primary': True, 'is_learning': True}
            )

        lang = user_language.language

        # Query recent analyses
        recent_analyses = list(
            AnalysisResult.objects.filter(
                recording__turn__session__user_language=user_language,
                is_current=True
            ).order_by('-created_at')[:5]
        )

        # Average WPM across recent sessions
        wpm_values = []
        for an in recent_analyses:
            metrics = an.fluency_metrics or {}
            wpm = metrics.get('wpm')
            if wpm and isinstance(wpm, (int, float)) and wpm > 0:
                wpm_values.append(wpm)
        avg_wpm = round(sum(wpm_values) / len(wpm_values), 1) if wpm_values else 0.0

        # Retrieve weakness history
        weaknesses = WeaknessTracker.get_learner_weaknesses(user=user, language=lang)
        recurring_tags = [w.tag for w in weaknesses if w.is_recurring]

        # Retrieve recent exercises attempted
        recent_exercise_qs = Exercise.objects.filter(
            conversation_sessions__user_language=user_language
        ).order_by('-conversation_sessions__created_at').distinct()

        recent_exercise_ids = list(dict.fromkeys(recent_exercise_qs.values_list('id', flat=True)[:20]))
        recent_topics = list(
            recent_exercise_qs.values_list('topic_tags__name', flat=True).filter(topic_tags__name__isnull=False)[:5]
        )

        return LearnerState(
            user_id=user.id,
            username=user.username,
            target_language=lang.code,
            current_cefr=user_language.current_cefr_level,
            target_goal=user_language.target_goal or 'Conversational Fluency',
            total_sessions_completed=user_language.total_sessions_completed,
            recent_average_wpm=avg_wpm,
            weaknesses=weaknesses,
            recurring_weakness_tags=recurring_tags,
            recent_topics=recent_topics,
            recent_exercise_ids=recent_exercise_ids
        )
