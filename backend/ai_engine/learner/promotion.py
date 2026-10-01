"""
Speaking CEFR Level Adjustment Service (Bidirectional).
Evaluates active spoken language proficiency based on pronunciation intelligibility,
conversational flow/tempo (WPM, pause placement), and multi-clause sentence complexity.

Supports:
1. Automated Promotion: Sustained performance over rolling window (4/5 sessions) or cap-off speaking milestones.
2. Automated Demotion (Recalibration): Conservative hysteresis protection (5/6 sessions falling substantially below floor)
   to ensure learners are practicing at an accurate proficiency tier without penalizing temporary bad days.
3. Level Confidence: Real-time confidence telemetry reflecting rolling stability within the current CEFR tier.
"""

import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone
from apps.authentication.models import UserLanguage
from apps.recordings.models import AnalysisResult

logger = logging.getLogger(__name__)


class SpeakingLevelAdjustmentService:
    """
    Automated bidirectional evaluation service that promotes or recalibrates (demotes)
    a learner's CEFR level based on sustained evidence across a rolling session history.
    """

    CEFR_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

    # Promotion Targets (Next Level Criteria)
    PROMOTION_TARGETS = {
        'A1': {
            'next_level': 'A2',
            'target_name': 'A2 - Elementary',
            'min_wpm': 65,
            'max_avg_pause_ms': 1250,
            'min_words_per_turn': 8,
            'min_grammar_score': 75,
            'min_vocab_score': 70,
            'description': 'Accurately pronounce words and short phrases with minimal hesitation.',
        },
        'A2': {
            'next_level': 'B1',
            'target_name': 'B1 - Intermediate',
            'min_wpm': 85,
            'max_avg_pause_ms': 950,
            'min_words_per_turn': 18,
            'min_grammar_score': 80,
            'min_vocab_score': 75,
            'description': 'Connect simple sentences together to describe experiences and routines without long halting pauses.',
        },
        'B1': {
            'next_level': 'B2',
            'target_name': 'B2 - Upper Intermediate',
            'min_wpm': 105,
            'max_avg_pause_ms': 850,
            'min_words_per_turn': 28,
            'min_grammar_score': 84,
            'min_vocab_score': 80,
            'max_filler_ratio': 0.08,
            'description': 'Speak spontaneously on familiar topics with clear grammatical control and multi-clause complexity.',
        },
        'B2': {
            'next_level': 'C1',
            'target_name': 'C1 - Advanced',
            'min_wpm': 120,
            'max_avg_pause_ms': 750,
            'min_words_per_turn': 42,
            'min_grammar_score': 88,
            'min_vocab_score': 85,
            'max_filler_ratio': 0.06,
            'description': 'Fluent, spontaneous discourse with complex syntactic structures and natural rhythm.',
        },
        'C1': {
            'next_level': 'C2',
            'target_name': 'C2 - Mastery',
            'min_wpm': 135,
            'max_avg_pause_ms': 700,
            'min_words_per_turn': 55,
            'min_grammar_score': 92,
            'min_vocab_score': 90,
            'description': 'Effortless articulation, precision, and native-like conversational cadence.',
        },
    }

    # Demotion Floors (Performance falling substantially below current tier)
    # A1 has no lower tier.
    DEMOTION_FLOORS = {
        'A2': {
            'prev_level': 'A1',
            'target_name': 'A1 - Beginner',
            'floor_wpm': 45,
            'max_avg_pause_ms': 1800,
            'max_grammar_score': 55,
            'max_vocab_score': 50,
            'max_words_per_turn': 6,
            'description': 'Struggling with elementary phrases and vocabulary; recalibrating to A1 foundations.',
        },
        'B1': {
            'prev_level': 'A2',
            'target_name': 'A2 - Elementary',
            'floor_wpm': 60,
            'max_avg_pause_ms': 1400,
            'max_grammar_score': 65,
            'max_vocab_score': 60,
            'max_words_per_turn': 12,
            'description': 'Difficulty connecting simple sentences and maintaining conversational flow; recalibrating to A2 practice.',
        },
        'B2': {
            'prev_level': 'B1',
            'target_name': 'B1 - Intermediate',
            'floor_wpm': 80,
            'max_avg_pause_ms': 1150,
            'max_grammar_score': 70,
            'max_vocab_score': 68,
            'max_words_per_turn': 18,
            'description': 'Struggling with spontaneous discourse and grammatical control; recalibrating to B1 intermediate practice.',
        },
        'C1': {
            'prev_level': 'B2',
            'target_name': 'B2 - Upper Intermediate',
            'floor_wpm': 95,
            'max_avg_pause_ms': 950,
            'max_grammar_score': 76,
            'max_vocab_score': 72,
            'max_words_per_turn': 26,
            'description': 'Difficulty maintaining fluent, complex syntactic structures; recalibrating to B2 focus.',
        },
        'C2': {
            'prev_level': 'C1',
            'target_name': 'C1 - Advanced',
            'floor_wpm': 110,
            'max_avg_pause_ms': 850,
            'max_grammar_score': 82,
            'max_vocab_score': 80,
            'max_words_per_turn': 36,
            'description': 'Precision and native-like conversational cadence slipping; recalibrating to C1 focus.',
        },
    }

    # Configuration constants
    PROMOTION_WINDOW = 5
    PROMOTION_REQUIRED = 4
    DEMOTION_WINDOW = 6
    DEMOTION_REQUIRED = 5
    MIN_SESSIONS_FOR_DEMOTION = 6

    @classmethod
    def evaluate_and_apply_adjustment(
        cls,
        user_language: UserLanguage,
        current_analysis: AnalysisResult,
        is_milestone: bool = False,
        promotion_window: int = PROMOTION_WINDOW,
        demotion_window: int = DEMOTION_WINDOW
    ) -> Dict[str, Any]:
        """
        Evaluates recent speech analysis results and applies bidirectional level adjustment
        (promotion or demotion) with hysteresis guardrails.
        """
        current_level = (user_language.current_cefr_level or 'B1').upper()
        if current_level not in cls.CEFR_ORDER:
            current_level = 'B1'

        # Fetch recent analyses covering the maximum window size
        max_window = max(promotion_window, demotion_window)
        recent_analyses = list(
            AnalysisResult.objects.filter(
                recording__turn__session__user_language=user_language,
                is_current=True
            ).select_related('recording__turn').order_by('-created_at')[:max_window]
        )

        # Ensure current_analysis is included in recent batch
        if current_analysis and current_analysis.id not in [a.id for a in recent_analyses]:
            recent_analyses.insert(0, current_analysis)
            recent_analyses = recent_analyses[:max_window]

        # -------------------------------------------------------------
        # 1. EVALUATE PROMOTION
        # -------------------------------------------------------------
        promo_target = cls.PROMOTION_TARGETS.get(current_level)
        promo_analyses = recent_analyses[:promotion_window]
        promo_evals = [cls._evaluate_single_for_promotion(an, promo_target) for an in promo_analyses] if promo_target else []

        # 1a. Milestone / Cap-off Trigger (Milestones only promote, never demote)
        if is_milestone and promo_target and promo_evals:
            curr_eval = promo_evals[0]
            if curr_eval['qualifies']:
                return cls._promote_user(
                    user_language=user_language,
                    current_level=current_level,
                    target=promo_target,
                    reason=f"Passed dedicated Cap-off Speaking Milestone with {curr_eval['wpm']} WPM and {curr_eval['grammar_score']}% accuracy.",
                    metrics_summary=curr_eval,
                    is_milestone=True,
                    level_confidence=85
                )

        # 1b. Sustained Promotion Over Time
        total_promo_sessions = len(promo_evals)
        promo_qualifying_count = sum(1 for e in promo_evals if e['qualifies'])

        is_sustained_promo = False
        if total_promo_sessions >= promotion_window and promo_qualifying_count >= cls.PROMOTION_REQUIRED:
            is_sustained_promo = True
        elif total_promo_sessions in (3, 4) and promo_qualifying_count == total_promo_sessions:
            is_sustained_promo = True

        if is_sustained_promo and promo_target:
            avg_wpm = round(sum(e['wpm'] for e in promo_evals) / total_promo_sessions, 1)
            avg_grammar = round(sum(e['grammar_score'] for e in promo_evals) / total_promo_sessions, 1)
            avg_words = round(sum(e['words_count'] for e in promo_evals) / total_promo_sessions, 1)

            reason = (
                f"Sustained speaking performance proven across {promo_qualifying_count}/{total_promo_sessions} recent sessions! "
                f"Averaged {avg_wpm} WPM speech rate, {avg_grammar}% grammatical control, and {avg_words} words per utterance."
            )
            return cls._promote_user(
                user_language=user_language,
                current_level=current_level,
                target=promo_target,
                reason=reason,
                metrics_summary={
                    "average_wpm": avg_wpm,
                    "average_grammar": avg_grammar,
                    "average_words": avg_words,
                    "qualifying_sessions": promo_qualifying_count,
                    "window_size": total_promo_sessions,
                },
                is_milestone=False,
                level_confidence=85
            )

        # -------------------------------------------------------------
        # 2. EVALUATE DEMOTION (Sustained Regression with Hysteresis)
        # -------------------------------------------------------------
        demote_floor = cls.DEMOTION_FLOORS.get(current_level)
        total_sessions_completed = user_language.total_sessions_completed

        # Safeguards:
        # - Cannot demote if already at A1 (floor tier)
        # - Cannot demote on milestone sessions (milestones are cap-off assessments, not traps)
        # - Cannot demote if user has fewer completed sessions than MIN_SESSIONS_FOR_DEMOTION
        can_evaluate_demotion = (
            demote_floor is not None
            and not is_milestone
            and total_sessions_completed >= cls.MIN_SESSIONS_FOR_DEMOTION
        )

        struggling_evals = []
        if can_evaluate_demotion:
            demote_analyses = recent_analyses[:demotion_window]
            struggling_evals = [
                cls._evaluate_single_for_demotion(an, current_level, demote_floor)
                for an in demote_analyses
            ]
            total_demote_window = len(struggling_evals)
            struggling_count = sum(1 for e in struggling_evals if e['is_struggling'])

            if total_demote_window >= demotion_window and struggling_count >= cls.DEMOTION_REQUIRED:
                avg_wpm = round(sum(e['wpm'] for e in struggling_evals) / total_demote_window, 1)
                avg_grammar = round(sum(e['grammar_score'] for e in struggling_evals) / total_demote_window, 1)
                avg_vocab = round(sum(e['vocab_score'] for e in struggling_evals) / total_demote_window, 1)

                reason = (
                    f"Consistently struggled across {struggling_count}/{total_demote_window} recent sessions at {current_level}. "
                    f"Averaged {avg_wpm} WPM, {avg_grammar}% grammar, and {avg_vocab}% vocabulary. "
                    f"Calibrating to {demote_floor['target_name']} to reinforce foundational fluency."
                )
                return cls._demote_user(
                    user_language=user_language,
                    current_level=current_level,
                    floor=demote_floor,
                    reason=reason,
                    metrics_summary={
                        "average_wpm": avg_wpm,
                        "average_grammar": avg_grammar,
                        "average_vocab": avg_vocab,
                        "struggling_sessions": struggling_count,
                        "window_size": total_demote_window,
                    },
                    level_confidence=75
                )

        # -------------------------------------------------------------
        # 3. NO LEVEL CHANGE: Calculate Confidence & Return Telemetry
        # -------------------------------------------------------------
        level_confidence = cls._calculate_level_confidence(
            current_level=current_level,
            analyses=recent_analyses[:max_window],
            promo_qualifying_count=promo_qualifying_count,
            promo_window=total_promo_sessions,
            struggling_count=sum(1 for e in struggling_evals if e['is_struggling']) if struggling_evals else 0,
            demote_window=len(struggling_evals)
        )

        return {
            "action": "MAINTAINED",
            "promoted": False,
            "demoted": False,
            "current_level": current_level,
            "next_level": promo_target['next_level'] if promo_target else None,
            "target_name": promo_target['target_name'] if promo_target else None,
            "level_confidence": level_confidence,
            "qualifying_sessions": promo_qualifying_count,
            "sessions_evaluated": total_promo_sessions,
            "required_qualifying": cls.PROMOTION_REQUIRED if total_promo_sessions >= promotion_window else 3,
            "target_description": promo_target['description'] if promo_target else "Mastery tier reached.",
            "demotion_floor": demote_floor['prev_level'] if demote_floor else None,
            "struggling_sessions": sum(1 for e in struggling_evals if e['is_struggling']) if struggling_evals else 0,
            "target_metrics": {
                "min_wpm": promo_target['min_wpm'],
                "max_avg_pause_ms": promo_target['max_avg_pause_ms'],
                "min_words_per_turn": promo_target['min_words_per_turn'],
                "min_grammar_score": promo_target['min_grammar_score'],
                "min_vocab_score": promo_target['min_vocab_score']
            } if promo_target else {}
        }

    # Alias for backwards compatibility
    evaluate_and_apply_promotion = evaluate_and_apply_adjustment

    @classmethod
    def _evaluate_single_for_promotion(cls, analysis: AnalysisResult, target: Dict[str, Any]) -> Dict[str, Any]:
        """Checks if a single analysis meets the target criteria for the next CEFR level."""
        fluency = analysis.fluency_metrics or {}
        grammar = analysis.grammar_feedback or {}
        vocab = analysis.vocabulary_feedback or {}

        wpm = float(fluency.get('wpm') or 0.0)
        avg_pause_ms = float(fluency.get('avg_pause_ms') or 0.0)
        filler_count = int(fluency.get('filler_count') or 0)

        transcript = ""
        if analysis.recording and analysis.recording.turn:
            transcript = analysis.recording.turn.text_content or ""
        words = [w for w in transcript.split() if w.strip()]
        word_count = len(words)
        if not word_count and analysis.word_timestamps:
            word_count = len(analysis.word_timestamps)

        filler_ratio = (filler_count / max(word_count, 1))
        grammar_score = int(grammar.get('overall_score') or 0)
        vocab_score = int(vocab.get('overall_score') or 0)

        wpm_ok = wpm >= target['min_wpm']
        pause_ok = (avg_pause_ms <= target['max_avg_pause_ms']) if avg_pause_ms > 0 else True
        words_ok = word_count >= target['min_words_per_turn']
        grammar_ok = grammar_score >= target['min_grammar_score']
        vocab_ok = vocab_score >= target['min_vocab_score']

        filler_ok = True
        if 'max_filler_ratio' in target:
            filler_ok = filler_ratio <= target['max_filler_ratio']

        qualifies = (wpm_ok and pause_ok and words_ok and grammar_ok and vocab_ok and filler_ok)

        return {
            "analysis_id": analysis.id,
            "qualifies": qualifies,
            "wpm": wpm,
            "avg_pause_ms": avg_pause_ms,
            "words_count": word_count,
            "grammar_score": grammar_score,
            "vocab_score": vocab_score,
            "filler_ratio": round(filler_ratio, 3),
        }

    @classmethod
    def _evaluate_single_for_demotion(
        cls,
        analysis: AnalysisResult,
        current_level: str,
        floor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Checks if a single analysis represents a substantially substandard performance
        relative to the expectations of current_level.
        """
        fluency = analysis.fluency_metrics or {}
        grammar = analysis.grammar_feedback or {}
        vocab = analysis.vocabulary_feedback or {}

        wpm = float(fluency.get('wpm') or 0.0)
        avg_pause_ms = float(fluency.get('avg_pause_ms') or 0.0)

        transcript = ""
        if analysis.recording and analysis.recording.turn:
            transcript = analysis.recording.turn.text_content or ""
        words = [w for w in transcript.split() if w.strip()]
        word_count = len(words)
        if not word_count and analysis.word_timestamps:
            word_count = len(analysis.word_timestamps)

        grammar_score = int(grammar.get('overall_score') or 0)
        vocab_score = int(vocab.get('overall_score') or 0)

        # 1. Estimated CEFR strictly below current tier
        est_cefr = (analysis.estimated_cefr or '').upper()
        cefr_below = False
        try:
            current_idx = cls.CEFR_ORDER.index(current_level)
            est_idx = cls.CEFR_ORDER.index(est_cefr)
            cefr_below = est_idx < current_idx
        except ValueError:
            cefr_below = False

        # 2. Performance falling below floor limits
        grammar_struggle = grammar_score <= floor['max_grammar_score']
        vocab_struggle = vocab_score <= floor['max_vocab_score']
        fluency_struggle = (wpm <= floor['floor_wpm']) or (avg_pause_ms >= floor['max_avg_pause_ms'] and avg_pause_ms > 0)
        words_struggle = word_count <= floor['max_words_per_turn']

        # Multi-factor requirement: must have estimated_cefr below current level,
        # plus linguistic struggles (grammar or vocab) AND delivery struggles (fluency or words)
        is_struggling = (
            cefr_below
            and (grammar_struggle or vocab_struggle)
            and (fluency_struggle or words_struggle)
        )

        return {
            "analysis_id": analysis.id,
            "is_struggling": is_struggling,
            "wpm": wpm,
            "avg_pause_ms": avg_pause_ms,
            "words_count": word_count,
            "grammar_score": grammar_score,
            "vocab_score": vocab_score,
            "estimated_cefr": est_cefr,
            "cefr_below": cefr_below
        }

    @classmethod
    def _calculate_level_confidence(
        cls,
        current_level: str,
        analyses: List[AnalysisResult],
        promo_qualifying_count: int,
        promo_window: int,
        struggling_count: int,
        demote_window: int
    ) -> int:
        """
        Computes dynamic level confidence (0-100%) indicating how comfortably
        the learner resides at their current CEFR tier.
        """
        if not analyses:
            return 80  # Default initial baseline confidence

        base_confidence = 75

        # Promotion momentum boost: up to +20%
        if promo_window > 0:
            promo_ratio = promo_qualifying_count / promo_window
            base_confidence += int(promo_ratio * 20)

        # Regression penalty: up to -35%
        if demote_window > 0:
            struggle_ratio = struggling_count / demote_window
            base_confidence -= int(struggle_ratio * 35)

        return max(15, min(98, base_confidence))

    @classmethod
    def _promote_user(
        cls,
        user_language: UserLanguage,
        current_level: str,
        target: Dict[str, Any],
        reason: str,
        metrics_summary: Dict[str, Any],
        is_milestone: bool,
        level_confidence: int = 85
    ) -> Dict[str, Any]:
        """Atomically promotes the user to the next CEFR level and returns event payload."""
        new_level = target['next_level']
        user_language.current_cefr_level = new_level
        user_language.save(update_fields=['current_cefr_level', 'updated_at'])

        logger.info(
            f"🎉 [SpeakingLevelAdjustment] User '{user_language.user.username}' PROMOTED: "
            f"{current_level} -> {new_level} in {user_language.language.code}. Reason: {reason}"
        )

        return {
            "action": "PROMOTED",
            "promoted": True,
            "demoted": False,
            "previous_level": current_level,
            "current_level": new_level,
            "new_level": new_level,
            "new_level_name": target['target_name'],
            "level_confidence": level_confidence,
            "reason": reason,
            "target_description": target['description'],
            "metrics_summary": metrics_summary,
            "is_milestone": is_milestone,
            "promoted_at": timezone.now().isoformat()
        }

    @classmethod
    def _demote_user(
        cls,
        user_language: UserLanguage,
        current_level: str,
        floor: Dict[str, Any],
        reason: str,
        metrics_summary: Dict[str, Any],
        level_confidence: int = 75
    ) -> Dict[str, Any]:
        """Atomically recalibrates (demotes) the user to the lower CEFR level and returns event payload."""
        new_level = floor['prev_level']
        user_language.current_cefr_level = new_level
        user_language.save(update_fields=['current_cefr_level', 'updated_at'])

        logger.info(
            f"📉 [SpeakingLevelAdjustment] User '{user_language.user.username}' CALIBRATED (demoted): "
            f"{current_level} -> {new_level} in {user_language.language.code}. Reason: {reason}"
        )

        return {
            "action": "DEMOTED",
            "promoted": False,
            "demoted": True,
            "previous_level": current_level,
            "current_level": new_level,
            "new_level": new_level,
            "new_level_name": floor['target_name'],
            "level_confidence": level_confidence,
            "reason": reason,
            "target_description": floor['description'],
            "metrics_summary": metrics_summary,
            "is_milestone": False,
            "demoted_at": timezone.now().isoformat()
        }


# Backwards compatibility alias
SpeakingPromotionService = SpeakingLevelAdjustmentService
