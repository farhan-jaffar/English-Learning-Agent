import logging
from celery import shared_task
from django.db import transaction
from django.db.models import F
from core.choices import CEFRLevel, RecordingStatus
from apps.authentication.models import UserLanguage
from .models import Recording, AnalysisResult, WeaknessTag

from ai_engine.config import AIEngineConfig
from ai_engine.transcription.gemini_transcriber import GeminiTranscriber
from ai_engine.speech.metrics import SpeechMetricsCalculator
from ai_engine.assessment.assessor import LinguisticAssessor
from ai_engine.learner.weaknesses import WeaknessTracker
from ai_engine.learner.promotion import SpeakingPromotionService, SpeakingLevelAdjustmentService

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    time_limit=300,
    name='recordings.process_recording'
)
def process_recording_task(self, recording_id):
    """
    Celery task orchestrating Gemini speech transcription, deterministic Python metrics,
    linguistic assessment, and persistent pedagogical weakness updates.
    """
    try:
        recording = Recording.objects.select_related(
            'turn__session__exercise__language',
            'turn__session__user_language__language',
            'turn__session__user_language__user'
        ).get(id=recording_id)
    except Recording.DoesNotExist:
        logger.error(f"Recording #{recording_id} does not exist.")
        return

    recording.status = RecordingStatus.PROCESSING
    recording.save(update_fields=['status', 'updated_at'])

    try:
        user_name = recording.user.username if recording.user else 'Anonymous'
        logger.info(f"Processing recording #{recording_id} for user {user_name}")

        session = recording.turn.session if recording.turn else None
        exercise = session.exercise if session else None
        user_language = session.user_language if session else None
        target_language = (
            (exercise and exercise.language) or
            (user_language and user_language.language)
        )

        # Derive baseline CEFR level
        cefr = (
            (exercise and exercise.cefr_level) or
            (user_language and user_language.current_cefr_level) or
            CEFRLevel.B1
        )
        duration = float(recording.duration_seconds or 15.0)

        # 1. Read audio file bytes
        audio_bytes = b""
        try:
            if recording.audio_file:
                recording.audio_file.open('rb')
                audio_bytes = recording.audio_file.read()
                recording.audio_file.close()
        except Exception as e:
            logger.warning(f"Could not read audio file directly for #{recording_id}: {e}")

        if not audio_bytes or len(audio_bytes) < 10:
            recording.status = RecordingStatus.FAILED
            recording.error_message = "Audio file is empty or could not be read."
            recording.save(update_fields=['status', 'error_message', 'updated_at'])
            logger.error(f"Recording #{recording_id} has empty audio file ({len(audio_bytes)} bytes).")
            return

        # 2. Gemini Multimodal Transcription & Word Timestamps
        transcriber = GeminiTranscriber()
        vocab_hints = getattr(exercise, 'vocabulary_hints', []) if exercise else []
        transcript_result, asr_telemetry = transcriber.transcribe(
            audio_bytes=audio_bytes,
            mime_type=recording.mime_type or "audio/webm",
            vocabulary_hints=vocab_hints,
            duration_seconds=duration
        )

        # 3. Deterministic Speech Metrics (WPM, Pauses, Fillers)
        metrics_calculator = SpeechMetricsCalculator()
        fluency_metrics = metrics_calculator.calculate(
            transcript_result=transcript_result,
            audio_duration_seconds=duration
        )

        # 4. Linguistic Assessment (Grammar, Vocabulary, CEFR, Weakness Extraction)
        assessor = LinguisticAssessor()
        prompt_context = (
            exercise.prompt_text if exercise else (session.snapshot_prompt_text if session else "")
        )
        recent_weakness_tags = []
        if recording.user and target_language:
            recent_weakness_tags = [
                w.tag for w in WeaknessTracker.get_learner_weaknesses(user=recording.user, language=target_language)
            ]

        assessment, llm_telemetry = assessor.assess(
            transcript=transcript_result.transcript,
            prompt_text=prompt_context,
            current_cefr=cefr,
            speech_metrics=fluency_metrics,
            recent_weaknesses=recent_weakness_tags
        )

        # Format word timestamps for database JSONField
        word_timestamps = [
            {"word": w.word, "start_offset": w.start, "end_offset": w.end}
            for w in transcript_result.words
        ]

        with transaction.atomic():
            # Mark any existing current analysis for this recording as not current
            AnalysisResult.objects.filter(recording=recording, is_current=True).update(is_current=False)

            analysis = AnalysisResult.objects.create(
                recording=recording,
                is_current=True,
                estimated_cefr=assessment.estimated_cefr or cefr,
                grammar_feedback=assessment.grammar_feedback.model_dump(),
                vocabulary_feedback=assessment.vocabulary_feedback.model_dump(),
                fluency_metrics=fluency_metrics,
                word_timestamps=word_timestamps,
                asr_model_version=asr_telemetry.get("asr_model_version", AIEngineConfig.TRANSCRIPTION_MODEL),
                llm_model_version=llm_telemetry.get("llm_model_version", AIEngineConfig.EVALUATION_MODEL),
                prompt_version=llm_telemetry.get("prompt_version", "v2.0-adaptive-eval"),
                latency_asr_ms=asr_telemetry.get("latency_asr_ms", 0),
                latency_llm_ms=llm_telemetry.get("latency_llm_ms", 0),
                input_tokens=(asr_telemetry.get("input_tokens", 0) + llm_telemetry.get("input_tokens", 0)),
                output_tokens=(asr_telemetry.get("output_tokens", 0) + llm_telemetry.get("output_tokens", 0)),
                raw_llm_response=llm_telemetry.get("raw_llm_response", {"status": "success"})
            )

            # Associate weakness tags dynamically from assessment
            if target_language and assessment.weaknesses:
                WeaknessTracker.sync_analysis_weaknesses(
                    analysis_result=analysis,
                    weakness_names=assessment.weaknesses,
                    language=target_language
                )

            # Update turn transcript with verbatim speech
            if recording.turn:
                recording.turn.text_content = transcript_result.transcript
                recording.turn.save(update_fields=['text_content', 'updated_at'])

            # Mark recording as ANALYZED
            recording.status = RecordingStatus.ANALYZED
            recording.error_message = ''
            recording.save(update_fields=['status', 'error_message', 'updated_at'])

            # Increment UserLanguage stats atomically
            if user_language:
                UserLanguage.objects.filter(pk=user_language.pk).update(
                    total_sessions_completed=F('total_sessions_completed') + 1,
                    total_practice_seconds=F('total_practice_seconds') + int(duration)
                )

                # Evaluate Speaking CEFR Adjustment (bidirectional: promotion, demotion with hysteresis, or maintain)
                try:
                    is_milestone = False
                    if exercise and exercise.title:
                        is_milestone = any(
                            k in exercise.title.lower()
                            for k in ('milestone', 'cap-off', 'assessment')
                        )
                    user_language.refresh_from_db()
                    adjustment_info = SpeakingLevelAdjustmentService.evaluate_and_apply_adjustment(
                        user_language=user_language,
                        current_analysis=analysis,
                        is_milestone=is_milestone
                    )
                    if adjustment_info:
                        if not isinstance(analysis.fluency_metrics, dict):
                            analysis.fluency_metrics = {}
                        analysis.fluency_metrics['adjustment'] = adjustment_info
                        # Maintain 'promotion' key for backward compatibility with existing UI
                        analysis.fluency_metrics['promotion'] = adjustment_info
                        analysis.save(update_fields=['fluency_metrics', 'updated_at'])
                except Exception as adj_err:
                    logger.warning(f"Speaking level adjustment warning for recording #{recording_id}: {adj_err}")

        logger.info(f"Successfully analyzed recording #{recording_id}, generated AnalysisResult #{analysis.id}")

    except Exception as exc:
        logger.exception(f"Pipeline error for recording #{recording_id}: {exc}")
        recording.status = RecordingStatus.FAILED
        recording.error_message = f"Speech analysis failed: {str(exc)}"
        recording.save(update_fields=['status', 'error_message', 'updated_at'])
        if recording.turn and recording.turn.text_content == "Learner Voice Reply":
            recording.turn.text_content = ""
            recording.turn.save(update_fields=['text_content', 'updated_at'])
        raise exc
