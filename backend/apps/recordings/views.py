from datetime import timedelta
import logging
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import models
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from core.choices import CEFRLevel, ConversationRole, RecordingStatus
from apps.authentication.models import Language, UserLanguage
from .models import Recording, AnalysisResult, ConversationSession, ConversationTurn, AgentDecisionLog
from .serializers import (
    RecordingSerializer,
    RecordingUploadSerializer,
    ConversationSessionSerializer,
    ConversationSessionDetailSerializer,
    StartConversationSessionSerializer,
    ConversationTurnReplySerializer,
)
from .conversations import get_all_scenarios, get_scenario, generate_coach_follow_up, SCENARIOS
from .tasks import process_recording_task
from ai_engine.config import AIEngineConfig
from ai_engine.generation.response_generator import ConversationalResponseGenerator
from ai_engine.agent.orchestrator import AdaptiveAgentOrchestrator
from ai_engine.schemas.assessment import LinguisticAssessment, GrammarFeedback, VocabularyFeedback
from ai_engine.schemas.agent import AgentActionType, AgentDecision

logger = logging.getLogger(__name__)

class RecordingUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = RecordingUploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        recording = serializer.save()

        # Enqueue asynchronous Celery analysis job
        try:
            from typing import Any
            task: Any = process_recording_task
            task.delay(recording.id)
        except Exception:
            pass


        return Response(
            RecordingSerializer(recording).data,
            status=status.HTTP_201_CREATED
        )

class RecordingDetailView(generics.RetrieveAPIView):
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recording.objects.filter(
            turn__session__user_language__user=self.request.user
        ).select_related('turn__session__exercise')

class UserRecordingsListView(generics.ListAPIView):
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recording.objects.filter(
            turn__session__user_language__user=self.request.user
        ).select_related('turn__session__exercise').prefetch_related('analysis_results').order_by('-created_at')

class ProgressMetricsView(APIView):
    """
    Derives progress trends dynamically from active AnalysisResult records.
    Query params:
      window: 7d, 30d, 90d, all (default: 30d)
      language: language code (e.g. 'en-US', 'es-ES'), or 'all' (default: primary language)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        window = request.query_params.get('window', '30d')
        lang_code = request.query_params.get('language')

        qs = AnalysisResult.objects.filter(
            recording__turn__session__user_language__user=user,
            is_current=True
        ).select_related('recording__turn__session__exercise', 'recording__turn__session__user_language__language').prefetch_related('weakness_tags').order_by('created_at')

        # Language isolation
        if lang_code and lang_code.lower() != 'all':
            user_lang = user.user_languages.filter(language__code=lang_code).select_related('language').first()
            if not user_lang:
                return Response(
                    {"detail": f"User is not enrolled in language '{lang_code}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(recording__turn__session__user_language=user_lang)
            current_cefr = user_lang.current_cefr_level
            target_lang_code = user_lang.language.code
            target_lang_name = user_lang.language.name
        elif lang_code and lang_code.lower() == 'all':
            primary_lang = user.primary_user_language
            current_cefr = primary_lang.current_cefr_level if primary_lang else CEFRLevel.B1
            target_lang_code = 'all'
            target_lang_name = 'All Languages'
        else:
            primary_lang = user.primary_user_language
            if primary_lang:
                qs = qs.filter(recording__turn__session__user_language=primary_lang)
                current_cefr = primary_lang.current_cefr_level
                target_lang_code = primary_lang.language.code
                target_lang_name = primary_lang.language.name
            else:
                current_cefr = CEFRLevel.B1
                target_lang_code = 'all'
                target_lang_name = 'All Languages'

        now = timezone.now()
        if window == '7d':
            qs = qs.filter(created_at__gte=now - timedelta(days=7))
        elif window == '30d':
            qs = qs.filter(created_at__gte=now - timedelta(days=30))
        elif window == '90d':
            qs = qs.filter(created_at__gte=now - timedelta(days=90))

        sessions = []
        weakness_counts = {}
        total_wpm = 0
        wpm_count = 0

        for item in qs:
            metrics = item.fluency_metrics or {}
            wpm = metrics.get('wpm')
            if wpm is not None:
                total_wpm += wpm
                wpm_count += 1

            for tag in item.weakness_tags.all():
                weakness_counts[tag.name] = weakness_counts.get(tag.name, 0) + 1

            ex_title = "Free Form Practice"
            rec = item.recording
            if rec.turn and rec.turn.session and rec.turn.session.exercise:
                ex_title = rec.turn.session.exercise.title

            sessions.append({
                "id": item.id,
                "recording_id": item.recording_id,
                "date": item.created_at.strftime('%Y-%m-%d %H:%M'),
                "cefr_estimate": item.estimated_cefr,
                "wpm": wpm,
                "pause_count": metrics.get('pause_count'),
                "avg_pause_ms": metrics.get('avg_pause_ms'),
                "filler_count": metrics.get('filler_count'),
                "exercise_title": ex_title,
            })

        avg_wpm = round(total_wpm / wpm_count, 1) if wpm_count > 0 else 0

        return Response({
            "window": window,
            "language": target_lang_code,
            "language_name": target_lang_name,
            "total_sessions": len(sessions),
            "average_wpm": avg_wpm,
            "current_cefr": current_cefr,
            "weakness_frequency": weakness_counts,
            "time_series": sessions,
        }, status=status.HTTP_200_OK)


class ConversationScenariosListView(APIView):
    """
    Returns catalog of available roleplay dialogue scenarios.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_all_scenarios(), status=status.HTTP_200_OK)


class ConversationSessionListCreateView(APIView):
    """
    GET: List user's conversation sessions.
    POST: Start a new conversation session seeded with Coach Turn #1.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ConversationSession.objects.filter(
            user_language__user=request.user
        ).select_related('user_language__language', 'exercise').prefetch_related(
            'turns__recording__analysis_results__weakness_tags'
        ).order_by('-created_at')
        serializer = ConversationSessionDetailSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = StartConversationSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scenario_id = serializer.validated_data['scenario_id']
        custom_title = serializer.validated_data.get('custom_title', '')

        user = request.user
        user_language = user.primary_user_language
        if not user_language:
            english, _ = Language.objects.get_or_create(
                code='en-US',
                defaults={'name': 'English (US)', 'is_active': True}
            )
            user_language, _ = UserLanguage.objects.get_or_create(
                user=user,
                language=english,
                defaults={'is_primary': True, 'is_learning': True, 'current_cefr_level': CEFRLevel.B1}
            )

        scenario = get_scenario(scenario_id)
        title = custom_title.strip() if custom_title and custom_title.strip() else scenario['title']

        session = ConversationSession.objects.create(
            user_language=user_language,
            session_title=title,
            snapshot_prompt_text=scenario['opening_message']
        )

        # Seed Turn #1 with the Coach's opening greeting/question
        _, first_seq = ConversationSession.get_next_turn_sequence(session.id)
        ConversationTurn.objects.create(
            session=session,
            role=ConversationRole.AGENT,
            turn_sequence=first_seq,
            text_content=scenario['opening_message'],
            llm_model_version='fluentflow-dialogue-v1',
            latency_ms=120,
            input_tokens=95,
            output_tokens=55
        )

        session.refresh_from_db()
        detail_serializer = ConversationSessionDetailSerializer(session, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class ConversationSessionDetailView(generics.RetrieveAPIView):
    """
    Retrieve single conversation session with complete turn history, audio URLs, and analysis.
    """
    serializer_class = ConversationSessionDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ConversationSession.objects.filter(
            user_language__user=self.request.user
        ).select_related('user_language__language', 'exercise').prefetch_related(
            'turns__recording__analysis_results__weakness_tags'
        )


class ConversationTurnReplyView(APIView):
    """
    Learner submits voice response audio to the active conversation session.
    Creates user turn + recording, runs analysis pipeline, evaluates agent policy,
    and generates an adaptive, pedagogically-guided Coach agent reply.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        session = get_object_or_404(
            ConversationSession.objects.select_related('user_language__language'),
            id=pk,
            user_language__user=request.user
        )

        if not session.is_active:
            return Response(
                {"detail": "This conversation session has concluded."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ConversationTurnReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        audio_file = serializer.validated_data['audio_file']
        duration_seconds = serializer.validated_data.get('duration_seconds', 0.0)
        mime_type = serializer.validated_data.get('mime_type', 'audio/webm')

        # Create user turn atomically under sequence lock
        _, user_seq = ConversationSession.get_next_turn_sequence(session.id)
        user_turn = ConversationTurn.objects.create(
            session=session,
            role=ConversationRole.USER,
            turn_sequence=user_seq,
            text_content="Learner Voice Reply"
        )

        recording = Recording.objects.create(
            turn=user_turn,
            audio_file=audio_file,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            file_size_bytes=audio_file.size,
            status=Recording.Status.UPLOADED
        )

        # Run analysis pipeline
        try:
            process_recording_task.apply(args=[recording.id])
        except Exception as exc:
            logger.warning(f"Direct apply of process_recording_task had warning: {exc}")
            try:
                process_recording_task.delay(recording.id)
            except Exception:
                pass

        user_turn.refresh_from_db()
        recording.refresh_from_db()

        # Fail gracefully if real transcription could not be completed
        if recording.status == RecordingStatus.FAILED or not user_turn.text_content:
            err_msg = recording.error_message or "Speech could not be transcribed."
            logger.warning(f"Turn #{user_seq} failed transcription for session {session.id}: {err_msg}")
            # Clean up the un-transcribed recording and turn so context is not corrupted
            recording.delete()
            user_turn.delete()
            if session.turn_counter > 0:
                ConversationSession.objects.filter(id=session.id).update(turn_counter=models.F('turn_counter') - 1)

            return Response(
                {
                    "detail": "We couldn't transcribe your audio clearly. The AI service may be experiencing high demand. Please tap the microphone and try speaking again.",
                    "error_detail": err_msg
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Count completed user turns in this session
        user_turns_count = session.turns.filter(role=ConversationRole.USER).count()

        # Identify scenario
        scenario_id = 'job_interview'
        for sc_key, sc_data in SCENARIOS.items():
            if sc_data['title'].lower() in session.session_title.lower() or sc_key in session.session_title.lower():
                scenario_id = sc_key
                break

        # READ BACK the fresh AnalysisResult from DB
        analysis_result = AnalysisResult.objects.filter(
            recording=recording,
            is_current=True
        ).prefetch_related('weakness_tags').first()

        assessment = None
        if analysis_result:
            try:
                grammar_data = analysis_result.grammar_feedback or {}
                vocab_data = analysis_result.vocabulary_feedback or {}
                weakness_names = [tag.name for tag in analysis_result.weakness_tags.all()]

                grammar_fb = GrammarFeedback(**grammar_data) if grammar_data else GrammarFeedback(overall_score=80)
                vocab_fb = VocabularyFeedback(**vocab_data) if vocab_data else VocabularyFeedback(overall_score=80)

                assessment = LinguisticAssessment(
                    estimated_cefr=analysis_result.estimated_cefr or CEFRLevel.B1,
                    grammar_feedback=grammar_fb,
                    vocabulary_feedback=vocab_fb,
                    fluency_feedback=str(analysis_result.fluency_metrics.get('feedback', '')) if isinstance(analysis_result.fluency_metrics, dict) else '',
                    weaknesses=weakness_names,
                    strengths_summary=""
                )
            except Exception as e:
                logger.warning(f"Failed to reconstruct LinguisticAssessment from AnalysisResult: {e}")

        # RUN ADAPTIVE AGENT ORCHESTRATOR
        target_lang_code = (
            session.user_language.language.code if session.user_language and session.user_language.language else "en"
        )
        max_turns = 4
        orchestrator = AdaptiveAgentOrchestrator()
        decision = orchestrator.decide_next_step(
            user=request.user,
            assessment=assessment,
            language_code=target_lang_code,
            interaction_type="conversation",
            current_turn=user_turns_count,
            max_turns=max_turns
        )

        # Log decision for cross-session continuity & analytics
        try:
            action_val = decision.action.value if hasattr(decision.action, 'value') else str(decision.action)
            AgentDecisionLog.objects.create(
                session=session,
                turn=user_turn,
                user=request.user,
                action=action_val,
                target_skill=decision.target_skill or '',
                target_weakness=decision.target_weakness or '',
                difficulty=decision.difficulty or '',
                reason=decision.reason or '',
                was_executed=False
            )
        except Exception as e:
            logger.warning(f"Failed to log AgentDecision: {e}")

        # Generate Coach's reply dynamically via Gemini response generator
        history_turns = [
            {"role": t.role, "text": t.text_content}
            for t in session.turns.order_by('turn_sequence')
        ]
        response_generator = ConversationalResponseGenerator()
        is_final = user_turns_count >= 4 or decision.action == AgentActionType.GIVE_FEEDBACK
        try:
            coach_text, is_concluding, coach_telemetry = response_generator.generate_reply(
                scenario_id=scenario_id,
                turn_number=user_turns_count,
                user_transcript=user_turn.text_content,
                history_turns=history_turns,
                is_final_turn=is_final,
                agent_decision=decision,
                assessment=assessment,
                analysis_result=analysis_result
            )
        except Exception as e:
            logger.error(f"Coach reply generation failed for session {session.id}: {e}")
            return Response(
                {
                    "detail": "Your speech was transcribed and analyzed, but the AI Coach is temporarily experiencing high traffic and could not reply. Please try speaking again.",
                    "error_detail": str(e),
                    "analysis_result_id": analysis_result.id if analysis_result else None
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Save Coach turn atomically under sequence lock
        _, coach_seq = ConversationSession.get_next_turn_sequence(session.id)
        ConversationTurn.objects.create(
            session=session,
            role=ConversationRole.AGENT,
            turn_sequence=coach_seq,
            text_content=coach_text,
            llm_model_version=coach_telemetry.get('llm_model_version', AIEngineConfig.DIALOGUE_MODEL),
            latency_ms=coach_telemetry.get('latency_ms', 150),
            input_tokens=coach_telemetry.get('input_tokens', 100),
            output_tokens=coach_telemetry.get('output_tokens', 50)
        )

        should_conclude = is_concluding or user_turns_count >= 4 or decision.action == AgentActionType.GIVE_FEEDBACK
        if should_conclude:
            session.is_active = False
            focus_text = f" Focus: {decision.target_weakness}." if decision.target_weakness else ""
            session.conversation_summary = (
                f"Roleplay scenario completed with {user_turns_count} user turns.{focus_text}"
            )
            session.save(update_fields=['is_active', 'conversation_summary', 'updated_at'])

        session.refresh_from_db()
        detail_serializer = ConversationSessionDetailSerializer(session, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class ConcludeConversationSessionView(APIView):
    """
    Allows learner or coach to wrap up an active conversation session explicitly.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        session = get_object_or_404(
            ConversationSession,
            id=pk,
            user_language__user=request.user
        )
        session.is_active = False
        user_turns = session.turns.filter(role=ConversationRole.USER).count()
        session.conversation_summary = f"Conversation concluded by user after {user_turns} speaking turns."
        session.save(update_fields=['is_active', 'conversation_summary', 'updated_at'])

        detail_serializer = ConversationSessionDetailSerializer(session, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

