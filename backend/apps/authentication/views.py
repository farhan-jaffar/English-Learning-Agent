from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import UserLanguage
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UserLanguageSerializer,
    UserLanguageEnrollSerializer,
    UserLanguageUpdateSerializer,
)

def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Helper to attach the refresh token as a secure httpOnly cookie."""
    cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH_NAME', 'refresh_token')
    cookie_path = getattr(settings, 'AUTH_COOKIE_PATH', '/api/auth/refresh/')
    cookie_httponly = getattr(settings, 'AUTH_COOKIE_HTTP_ONLY', True)
    cookie_samesite = getattr(settings, 'AUTH_COOKIE_SAMESITE', 'Lax')
    cookie_secure = getattr(settings, 'AUTH_COOKIE_SECURE', not settings.DEBUG)
    max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

    response.set_cookie(
        key=cookie_name,
        value=refresh_token,
        max_age=max_age,
        path=cookie_path,
        httponly=cookie_httponly,
        samesite=cookie_samesite,
        secure=cookie_secure,
    )

def clear_refresh_cookie(response: Response) -> None:
    """Helper to delete the refresh token cookie."""
    cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH_NAME', 'refresh_token')
    cookie_path = getattr(settings, 'AUTH_COOKIE_PATH', '/api/auth/refresh/')
    response.delete_cookie(key=cookie_name, path=cookie_path)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                'access': access_token,
                'user': UserSerializer(user).data,
                'message': 'Registration successful.',
            },
            status=status.HTTP_201_CREATED
        )
        set_refresh_cookie(response, refresh_token)
        return response

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                'access': access_token,
                'user': UserSerializer(user).data,
                'message': 'Login successful.',
            },
            status=status.HTTP_200_OK
        )
        set_refresh_cookie(response, refresh_token)
        return response

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH_NAME', 'refresh_token')
        raw_refresh = request.COOKIES.get(cookie_name)

        if not raw_refresh:
            return Response(
                {'detail': 'Authentication refresh cookie not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            token = RefreshToken(raw_refresh)
            data = {'access': str(token.access_token)}

            response = Response(data, status=status.HTTP_200_OK)

            # If token rotation is enabled, blacklist old token and set new cookie
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                token.blacklist()
                user_id = token.payload.get(settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id'))
                from .models import User
                try:
                    user = User.objects.get(id=user_id)
                    new_token = RefreshToken.for_user(user)
                    set_refresh_cookie(response, str(new_token))
                except User.DoesNotExist:
                    pass

            return response
        except (TokenError, InvalidToken) as exc:
            response = Response(
                {'detail': 'Invalid or expired refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            clear_refresh_cookie(response)
            return response

class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cookie_name = getattr(settings, 'AUTH_COOKIE_REFRESH_NAME', 'refresh_token')
        raw_refresh = request.COOKIES.get(cookie_name)

        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
                token.blacklist()
            except TokenError:
                pass

        response = Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_200_OK
        )
        clear_refresh_cookie(response)
        return response

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserLanguageListCreateView(APIView):
    """
    GET: List all language learning profiles for the authenticated user.
    POST: Enroll in a new language.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        languages = request.user.user_languages.select_related('language').all()
        return Response(UserLanguageSerializer(languages, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserLanguageEnrollSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user_language = serializer.save()
        return Response(UserLanguageSerializer(user_language).data, status=status.HTTP_201_CREATED)

class UserLanguageDetailView(APIView):
    """
    GET: Retrieve details of a specific UserLanguage profile.
    PATCH: Update target_goal, current_cefr_level, or active learning status.
    DELETE: Unenroll from a language profile.
    """
    permission_classes = [IsAuthenticated]

    def _get_object(self, request, pk):
        try:
            return request.user.user_languages.select_related('language').get(pk=pk)
        except UserLanguage.DoesNotExist:
            return None

    def get(self, request, pk):
        user_lang = self._get_object(request, pk)
        if not user_lang:
            return Response({"detail": "User language profile not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserLanguageSerializer(user_lang).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        user_lang = self._get_object(request, pk)
        if not user_lang:
            return Response({"detail": "User language profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserLanguageUpdateSerializer(user_lang, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(UserLanguageSerializer(updated).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        user_lang = self._get_object(request, pk)
        if not user_lang:
            return Response({"detail": "User language profile not found."}, status=status.HTTP_404_NOT_FOUND)

        if user_lang.is_primary and request.user.user_languages.count() > 1:
            return Response(
                {"detail": "Cannot delete your primary language. Please designate another language as primary first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_lang.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserLanguageSetPrimaryView(APIView):
    """
    POST: Atomically designate this language profile as the learner's active primary language.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from django.db import transaction
        try:
            user_language = request.user.user_languages.select_related('language').get(pk=pk)
        except UserLanguage.DoesNotExist:
            return Response({"detail": "User language profile not found."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            request.user.user_languages.filter(is_primary=True).exclude(pk=user_language.pk).update(is_primary=False)
            user_language.is_primary = True
            user_language.save(update_fields=['is_primary', 'updated_at'])

        return Response(UserLanguageSerializer(user_language).data, status=status.HTTP_200_OK)
