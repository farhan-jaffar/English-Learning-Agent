import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse
from rest_framework.test import APIClient
from core.choices import CEFRLevel
from apps.authentication.models import User, Language, UserLanguage

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(db):
    def _create_user(
        username='learner1',
        email='learner1@example.com',
        password='StrongPassword123!',
        cefr_level=CEFRLevel.B1,
        native_language='Spanish'
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        english, _ = Language.objects.get_or_create(
            code='en-US',
            defaults={'name': 'English (US)', 'is_active': True}
        )
        UserLanguage.objects.create(
            user=user,
            language=english,
            current_cefr_level=cefr_level,
            target_goal='General Fluency',
            is_primary=True,
            is_learning=True
        )
        if native_language:
            native_code = native_language.lower()[:5]
            native, _ = Language.objects.get_or_create(
                name=native_language,
                defaults={'code': native_code, 'is_active': True}
            )
            UserLanguage.objects.create(
                user=user,
                language=native,
                is_native=True,
                is_learning=False,
                is_primary=False
            )
        return user
    return _create_user

@pytest.mark.django_db
def test_user_registration_success(api_client):
    url = reverse('auth-register')
    payload = {
        'username': 'alice',
        'email': 'alice@example.com',
        'password': 'ComplexPassword123!',
        'password_confirm': 'ComplexPassword123!',
        'cefr_level': 'B2',
        'native_language': 'French',
        'target_goal': 'Job Interview'
    }

    response = api_client.post(url, payload, format='json')
    assert response.status_code == 201
    assert 'access' in response.data
    assert response.data['user']['username'] == 'alice'
    assert response.data['user']['cefr_level'] == 'B2'

    # Verify primary UserLanguage was auto-created
    user = User.objects.get(username='alice')
    primary_ul = user.primary_user_language
    assert primary_ul is not None
    assert primary_ul.language.code == 'en-US'
    assert primary_ul.current_cefr_level == 'B2'
    assert primary_ul.target_goal == 'Job Interview'
    assert primary_ul.is_primary is True

    # Check refresh cookie
    assert 'refresh_token' in response.cookies
    cookie = response.cookies['refresh_token']
    assert cookie['httponly'] is True
    assert cookie['path'] == '/api/auth/refresh/'

@pytest.mark.django_db
def test_user_registration_password_mismatch(api_client):
    url = reverse('auth-register')
    payload = {
        'username': 'bob',
        'email': 'bob@example.com',
        'password': 'ComplexPassword123!',
        'password_confirm': 'DifferentPassword123!',
    }
    response = api_client.post(url, payload, format='json')
    assert response.status_code == 400
    assert 'password_confirm' in response.data

@pytest.mark.django_db
def test_user_login_success(api_client, create_user):
    create_user(username='charlie', password='StrongPassword123!')
    url = reverse('auth-login')

    response = api_client.post(url, {
        'username': 'charlie',
        'password': 'StrongPassword123!'
    }, format='json')

    assert response.status_code == 200
    assert 'access' in response.data
    assert response.data['user']['username'] == 'charlie'
    assert 'refresh_token' in response.cookies
    assert response.cookies['refresh_token']['httponly'] is True

@pytest.mark.django_db
def test_user_login_invalid_password(api_client, create_user):
    create_user(username='david', password='CorrectPassword123!')
    url = reverse('auth-login')

    response = api_client.post(url, {
        'username': 'david',
        'password': 'WrongPassword999!'
    }, format='json')

    assert response.status_code == 400
    assert 'detail' in response.data

@pytest.mark.django_db
def test_current_user_me_endpoint(api_client, create_user):
    user = create_user(username='eve', cefr_level=CEFRLevel.C1)
    url = reverse('auth-me')

    # Unauthenticated request
    res_unauth = api_client.get(url)
    assert res_unauth.status_code == 401

    # Authenticated with Bearer token
    api_client.force_authenticate(user=user)
    res_auth = api_client.get(url)
    assert res_auth.status_code == 200
    assert res_auth.data['username'] == 'eve'
    assert res_auth.data['cefr_level'] == 'C1'

@pytest.mark.django_db
def test_token_refresh_flow(api_client, create_user):
    create_user(username='frank', password='StrongPassword123!')
    login_url = reverse('auth-login')

    # Step 1: Login to acquire refresh cookie
    login_res = api_client.post(login_url, {
        'username': 'frank',
        'password': 'StrongPassword123!'
    }, format='json')
    assert login_res.status_code == 200
    refresh_token = login_res.cookies['refresh_token'].value

    # Step 2: Request new access token using refresh cookie
    refresh_url = reverse('auth-refresh')
    api_client.cookies['refresh_token'] = refresh_token

    refresh_res = api_client.post(refresh_url, {}, format='json')
    assert refresh_res.status_code == 200
    assert 'access' in refresh_res.data

@pytest.mark.django_db
def test_token_refresh_without_cookie(api_client):
    refresh_url = reverse('auth-refresh')
    response = api_client.post(refresh_url, {}, format='json')
    assert response.status_code == 401
    assert 'detail' in response.data

@pytest.mark.django_db
def test_logout_clears_cookie(api_client, create_user):
    create_user(username='grace', password='StrongPassword123!')
    login_url = reverse('auth-login')

    login_res = api_client.post(login_url, {
        'username': 'grace',
        'password': 'StrongPassword123!'
    }, format='json')
    refresh_token = login_res.cookies['refresh_token'].value

    logout_url = reverse('auth-logout')
    api_client.cookies['refresh_token'] = refresh_token

    logout_res = api_client.post(logout_url, {}, format='json')
    assert logout_res.status_code == 200
    assert logout_res.cookies['refresh_token'].value == ''

@pytest.mark.django_db
def test_user_language_constraints(create_user):
    user = create_user(username='constraint_user')
    lang = Language.objects.get(code='en-US')

    # Duplicate (user, language) constraint violation
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            UserLanguage.objects.create(
                user=user,
                language=lang,
                current_cefr_level=CEFRLevel.A2
            )

    # Secondary primary language constraint violation
    es_lang = Language.objects.create(code='es-ES', name='Spanish')
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            UserLanguage.objects.create(
                user=user,
                language=es_lang,
                current_cefr_level=CEFRLevel.A1,
                is_primary=True
            )

@pytest.mark.django_db
def test_user_language_atomic_f_expression(create_user):
    user = create_user(username='f_expr_user')
    ul = user.primary_user_language
    assert ul.total_practice_seconds == 0
    assert ul.total_sessions_completed == 0

    ul.record_session_completion(duration_seconds=45)
    assert ul.total_practice_seconds == 45
    assert ul.total_sessions_completed == 1

    ul.record_session_completion(duration_seconds=55)
    assert ul.total_practice_seconds == 100
    assert ul.total_sessions_completed == 2

@pytest.mark.django_db
def test_language_protected_from_deletion_when_user_language_exists(create_user):
    """
    Verifies that UserLanguage.language on_delete=PROTECT prevents deletion of a Language
    while user learning profiles are associated with it.
    """
    user = create_user(username='protect_test_user')
    english = Language.objects.get(code='en-US')
    assert user.user_languages.filter(language=english).exists()

    with pytest.raises(ProtectedError):
        english.delete()

@pytest.mark.django_db
def test_user_language_list_and_enroll(api_client, create_user):
    user = create_user(username='polyglot_user')
    api_client.force_authenticate(user=user)

    # 1. List current languages (should have English primary + Spanish native)
    url = reverse('auth-user-languages')
    res = api_client.get(url)
    assert res.status_code == 200
    assert len(res.data) >= 1

    # 2. Create target language French
    fr_lang = Language.objects.create(code='fr-FR', name='French')

    # 3. Enroll in French as learning language
    payload = {
        'language_code': 'fr-FR',
        'current_cefr_level': CEFRLevel.A1,
        'target_goal': 'Vacation in Paris',
        'is_primary': False
    }
    enroll_res = api_client.post(url, payload, format='json')
    assert enroll_res.status_code == 201
    assert enroll_res.data['language_code'] == 'fr-FR'
    assert enroll_res.data['current_cefr_level'] == 'A1'
    assert enroll_res.data['target_goal'] == 'Vacation in Paris'

    # 4. Attempt duplicate enrollment -> should fail with 400
    dup_res = api_client.post(url, payload, format='json')
    assert dup_res.status_code == 400

@pytest.mark.django_db
def test_user_language_set_primary_atomicity(api_client, create_user):
    user = create_user(username='switcher_user')
    api_client.force_authenticate(user=user)

    german = Language.objects.create(code='de-DE', name='German')
    de_ul = UserLanguage.objects.create(
        user=user,
        language=german,
        current_cefr_level=CEFRLevel.B2,
        target_goal='Work in Berlin',
        is_primary=False,
        is_learning=True
    )

    # Initially, English is primary
    assert user.primary_user_language.language.code == 'en-US'

    # Set German as primary
    url = reverse('auth-user-language-set-primary', kwargs={'pk': de_ul.pk})
    res = api_client.post(url)
    assert res.status_code == 200
    assert res.data['is_primary'] is True

    # Confirm English is no longer primary and German is now primary
    user.refresh_from_db()
    primary = user.primary_user_language
    assert primary.language.code == 'de-DE'
    assert primary.current_cefr_level == 'B2'

    # Verify /api/auth/me/ reflects updated primary language
    me_res = api_client.get(reverse('auth-me'))
    assert me_res.status_code == 200
    assert me_res.data['cefr_level'] == 'B2'
    assert me_res.data['target_goal'] == 'Work in Berlin'

