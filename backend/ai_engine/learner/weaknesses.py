"""
Weakness intelligence service.
Combines current assessment, historical data, frequency, and recency to identify persistent weaknesses.
"""

from collections import Counter
from typing import List, Tuple
from django.db.models import QuerySet
from apps.authentication.models import Language, User
from apps.recordings.models import WeaknessTag, AnalysisResult
from ai_engine.config import AIEngineConfig
from ai_engine.schemas.learner import LearnerWeakness

class WeaknessTracker:
    """Manages pedagogical weakness tracking, normalization, and persistence detection."""

    @staticmethod
    def sync_analysis_weaknesses(
        analysis_result: AnalysisResult,
        weakness_names: List[str],
        language: Language
    ) -> List[WeaknessTag]:
        """
        Normalizes and links identified weaknesses to the AnalysisResult in the database.
        """
        if not language or not weakness_names:
            return []

        tags = []
        for raw_name in weakness_names:
            name = raw_name.strip()
            if not name:
                continue
            # Capitalize standard tag format
            clean_name = " ".join(word.capitalize() for word in name.split())
            tag, _ = WeaknessTag.objects.get_or_create(
                language=language,
                name=clean_name
            )
            tags.append(tag)

        analysis_result.weakness_tags.set(tags)
        return tags

    @staticmethod
    def get_learner_weaknesses(
        user: User,
        language: Language,
        session_window: int = AIEngineConfig.RECENCY_WINDOW_SESSIONS,
        persistence_threshold: int = AIEngineConfig.WEAKNESS_PERSISTENCE_THRESHOLD
    ) -> List[LearnerWeakness]:
        """
        Calculates frequency and recency of weaknesses across recent analysis results for the user and language.
        """
        recent_analyses = AnalysisResult.objects.filter(
            recording__turn__session__user_language__user=user,
            recording__turn__session__user_language__language=language,
            is_current=True
        ).prefetch_related('weakness_tags', 'recording__turn__session').order_by('-created_at')[:session_window]

        tag_counts = Counter()
        last_sessions = {}

        for analysis in recent_analyses:
            session_id = str(analysis.recording.turn.session_id) if (analysis.recording and analysis.recording.turn) else None
            for tag in analysis.weakness_tags.all():
                tag_counts[tag.name] += 1
                if tag.name not in last_sessions:
                    last_sessions[tag.name] = session_id

        weakness_list = []
        for tag_name, freq in tag_counts.most_common():
            is_recurring = (freq >= persistence_threshold)
            weakness_list.append(LearnerWeakness(
                tag=tag_name,
                frequency=freq,
                is_recurring=is_recurring,
                last_observed_session_id=last_sessions.get(tag_name)
            ))

        return weakness_list
