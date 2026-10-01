import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from core.choices import CEFRLevel, ConversationRole
from apps.authentication.models import User, Language, UserLanguage
from apps.recordings.models import ConversationSession, ConversationTurn, Recording

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
        username='convo_tester',
        email='convo_tester@example.com',
        password='StrongPassword123!',
    )
    UserLanguage.objects.create(
        user=u,
        language=english_lang,
        current_cefr_level=CEFRLevel.B2,
        is_primary=True,
        is_learning=True
    )
    return u

@pytest.mark.django_db
def test_conversation_scenarios_list(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse('conversation-scenarios')
    response = api_client.get(url)

    assert response.status_code == 200
    scenarios = response.data
    assert len(scenarios) >= 4
    scenario_ids = [s['id'] for s in scenarios]
    assert 'job_interview' in scenario_ids
    assert 'coffee_shop' in scenario_ids
    assert 'airport_travel' in scenario_ids
    assert 'tech_debate' in scenario_ids

@pytest.mark.django_db
def test_start_conversation_session(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse('conversation-sessions')
    payload = {
        'scenario_id': 'job_interview',
        'custom_title': 'My Mock Tech Interview'
    }
    response = api_client.post(url, payload, format='json')

    assert response.status_code == 201
    data = response.data
    assert data['session_title'] == 'My Mock Tech Interview'
    assert data['is_active'] is True
    assert data['turn_counter'] == 1
    assert len(data['turns']) == 1

    first_turn = data['turns'][0]
    assert first_turn['role'] == ConversationRole.AGENT
    assert first_turn['turn_sequence'] == 1
    assert "Hello and welcome" in first_turn['text_content']

@pytest.mark.django_db
def test_conversation_turn_reply_and_coach_response(api_client, user):
    api_client.force_authenticate(user=user)
    # 1. Start session
    start_url = reverse('conversation-sessions')
    start_resp = api_client.post(start_url, {'scenario_id': 'coffee_shop'}, format='json')
    session_id = start_resp.data['id']

    # 2. Reply with user audio
    reply_url = reverse('conversation-turn-reply', kwargs={'pk': session_id})
    dummy_audio = SimpleUploadedFile(
        "order.webm",
        b"\x1a\x45\xdf\xa3" + b"dummy audio speech content",
        content_type="audio/webm"
    )
    reply_resp = api_client.post(
        reply_url,
        {
            'audio_file': dummy_audio,
            'duration_seconds': 14.5,
            'mime_type': 'audio/webm'
        },
        format='multipart'
    )

    assert reply_resp.status_code == 201
    data = reply_resp.data
    assert data['turn_counter'] == 3  # Turn 1 (Agent), Turn 2 (User), Turn 3 (Agent follow-up)
    assert len(data['turns']) == 3

    user_turn = data['turns'][1]
    assert user_turn['role'] == ConversationRole.USER
    assert user_turn['turn_sequence'] == 2
    assert user_turn['recording_id'] is not None
    assert user_turn['analysis'] is not None
    assert user_turn['analysis']['fluency_metrics']['wpm'] > 0

    coach_turn = data['turns'][2]
    assert coach_turn['role'] == ConversationRole.AGENT
    assert coach_turn['turn_sequence'] == 3
    assert len(coach_turn['text_content']) > 10

@pytest.mark.django_db
def test_conclude_conversation_session(api_client, user):
    api_client.force_authenticate(user=user)
    start_url = reverse('conversation-sessions')
    start_resp = api_client.post(start_url, {'scenario_id': 'airport_travel'}, format='json')
    session_id = start_resp.data['id']

    conclude_url = reverse('conversation-session-conclude', kwargs={'pk': session_id})
    resp = api_client.post(conclude_url)

    assert resp.status_code == 200
    assert resp.data['is_active'] is False
    assert "concluded" in resp.data['conversation_summary'].lower()
