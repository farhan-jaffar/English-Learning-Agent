import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from core.choices import CEFRLevel
from apps.authentication.models import User, Language, UserLanguage
from apps.exercises.models import Exercise, TopicTag
from apps.recordings.models import Recording, AnalysisResult, WeaknessTag, ConversationSession, ConversationTurn

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def english_lang(db):
    lang, _ = Language.objects.get_or_create(
        code='en-US',
        defaults={'name': 'English (US)', 'is_active': True}
    )
    return lang

@pytest.fixture
def user(db, english_lang):
    u = User.objects.create_user(
        username='learner_test',
        email='learner_test@example.com',
        password='StrongPassword123!',
    )
    UserLanguage.objects.create(
        user=u,
        language=english_lang,
        current_cefr_level=CEFRLevel.B1,
        is_primary=True,
        is_learning=True
    )
    return u

@pytest.fixture
def exercise(db, english_lang):
    ex = Exercise.objects.create(
        language=english_lang,
        title="Test Fluency Prompt",
        prompt_text="Describe your favorite book in 60 seconds.",
        skill_focus=Exercise.SkillFocus.FLUENCY,
        cefr_level=CEFRLevel.B1,
        vocabulary_hints=["author", "character", "plot", "theme"],
    )
    t1, _ = TopicTag.objects.get_or_create(name="literature")
    t2, _ = TopicTag.objects.get_or_create(name="books")
    ex.topic_tags.set([t1, t2])
    return ex

@pytest.mark.django_db
def test_exercise_list_and_filter(api_client, user, exercise):
    api_client.force_authenticate(user=user)
    url = reverse('exercise-list-create')

    # Get list
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 1

    # Filter by cefr_level
    res_filtered = api_client.get(f"{url}?cefr_level=B1")
    assert res_filtered.status_code == 200
    assert all(item['cefr_level'] == 'B1' for item in res_filtered.data)

    # Filter by skill_focus (lowercase, uppercase, speaking alias, and ALL)
    res_skill = api_client.get(f"{url}?skill_focus=fluency")
    assert res_skill.status_code == 200
    assert all(item['skill_focus'] == 'fluency' for item in res_skill.data)

    res_skill_upper = api_client.get(f"{url}?skill_focus=FLUENCY")
    assert res_skill_upper.status_code == 200
    assert all(item['skill_focus'] == 'fluency' for item in res_skill_upper.data)

    res_skill_speaking = api_client.get(f"{url}?skill_focus=speaking")
    assert res_skill_speaking.status_code == 200
    assert all(item['skill_focus'] == 'fluency' for item in res_skill_speaking.data)

    res_skill_all = api_client.get(f"{url}?skill_focus=ALL")
    assert res_skill_all.status_code == 200
    assert len(res_skill_all.data) >= 1


@pytest.mark.django_db
def test_adaptive_next_exercise(api_client, user, exercise):
    api_client.force_authenticate(user=user)
    url = reverse('exercise-next')

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['id'] == exercise.id
    assert response.data['cefr_level'] == user.primary_user_language.current_cefr_level

@pytest.mark.django_db
def test_recording_upload_and_detail(api_client, user, exercise):
    api_client.force_authenticate(user=user)
    upload_url = reverse('recording-upload')

    dummy_audio = SimpleUploadedFile(
        "sample.webm",
        b"RIFFdummydataformockaudio",
        content_type="audio/webm"
    )

    payload = {
        'exercise_id': exercise.id,
        'audio_file': dummy_audio,
        'mime_type': 'audio/webm',
        'duration_seconds': 42.5,
    }

    upload_res = api_client.post(upload_url, payload, format='multipart')
    assert upload_res.status_code == 201
    recording_id = upload_res.data['id']
    assert upload_res.data['status'] == Recording.Status.UPLOADED
    assert upload_res.data['exercise_title'] == exercise.title

    # Verify underlying hierarchy created: session -> turn -> recording
    recording = Recording.objects.get(id=recording_id)
    assert recording.turn is not None
    assert recording.turn.role == ConversationTurn.Role.USER
    assert recording.turn.turn_sequence == 1
    assert recording.turn.session.exercise == exercise
    assert recording.turn.session.user_language.user == user

    # Query detail
    detail_url = reverse('recording-detail', kwargs={'pk': recording_id})
    detail_res = api_client.get(detail_url)
    assert detail_res.status_code == 200
    assert detail_res.data['id'] == recording_id

@pytest.mark.django_db
def test_progress_metrics_derivation(api_client, user, exercise, english_lang):
    api_client.force_authenticate(user=user)
    user_lang = user.primary_user_language

    session = ConversationSession.objects.create(
        user_language=user_lang,
        exercise=exercise,
        session_title="Metrics Test Session"
    )

    # Turn 1 & Recording 1
    turn1 = ConversationTurn.objects.create(session=session, role=ConversationTurn.Role.USER, turn_sequence=1)
    rec1 = Recording.objects.create(turn=turn1, audio_file="mock1.webm", status=Recording.Status.ANALYZED)
    tag1, _ = WeaknessTag.objects.get_or_create(name="filler_words_high", language=english_lang)
    ar1 = AnalysisResult.objects.create(
        recording=rec1,
        is_current=True,
        estimated_cefr='B1',
        fluency_metrics={"wpm": 120, "pause_count": 2, "filler_count": 1}
    )
    ar1.weakness_tags.set([tag1])

    # Turn 2 & Recording 2
    turn2 = ConversationTurn.objects.create(session=session, role=ConversationTurn.Role.USER, turn_sequence=2)
    rec2 = Recording.objects.create(turn=turn2, audio_file="mock2.webm", status=Recording.Status.ANALYZED)
    tag2, _ = WeaknessTag.objects.get_or_create(name="grammar_error_rate_high", language=english_lang)
    ar2 = AnalysisResult.objects.create(
        recording=rec2,
        is_current=True,
        estimated_cefr='B2',
        fluency_metrics={"wpm": 130, "pause_count": 1, "filler_count": 0}
    )
    ar2.weakness_tags.set([tag2])

    progress_url = reverse('recording-progress')
    res = api_client.get(f"{progress_url}?window=30d")
    assert res.status_code == 200
    data = res.data
    assert data['total_sessions'] == 2
    assert data['average_wpm'] == 125.0
    assert 'filler_words_high' in data['weakness_frequency']
    assert 'grammar_error_rate_high' in data['weakness_frequency']
    assert len(data['time_series']) == 2

@pytest.mark.django_db
def test_conversation_session_turn_counter_locking(user, exercise):
    user_lang = user.primary_user_language
    session = ConversationSession.objects.create(user_language=user_lang, exercise=exercise)
    assert session.turn_counter == 0

    sess, seq1 = ConversationSession.get_next_turn_sequence(session.id)
    assert seq1 == 1
    assert sess.turn_counter == 1

    sess, seq2 = ConversationSession.get_next_turn_sequence(session.id)
    assert seq2 == 2
    assert sess.turn_counter == 2

@pytest.mark.django_db
def test_conversation_turn_unique_sequence_constraint(user, exercise):
    user_lang = user.primary_user_language
    session = ConversationSession.objects.create(user_language=user_lang, exercise=exercise)

    ConversationTurn.objects.create(session=session, role=ConversationTurn.Role.USER, turn_sequence=1)

    # Attempting to create duplicate sequence 1 in the same session raises IntegrityError
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            ConversationTurn.objects.create(session=session, role=ConversationTurn.Role.AGENT, turn_sequence=1)

@pytest.mark.django_db
def test_analysis_result_partial_unique_current_constraint(user, exercise):
    user_lang = user.primary_user_language
    session = ConversationSession.objects.create(user_language=user_lang, exercise=exercise)
    turn = ConversationTurn.objects.create(session=session, role=ConversationTurn.Role.USER, turn_sequence=1)
    rec = Recording.objects.create(turn=turn, audio_file="mock.webm")

    # First active analysis
    AnalysisResult.objects.create(recording=rec, is_current=True, estimated_cefr='B1')

    # Inserting second active analysis without setting previous to is_current=False raises IntegrityError
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            AnalysisResult.objects.create(recording=rec, is_current=True, estimated_cefr='B2')

    # However, inserting an inactive analysis succeeds (historical/re-run support)
    inactive_ar = AnalysisResult.objects.create(recording=rec, is_current=False, estimated_cefr='B2')
    assert inactive_ar.id is not None

@pytest.mark.django_db
def test_model_telemetry_tracking_fields(user, exercise):
    user_lang = user.primary_user_language
    session = ConversationSession.objects.create(user_language=user_lang, exercise=exercise)

    turn = ConversationTurn.objects.create(
        session=session,
        role=ConversationTurn.Role.AGENT,
        turn_sequence=1,
        text_content="Hello, how are you today?",
        llm_model_version="gpt-4o-2024-05-13",
        latency_ms=342,
        input_tokens=150,
        output_tokens=25
    )
    assert turn.llm_model_version == "gpt-4o-2024-05-13"
    assert turn.latency_ms == 342
    assert turn.input_tokens == 150
    assert turn.output_tokens == 25

    rec = Recording.objects.create(turn=turn, audio_file="telemetry.webm")
    ar = AnalysisResult.objects.create(
        recording=rec,
        is_current=True,
        asr_model_version="whisper-large-v3",
        llm_model_version="claude-3-5-sonnet-20241022",
        prompt_version="v2.1",
        latency_asr_ms=450,
        latency_llm_ms=620,
        input_tokens=500,
        output_tokens=180,
        raw_llm_response={"finish_reason": "stop"}
    )
    assert ar.asr_model_version == "whisper-large-v3"
    assert ar.llm_model_version == "claude-3-5-sonnet-20241022"
    assert ar.raw_llm_response["finish_reason"] == "stop"

@pytest.mark.django_db
def test_adaptive_next_exercise_with_language_param(api_client, user):
    api_client.force_authenticate(user=user)

    # Enroll user in Spanish at A2 level
    spanish = Language.objects.create(code='es-ES', name='Spanish')
    UserLanguage.objects.create(
        user=user,
        language=spanish,
        current_cefr_level=CEFRLevel.A2,
        is_primary=False,
        is_learning=True
    )

    es_exercise = Exercise.objects.create(
        language=spanish,
        title="Spanish Speaking Prompt",
        prompt_text="Describe tu ciudad favorita.",
        skill_focus=Exercise.SkillFocus.VOCABULARY,
        cefr_level=CEFRLevel.A2,
    )

    url = reverse('exercise-next')

    # Query with ?language=es-ES -> should recommend Spanish A2 exercise
    res_es = api_client.get(f"{url}?language=es-ES")
    assert res_es.status_code == 200
    assert res_es.data['id'] == es_exercise.id
    assert res_es.data['cefr_level'] == 'A2'

    # Query with language user is not enrolled in -> returns 400
    res_not_enrolled = api_client.get(f"{url}?language=it-IT")
    assert res_not_enrolled.status_code == 400

@pytest.mark.django_db
def test_progress_metrics_isolated_by_language(api_client, user, english_lang):
    api_client.force_authenticate(user=user)

    # 1. Session and analysis in English
    en_ul = user.primary_user_language
    en_session = ConversationSession.objects.create(user_language=en_ul)
    en_turn = ConversationTurn.objects.create(session=en_session, role=ConversationTurn.Role.USER, turn_sequence=1)
    en_rec = Recording.objects.create(turn=en_turn, audio_file="en.webm")
    AnalysisResult.objects.create(
        recording=en_rec,
        is_current=True,
        estimated_cefr='B1',
        fluency_metrics={"wpm": 120.0, "pause_count": 2}
    )

    # 2. Session and analysis in Spanish
    spanish = Language.objects.create(code='es-ES', name='Spanish')
    es_ul = UserLanguage.objects.create(
        user=user,
        language=spanish,
        current_cefr_level=CEFRLevel.A2,
        is_primary=False,
        is_learning=True
    )
    es_session = ConversationSession.objects.create(user_language=es_ul)
    es_turn = ConversationTurn.objects.create(session=es_session, role=ConversationTurn.Role.USER, turn_sequence=1)
    es_rec = Recording.objects.create(turn=es_turn, audio_file="es.webm")
    AnalysisResult.objects.create(
        recording=es_rec,
        is_current=True,
        estimated_cefr='A2',
        fluency_metrics={"wpm": 80.0, "pause_count": 5}
    )

    progress_url = reverse('recording-progress')

    # Query Spanish specifically
    res_es = api_client.get(f"{progress_url}?language=es-ES")
    assert res_es.status_code == 200
    assert res_es.data['language'] == 'es-ES'
    assert res_es.data['total_sessions'] == 1
    assert res_es.data['average_wpm'] == 80.0
    assert res_es.data['current_cefr'] == 'A2'

    # Query English specifically
    res_en = api_client.get(f"{progress_url}?language=en-US")
    assert res_en.status_code == 200
    assert res_en.data['language'] == 'en-US'
    assert res_en.data['total_sessions'] == 1
    assert res_en.data['average_wpm'] == 120.0
    assert res_en.data['current_cefr'] == 'B1'

    # Query All languages
    res_all = api_client.get(f"{progress_url}?language=all")
    assert res_all.status_code == 200
    assert res_all.data['language'] == 'all'
    assert res_all.data['total_sessions'] == 2
    assert res_all.data['average_wpm'] == 100.0

@pytest.mark.django_db
def test_recording_upload_auto_binds_to_exercise_target_language(api_client, user):
    api_client.force_authenticate(user=user)

    japanese = Language.objects.create(code='ja-JP', name='Japanese')
    ja_exercise = Exercise.objects.create(
        language=japanese,
        title="Japanese Prompt",
        prompt_text="Konnichiwa.",
        cefr_level=CEFRLevel.A1
    )

    upload_url = reverse('recording-upload')
    audio_file = SimpleUploadedFile("speech.webm", b"mockaudiodata", content_type="audio/webm")

    # Upload audio for Japanese exercise (user not yet enrolled)
    res = api_client.post(upload_url, {
        'exercise_id': ja_exercise.id,
        'audio_file': audio_file,
    }, format='multipart')

    assert res.status_code == 201
    recording = Recording.objects.get(id=res.data['id'])
    assert recording.turn.session.user_language.language.code == 'ja-JP'
    assert recording.turn.session.user_language.user == user
    assert recording.turn.session.user_language.is_primary is False


@pytest.mark.django_db
def test_recording_analysis_pipeline_completion(api_client, user, exercise):
    """
    Verifies that uploading a recording triggers the analysis task eagerly,
    updates recording status to ANALYZED, creates an AnalysisResult with
    CEFR/fluency/grammar/vocab data, and atomically increments user practice stats.
    """
    api_client.force_authenticate(user=user)
    upload_url = reverse('recording-upload')
    audio_file = SimpleUploadedFile("speech.webm", b"mockaudiodata_test_pipeline", content_type="audio/webm")

    res = api_client.post(upload_url, {
        'exercise_id': exercise.id,
        'audio_file': audio_file,
        'duration_seconds': 35.0,
    }, format='multipart')

    assert res.status_code == 201
    recording_id = res.data['id']

    # Detail view should show analyzed recording with analysis payload
    detail_url = reverse('recording-detail', kwargs={'pk': recording_id})
    detail_res = api_client.get(detail_url)
    assert detail_res.status_code == 200
    data = detail_res.data

    assert data['status'] == 'analyzed'
    assert data['analysis'] is not None
    assert data['analysis']['estimated_cefr'] == exercise.cefr_level
    assert data['analysis']['fluency_metrics']['wpm'] > 0
    assert 'overall_score' in data['analysis']['grammar_feedback']
    assert 'overall_score' in data['analysis']['vocabulary_feedback']
    assert len(data['analysis']['weakness_tags']) >= 1

    # Verify user language stats incremented atomically
    user_lang = user.user_languages.get(language=exercise.language)
    assert user_lang.total_sessions_completed >= 1
    assert user_lang.total_practice_seconds >= 35


