import random
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.choices import CEFRLevel, SkillFocus
from .models import Exercise

from .serializers import ExerciseSerializer
from ai_engine.learner.state import LearnerStateBuilder
from ai_engine.generation.exercise_generator import AdaptiveExerciseGenerator

class ExerciseListCreateView(generics.ListCreateAPIView):
    """List speaking exercises or filter by CEFR level, skill focus, or language."""
    queryset = Exercise.objects.select_related('language').prefetch_related('topic_tags').all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cefr = self.request.query_params.get('cefr_level')
        skill = self.request.query_params.get('skill_focus')
        lang = self.request.query_params.get('language')

        if cefr and cefr.upper() != 'ALL':
            qs = qs.filter(cefr_level__iexact=cefr.strip())
        if skill and skill.upper() != 'ALL':
            s = skill.strip().lower()
            if s == 'speaking':
                s = 'fluency'
            qs = qs.filter(skill_focus__iexact=s)
        if lang and lang.lower() != 'all':
            qs = qs.filter(language__code__iexact=lang.strip())
        return qs


class ExerciseDetailView(generics.RetrieveAPIView):
    """Retrieve details for a single exercise."""
    queryset = Exercise.objects.select_related('language').prefetch_related('topic_tags').all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

class NextExerciseView(APIView):
    """
    Adaptive Next Exercise Picker:
    1. Checks for unexecuted REMEDIATE decisions from previous conversation sessions.
    2. Reads compact LearnerState (proficiency, goals, recent performance).
    3. Inspects persistent and recurring weaknesses.
    4. Finds candidate exercises matching target language, level, and weaknesses.
    5. Excludes recently completed exercises and explicit exclude_id to avoid repetition.
    6. Falls back to adjacent CEFR levels when pool is exhausted.
    7. Dynamically generates a targeted exercise if no candidate exists in the bank.
    """
    permission_classes = [IsAuthenticated]

    CEFR_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

    def get(self, request):
        from apps.recordings.models import AgentDecisionLog

        user = request.user
        lang_code = request.query_params.get('language')
        exclude_id = request.query_params.get('exclude_id')

        if lang_code:
            target_user_lang = user.user_languages.filter(language__code=lang_code).select_related('language').first()
            if not target_user_lang:
                return Response(
                    {"detail": f"User is not enrolled in language '{lang_code}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_user_lang = user.primary_user_language

        learner_state = LearnerStateBuilder.build(user, lang_code)
        target_cefr = learner_state.current_cefr
        recent_exercise_ids = set(learner_state.recent_exercise_ids)

        # Add explicit exclude_id (the exercise currently shown to the user)
        if exclude_id:
            try:
                recent_exercise_ids.add(int(exclude_id))
            except (ValueError, TypeError):
                pass

        # Standard weakness tag to skill focus mapping
        weakness_map = {
            'grammar_error_rate_high': SkillFocus.GRAMMAR,
            'past_tense': SkillFocus.GRAMMAR,
            'prepositions': SkillFocus.GRAMMAR,
            'subject-verb_agreement': SkillFocus.GRAMMAR,
            'past_participle': SkillFocus.GRAMMAR,
            'irregular_verbs': SkillFocus.GRAMMAR,
            'capitalization': SkillFocus.GRAMMAR,
            'double_negatives': SkillFocus.GRAMMAR,
            'vocabulary_repetition': SkillFocus.VOCABULARY,
            'lexical_variety': SkillFocus.VOCABULARY,
            'filler_words_high': SkillFocus.FLUENCY,
            'pause_heavy': SkillFocus.FLUENCY,
            'low_wpm': SkillFocus.FLUENCY,
            'elaboration_&_fluency': SkillFocus.FLUENCY,
            'pronunciation_clarity_low': SkillFocus.PRONUNCIATION,
        }

        # Identify top weakness from LearnerState
        top_weakness_name = None
        target_skill = None
        if learner_state.weaknesses:
            top_weakness = learner_state.weaknesses[0]
            top_weakness_name = top_weakness.tag
            clean_tag = top_weakness.tag.lower().replace(" ", "_")
            target_skill = weakness_map.get(clean_tag, SkillFocus.GRAMMAR)

        # Check for unexecuted remediation directives from agent policy
        pending_remediation = AgentDecisionLog.objects.filter(
            user=user,
            action="REMEDIATE",
            was_executed=False
        ).order_by('-created_at').first()

        if pending_remediation:
            if pending_remediation.target_weakness:
                top_weakness_name = pending_remediation.target_weakness
            if pending_remediation.target_skill:
                clean_skill = pending_remediation.target_skill.lower()
                target_skill = SkillFocus.GRAMMAR if clean_skill == 'grammar' else (
                    SkillFocus.VOCABULARY if clean_skill == 'vocabulary' else (
                        SkillFocus.FLUENCY if clean_skill == 'fluency' else SkillFocus.GRAMMAR
                    )
                )
            if pending_remediation.difficulty:
                target_cefr = pending_remediation.difficulty

        selected = self._pick_exercise(target_user_lang, target_cefr, target_skill, recent_exercise_ids)

        # If exact CEFR pool is exhausted, try adjacent levels (one above, one below)
        if selected is None:
            try:
                idx = self.CEFR_ORDER.index(target_cefr)
            except ValueError:
                idx = 2  # default to B1 position
            adjacent_levels = []
            if idx + 1 < len(self.CEFR_ORDER):
                adjacent_levels.append(self.CEFR_ORDER[idx + 1])
            if idx - 1 >= 0:
                adjacent_levels.append(self.CEFR_ORDER[idx - 1])

            for adj_cefr in adjacent_levels:
                selected = self._pick_exercise(target_user_lang, adj_cefr, target_skill, recent_exercise_ids)
                if selected:
                    break

        # Last resort: any unseen exercise in language, or generate one
        if selected is None:
            if target_user_lang:
                fallback_qs = Exercise.objects.filter(
                    language=target_user_lang.language
                ).exclude(id__in=recent_exercise_ids)
                if fallback_qs.exists():
                    selected = random.choice(list(fallback_qs))
                else:
                    # Pick any exercise in language even if seen before
                    all_lang = Exercise.objects.filter(language=target_user_lang.language)
                    if all_lang.exists() and not pending_remediation:
                        selected = random.choice(list(all_lang))
                    else:
                        generator = AdaptiveExerciseGenerator()
                        selected = generator.generate_and_save(
                            language=target_user_lang.language,
                            cefr_level=target_cefr,
                            skill_focus=target_skill or "grammar",
                            target_weakness=top_weakness_name or ""
                        )
            else:
                return Response(
                    {"detail": "No exercises found in exercise bank."},
                    status=status.HTTP_404_NOT_FOUND
                )

        if pending_remediation:
            pending_remediation.was_executed = True
            pending_remediation.save(update_fields=['was_executed', 'updated_at'])

        serializer = ExerciseSerializer(selected)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _pick_exercise(self, user_lang, cefr, skill, exclude_ids):
        """Try to pick an unseen exercise at the given CEFR level. Returns Exercise or None."""
        candidates = Exercise.objects.filter(cefr_level=cefr)
        if user_lang:
            candidates = candidates.filter(language=user_lang.language)

        if skill:
            skill_matched = candidates.filter(skill_focus=skill).exclude(id__in=exclude_ids)
            if skill_matched.exists():
                return random.choice(list(skill_matched))

        unseen = candidates.exclude(id__in=exclude_ids)
        if unseen.exists():
            return random.choice(list(unseen))

        return None

