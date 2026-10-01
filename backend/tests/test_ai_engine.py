"""
Unit and integration tests for AI Engine components:
- Speech metrics calculation (WPM, pauses, fillers)
- Gemini transcriber and timestamp normalization
- Linguistic assessor and schema validation
- Weakness tracking and persistence detection
- Learner state builder
- Adaptive agent hybrid policy & remediation exercise generation
- Conversational response generator
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from core.choices import CEFRLevel, ExerciseSourceType, RecordingStatus, ConversationRole
from apps.authentication.models import User, Language, UserLanguage
from apps.exercises.models import Exercise
from apps.recordings.models import ConversationSession, ConversationTurn, Recording, AnalysisResult, WeaknessTag

from ai_engine.schemas.transcription import WordTimestamp, TranscriptResult
from ai_engine.schemas.assessment import LinguisticAssessment, GrammarFeedback, VocabularyFeedback
from ai_engine.schemas.agent import AgentActionType
from ai_engine.speech.metrics import SpeechMetricsCalculator
from ai_engine.transcription.gemini_transcriber import GeminiTranscriber
from ai_engine.assessment.assessor import LinguisticAssessor
from ai_engine.learner.weaknesses import WeaknessTracker
from ai_engine.learner.state import LearnerStateBuilder
from ai_engine.learner.promotion import SpeakingLevelAdjustmentService, SpeakingPromotionService
from ai_engine.agent.policy import HybridAgentPolicy
from ai_engine.agent.orchestrator import AdaptiveAgentOrchestrator
from ai_engine.generation.response_generator import ConversationalResponseGenerator
from ai_engine.generation.exercise_generator import AdaptiveExerciseGenerator
from apps.recordings.tasks import process_recording_task


@pytest.fixture
def english_lang(db):
    lang, _ = Language.objects.get_or_create(
        code='en-US',
        defaults={'name': 'English (US)', 'is_active': True}
    )
    return lang


@pytest.fixture
def learner_user(db, english_lang):
    user = User.objects.create_user(
        username='ai_learner',
        email='ai_learner@example.com',
        password='TestPassword123!'
    )
    UserLanguage.objects.create(
        user=user,
        language=english_lang,
        current_cefr_level=CEFRLevel.B1,
        target_goal='Fluent Speaking',
        is_primary=True,
        is_learning=True
    )
    return user


def test_speech_metrics_calculation():
    """Verify deterministic WPM, pause detection, and filler count in pure Python."""
    calculator = SpeechMetricsCalculator(pause_threshold_sec=0.45)

    words = [
        WordTimestamp(word="Well", start=0.0, end=0.4),
        WordTimestamp(word="I", start=0.5, end=0.7),
        WordTimestamp(word="um", start=0.8, end=1.0),
        WordTimestamp(word="think", start=1.6, end=2.0),   # 0.6s gap -> pause!
        WordTimestamp(word="that", start=2.1, end=2.3),
        WordTimestamp(word="is", start=2.4, end=2.6),
        WordTimestamp(word="great", start=3.3, end=3.8),   # 0.7s gap -> pause!
    ]
    transcript = TranscriptResult(
        transcript="Well I um think that is great",
        words=words
    )

    metrics = calculator.calculate(transcript, audio_duration_seconds=5.0)

    assert metrics["word_count"] == 7
    assert metrics["pause_count"] == 2
    assert metrics["filler_count"] >= 2  # 'well', 'um'
    assert metrics["wpm"] == int((7 / 5.0) * 60)
    assert metrics["avg_pause_ms"] > 500


def test_gemini_transcriber_normalization():
    """Verify timestamp sanitization ensures ascending chronological bounds."""
    transcriber = GeminiTranscriber()
    raw_words = [
        WordTimestamp(word="Hello", start=0.0, end=0.5),
        WordTimestamp(word="world", start=0.3, end=0.8),  # overlapping -> normalized!
    ]
    normalized = transcriber._normalize_timestamps(raw_words, audio_duration=5.0)

    assert len(normalized) == 2
    assert normalized[1].start >= normalized[0].end


@pytest.mark.django_db
def test_weakness_tracker_and_persistence(learner_user, english_lang):
    """Verify weakness sync, frequency accumulation, and persistence detection."""
    # 1. Create a session and recording
    user_lang = learner_user.primary_user_language
    session = ConversationSession.objects.create(user_language=user_lang, session_title="Practice")
    turn = ConversationTurn.objects.create(session=session, role=ConversationRole.USER, turn_sequence=1)
    rec = Recording.objects.create(turn=turn, duration_seconds=10.0, status=RecordingStatus.ANALYZED)

    analysis = AnalysisResult.objects.create(
        recording=rec,
        estimated_cefr=CEFRLevel.B1,
        grammar_feedback={},
        vocabulary_feedback={},
        fluency_metrics={}
    )

    # 2. Sync weaknesses
    tags = WeaknessTracker.sync_analysis_weaknesses(
        analysis_result=analysis,
        weakness_names=["Past Tense", "Prepositions"],
        language=english_lang
    )
    assert len(tags) == 2
    assert analysis.weakness_tags.count() == 2

    # 3. Retrieve learner weaknesses
    weaknesses = WeaknessTracker.get_learner_weaknesses(learner_user, english_lang)
    assert len(weaknesses) == 2
    tag_names = [w.tag for w in weaknesses]
    assert "Past Tense" in tag_names
    assert "Prepositions" in tag_names


@pytest.mark.django_db
def test_learner_state_builder(learner_user, english_lang):
    """Verify compact LearnerState is populated correctly from Django models."""
    state = LearnerStateBuilder.build(learner_user, english_lang.code)

    assert state.user_id == learner_user.id
    assert state.username == learner_user.username
    assert state.current_cefr == 'B1'
    assert state.target_language == english_lang.code
    assert isinstance(state.weaknesses, list)


@pytest.mark.django_db
def test_hybrid_agent_policy_remediation():
    """Verify policy triggers REMEDIATE when a recurring weakness is detected."""
    from ai_engine.schemas.learner import LearnerState, LearnerWeakness

    state = LearnerState(
        user_id=1,
        username="test",
        current_cefr="B1",
        weaknesses=[
            LearnerWeakness(tag="Past Tense", frequency=4, is_recurring=True)
        ],
        recurring_weakness_tags=["Past Tense"]
    )

    assessment = LinguisticAssessment(
        estimated_cefr="B1",
        grammar_feedback=GrammarFeedback(overall_score=75, strengths=[], corrections=[]),
        vocabulary_feedback=VocabularyFeedback(overall_score=80, advanced_words_used=[], suggestions=[]),
        weaknesses=["Past Tense"]
    )

    decision = HybridAgentPolicy.evaluate(
        learner_state=state,
        assessment=assessment,
        interaction_type="exercise"
    )

    assert decision.action == AgentActionType.REMEDIATE
    assert decision.target_weakness == "Past Tense"


@pytest.mark.django_db
def test_adaptive_exercise_generator(learner_user, english_lang):
    """Verify adaptive exercise generator creates and saves an exercise with source=GENERATED."""
    generator = AdaptiveExerciseGenerator()
    exercise = generator.generate_and_save(
        language=english_lang,
        cefr_level="B1",
        skill_focus="grammar",
        target_weakness="Past Tense"
    )

    assert exercise.id is not None
    assert exercise.source == ExerciseSourceType.GENERATED
    assert exercise.language == english_lang
    assert exercise.cefr_level == "B1"
    assert exercise.topic_tags.count() >= 1


@pytest.mark.django_db
def test_conversational_response_generator():
    """Verify dynamic coach reply generation fallback."""
    generator = ConversationalResponseGenerator()
    reply, is_concluding, telemetry = generator.generate_reply(
        scenario_id="coffee_shop",
        turn_number=1,
        user_transcript="I would like a large cappuccino with oat milk, please."
    )

    assert len(reply) > 0
    assert isinstance(is_concluding, bool)
    assert "llm_model_version" in telemetry


@pytest.mark.django_db
def test_end_to_end_process_recording_pipeline(learner_user, english_lang, monkeypatch):
    """Verify full Celery task execution with transcription, metrics, and assessment."""
    user_lang = learner_user.primary_user_language
    session = ConversationSession.objects.create(
        user_language=user_lang,
        session_title="Order at Coffee Shop"
    )
    turn = ConversationTurn.objects.create(
        session=session,
        role=ConversationRole.USER,
        turn_sequence=1,
        text_content=""
    )
    audio_file = SimpleUploadedFile("audio.webm", b"RIFFaudiobytes123", content_type="audio/webm")
    rec = Recording.objects.create(
        turn=turn,
        audio_file=audio_file,
        duration_seconds=18.0,
        mime_type="audio/webm",
        status=RecordingStatus.UPLOADED
    )

    # Mock transcriber to isolate Celery pipeline from live audio API call
    from ai_engine.schemas.transcription import TranscriptResult, WordTimestamp
    mock_transcript = TranscriptResult(
        transcript="Hello, I would like to order a warm cappuccino with almond milk please.",
        words=[
            WordTimestamp(word="Hello", start=0.2, end=0.6),
            WordTimestamp(word="cappuccino", start=1.2, end=1.9),
        ],
        detected_language="en-US"
    )
    monkeypatch.setattr(
        GeminiTranscriber,
        "transcribe",
        lambda self, *args, **kwargs: (mock_transcript, {"asr_model_version": "mock-whisper-v3"})
    )

    # Run the task directly (CELERY_TASK_ALWAYS_EAGER=True)
    process_recording_task.apply(args=[rec.id])

    rec.refresh_from_db()
    turn.refresh_from_db()

    assert rec.status == RecordingStatus.ANALYZED
    assert len(turn.text_content) > 0  # Transcribed speech populated!

    analysis = rec.analysis_results.filter(is_current=True).first()
    assert analysis is not None
    assert "wpm" in analysis.fluency_metrics
    assert "overall_score" in analysis.grammar_feedback
    assert "overall_score" in analysis.vocabulary_feedback
    assert len(analysis.word_timestamps) > 0
    assert analysis.weakness_tags.count() >= 0
    # Check that level adjustment telemetry was recorded in fluency_metrics
    assert "adjustment" in analysis.fluency_metrics
    assert "level_confidence" in analysis.fluency_metrics["adjustment"]


def _create_analysis_for_test(
    user_language,
    estimated_cefr="B1",
    wpm=100,
    avg_pause_ms=800,
    grammar_score=80,
    vocab_score=80,
    word_count=30
):
    """Helper to create realistic AnalysisResult linked to a user_language."""
    session = ConversationSession.objects.create(
        user_language=user_language,
        session_title="Practice Session"
    )
    transcript = " ".join(["fluent_word"] * word_count)
    turn = ConversationTurn.objects.create(
        session=session,
        role=ConversationRole.USER,
        turn_sequence=1,
        text_content=transcript
    )
    rec = Recording.objects.create(
        turn=turn,
        duration_seconds=15.0,
        mime_type="audio/webm",
        status=RecordingStatus.ANALYZED
    )
    return AnalysisResult.objects.create(
        recording=rec,
        is_current=True,
        estimated_cefr=estimated_cefr,
        fluency_metrics={
            "wpm": wpm,
            "avg_pause_ms": avg_pause_ms,
            "filler_count": 0
        },
        grammar_feedback={
            "overall_score": grammar_score,
            "strengths": ["Consistent agreement"],
            "corrections": []
        },
        vocabulary_feedback={
            "overall_score": vocab_score,
            "advanced_words_used": ["sophisticated"],
            "suggestions": []
        }
    )


@pytest.mark.django_db
def test_adjustment_sustained_promotion(learner_user):
    """Verify that consistent high performance across 4 of 5 sessions promotes the learner."""
    user_lang = learner_user.primary_user_language
    user_lang.current_cefr_level = "B1"
    user_lang.save()

    # Create 5 sessions meeting B1 -> B2 criteria (min WPM: 105, min grammar: 84, min vocab: 80, words: 28)
    analyses = [
        _create_analysis_for_test(
            user_language=user_lang,
            estimated_cefr="B2",
            wpm=112,
            avg_pause_ms=750,
            grammar_score=88,
            vocab_score=85,
            word_count=35
        )
        for _ in range(5)
    ]

    result = SpeakingLevelAdjustmentService.evaluate_and_apply_adjustment(
        user_language=user_lang,
        current_analysis=analyses[0],
        is_milestone=False
    )

    assert result["action"] == "PROMOTED"
    assert result["promoted"] is True
    assert result["demoted"] is False
    assert result["new_level"] == "B2"
    assert result["level_confidence"] >= 80

    user_lang.refresh_from_db()
    assert user_lang.current_cefr_level == "B2"


@pytest.mark.django_db
def test_adjustment_milestone_promotion(learner_user):
    """Verify that passing a cap-off milestone promotes immediately."""
    user_lang = learner_user.primary_user_language
    user_lang.current_cefr_level = "A1"
    user_lang.save()

    analysis = _create_analysis_for_test(
        user_language=user_lang,
        estimated_cefr="A2",
        wpm=75,
        avg_pause_ms=1000,
        grammar_score=80,
        vocab_score=75,
        word_count=12
    )

    result = SpeakingLevelAdjustmentService.evaluate_and_apply_adjustment(
        user_language=user_lang,
        current_analysis=analysis,
        is_milestone=True
    )

    assert result["action"] == "PROMOTED"
    assert result["promoted"] is True
    assert result["new_level"] == "A2"
    assert result["is_milestone"] is True

    user_lang.refresh_from_db()
    assert user_lang.current_cefr_level == "A2"


@pytest.mark.django_db
def test_adjustment_temporary_stumble_does_not_demote(learner_user):
    """Verify hysteresis: a single poor session does NOT demote the learner."""
    user_lang = learner_user.primary_user_language
    user_lang.current_cefr_level = "B1"
    user_lang.total_sessions_completed = 10
    user_lang.save()

    # 4 normal sessions + 1 terrible session
    for _ in range(4):
        _create_analysis_for_test(
            user_language=user_lang,
            estimated_cefr="B1",
            wpm=90,
            avg_pause_ms=850,
            grammar_score=80,
            vocab_score=78,
            word_count=25
        )

    bad_analysis = _create_analysis_for_test(
        user_language=user_lang,
        estimated_cefr="A2",
        wpm=45,
        avg_pause_ms=1600,
        grammar_score=50,
        vocab_score=45,
        word_count=6
    )

    result = SpeakingLevelAdjustmentService.evaluate_and_apply_adjustment(
        user_language=user_lang,
        current_analysis=bad_analysis,
        is_milestone=False
    )

    assert result["action"] == "MAINTAINED"
    assert result["promoted"] is False
    assert result["demoted"] is False
    assert result["current_level"] == "B1"

    user_lang.refresh_from_db()
    assert user_lang.current_cefr_level == "B1"


@pytest.mark.django_db
def test_adjustment_sustained_regression_demotes(learner_user):
    """Verify that sustained struggle across 5 of 6 sessions triggers conservative demotion with hysteresis."""
    user_lang = learner_user.primary_user_language
    user_lang.current_cefr_level = "B1"
    user_lang.total_sessions_completed = 12
    user_lang.save()

    # Create 6 sessions: 5 heavily struggling below B1 floor (wpm <= 60, grammar <= 65, vocab <= 60, estimated_cefr < B1)
    analyses = []
    for _ in range(5):
        analyses.append(_create_analysis_for_test(
            user_language=user_lang,
            estimated_cefr="A2",
            wpm=50,
            avg_pause_ms=1500,
            grammar_score=52,
            vocab_score=50,
            word_count=8
        ))

    # 1 okay session
    analyses.append(_create_analysis_for_test(
        user_language=user_lang,
        estimated_cefr="B1",
        wpm=90,
        avg_pause_ms=850,
        grammar_score=80,
        vocab_score=75,
        word_count=20
    ))

    result = SpeakingLevelAdjustmentService.evaluate_and_apply_adjustment(
        user_language=user_lang,
        current_analysis=analyses[0],
        is_milestone=False
    )

    assert result["action"] == "DEMOTED"
    assert result["demoted"] is True
    assert result["promoted"] is False
    assert result["previous_level"] == "B1"
    assert result["new_level"] == "A2"
    assert "Calibrating to A2" in result["reason"] or "A2 - Elementary" in result["reason"]

    user_lang.refresh_from_db()
    assert user_lang.current_cefr_level == "A2"


@pytest.mark.django_db
def test_adjustment_a1_floor_protection(learner_user):
    """Verify that a learner at A1 is never demoted, as A1 is the baseline CEFR floor."""
    user_lang = learner_user.primary_user_language
    user_lang.current_cefr_level = "A1"
    user_lang.total_sessions_completed = 15
    user_lang.save()

    analyses = [
        _create_analysis_for_test(
            user_language=user_lang,
            estimated_cefr="A1",
            wpm=30,
            avg_pause_ms=2200,
            grammar_score=40,
            vocab_score=35,
            word_count=4
        )
        for _ in range(6)
    ]

    result = SpeakingLevelAdjustmentService.evaluate_and_apply_adjustment(
        user_language=user_lang,
        current_analysis=analyses[0],
        is_milestone=False
    )

    assert result["action"] == "MAINTAINED"
    assert result["demoted"] is False
    assert result["current_level"] == "A1"

    user_lang.refresh_from_db()
    assert user_lang.current_cefr_level == "A1"


@pytest.mark.django_db
def test_adjustment_milestone_never_demotes(learner_user):
    """Verify milestone immunity: cap-off assessments cannot demote even on severe struggle."""
    user_lang = learner_user.primary_user_language
    user_lang.current_cefr_level = "B1"
    user_lang.total_sessions_completed = 15
    user_lang.save()

    analyses = [
        _create_analysis_for_test(
            user_language=user_lang,
            estimated_cefr="A2",
            wpm=40,
            avg_pause_ms=1800,
            grammar_score=45,
            vocab_score=40,
            word_count=5
        )
        for _ in range(6)
    ]

    result = SpeakingLevelAdjustmentService.evaluate_and_apply_adjustment(
        user_language=user_lang,
        current_analysis=analyses[0],
        is_milestone=True  # Milestone cap-off
    )

    assert result["demoted"] is False
    assert result["promoted"] is False
    assert result["action"] == "MAINTAINED"
    assert user_lang.current_cefr_level == "B1"
