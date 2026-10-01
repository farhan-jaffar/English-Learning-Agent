from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from core.choices import CEFRLevel
from .models import User, Language, UserLanguage

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'code', 'name', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserLanguageSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)

    class Meta:
        model = UserLanguage
        fields = [
            'id',
            'language',
            'language_code',
            'language_name',
            'current_cefr_level',
            'target_goal',
            'is_native',
            'is_learning',
            'is_primary',
            'total_practice_seconds',
            'total_sessions_completed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'language_code',
            'language_name',
            'total_practice_seconds',
            'total_sessions_completed',
            'created_at',
            'updated_at',
        ]

class UserLanguageEnrollSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(write_only=True, required=False)
    language = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), required=False)
    current_cefr_level = serializers.ChoiceField(choices=CEFRLevel.choices, default=CEFRLevel.A1, required=False)
    target_goal = serializers.CharField(max_length=100, default='General Fluency', required=False)
    is_primary = serializers.BooleanField(default=False, required=False)
    is_native = serializers.BooleanField(default=False, required=False)
    language_details = UserLanguageSerializer(source='*', read_only=True)

    class Meta:
        model = UserLanguage
        fields = [
            'id',
            'language',
            'language_code',
            'current_cefr_level',
            'target_goal',
            'is_primary',
            'is_native',
            'is_learning',
            'language_details',
            'total_practice_seconds',
            'total_sessions_completed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'language_details', 'total_practice_seconds', 'total_sessions_completed', 'created_at', 'updated_at']

    def validate(self, attrs):
        user = self.context['request'].user
        lang = attrs.get('language')
        code = attrs.get('language_code')

        if not lang and not code:
            raise serializers.ValidationError("Either 'language' ID or 'language_code' must be provided.")

        if not lang and code:
            lang_names = {
                'en-US': 'English (US)',
                'es-ES': 'Spanish (Spain)',
                'fr-FR': 'French (France)',
                'de-DE': 'German (Germany)',
                'it-IT': 'Italian (Italy)',
                'pt-BR': 'Portuguese (Brazil)',
                'ja-JP': 'Japanese (Japan)',
                'zh-CN': 'Chinese (Simplified)',
            }
            default_name = lang_names.get(code, code)
            lang, _ = Language.objects.get_or_create(
                code=code,
                defaults={'name': default_name, 'is_active': True}
            )
            attrs['language'] = lang

        attrs.pop('language_code', None)

        if UserLanguage.objects.filter(user=user, language=attrs['language']).exists():
            raise serializers.ValidationError(f"You are already enrolled in language '{attrs['language'].code}'.")

        return attrs

    def create(self, validated_data):
        from django.db import transaction
        user = self.context['request'].user
        is_primary = validated_data.get('is_primary', False)

        with transaction.atomic():
            if is_primary:
                UserLanguage.objects.filter(user=user, is_primary=True).update(is_primary=False)
            user_language = UserLanguage.objects.create(user=user, **validated_data)
        return user_language

class UserLanguageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLanguage
        fields = [
            'current_cefr_level',
            'target_goal',
            'is_learning',
            'is_primary',
        ]

    def update(self, instance, validated_data):
        from django.db import transaction
        is_primary = validated_data.get('is_primary')
        with transaction.atomic():
            if is_primary:
                UserLanguage.objects.filter(user=instance.user, is_primary=True).exclude(pk=instance.pk).update(is_primary=False)
            return super().update(instance, validated_data)

class UserSerializer(serializers.ModelSerializer):
    cefr_level = serializers.SerializerMethodField(help_text="Derived explicitly from primary UserLanguage")
    native_language = serializers.SerializerMethodField(help_text="Derived explicitly from native UserLanguage")
    target_goal = serializers.SerializerMethodField(help_text="Derived explicitly from primary UserLanguage")
    user_languages = UserLanguageSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'is_active',
            'cefr_level',
            'native_language',
            'target_goal',
            'user_languages',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

    def get_cefr_level(self, obj):
        primary = obj.primary_user_language
        return primary.current_cefr_level if primary else CEFRLevel.B1

    def get_target_goal(self, obj):
        primary = obj.primary_user_language
        return primary.target_goal if primary else 'General Fluency'

    def get_native_language(self, obj):
        native = obj.user_languages.filter(is_native=True).select_related('language').first()
        return native.language.name if native else ''

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    cefr_level = serializers.ChoiceField(
        choices=CEFRLevel.choices,
        default=CEFRLevel.B1,
        required=False
    )
    native_language = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    target_goal = serializers.CharField(max_length=100, required=False, allow_blank=True, default='General Fluency')

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'cefr_level',
            'native_language',
            'target_goal',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        cefr_level = validated_data.pop('cefr_level', CEFRLevel.B1)
        native_lang_name = validated_data.pop('native_language', '').strip()
        target_goal = validated_data.pop('target_goal', 'General Fluency')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

        # Ensure default English learning language exists
        english, _ = Language.objects.get_or_create(
            code='en-US',
            defaults={'name': 'English (US)', 'is_active': True}
        )

        # Create primary learning UserLanguage
        UserLanguage.objects.create(
            user=user,
            language=english,
            current_cefr_level=cefr_level,
            target_goal=target_goal,
            is_learning=True,
            is_primary=True,
            is_native=False
        )

        # If native language provided, create native language entry
        if native_lang_name:
            native_code = native_lang_name.lower()[:5]
            native_lang, _ = Language.objects.get_or_create(
                name=native_lang_name,
                defaults={'code': native_code, 'is_active': True}
            )
            UserLanguage.objects.get_or_create(
                user=user,
                language=native_lang,
                defaults={
                    'is_native': True,
                    'is_learning': False,
                    'is_primary': False
                }
            )

        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        # Allow login via username or email
        user = authenticate(username=username, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email=username)
                if user_obj.check_password(password):
                    user = user_obj
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError({"detail": "Invalid username/email or password."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This user account is inactive."})

        attrs['user'] = user
        return attrs
