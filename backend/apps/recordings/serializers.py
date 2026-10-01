from rest_framework import serializers
from .models import Recording, AnalysisResult, WeaknessTag, ConversationSession, ConversationTurn
from apps.exercises.models import Exercise
from apps.authentication.models import UserLanguage, Language

class WeaknessTagSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)

    class Meta:
        model = WeaknessTag
        fields = ['id', 'name', 'language', 'language_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConversationTurnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationTurn
        fields = [
            'id',
            'session',
            'role',
            'turn_sequence',
            'text_content',
            'llm_model_version',
            'latency_ms',
            'input_tokens',
            'output_tokens',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConversationTurnDetailSerializer(serializers.ModelSerializer):
    recording_id = serializers.IntegerField(source='recording.id', read_only=True, default=None)
    audio_url = serializers.SerializerMethodField()
    analysis = serializers.SerializerMethodField()

    class Meta:
        model = ConversationTurn
        fields = [
            'id',
            'session',
            'role',
            'turn_sequence',
            'text_content',
            'recording_id',
            'audio_url',
            'analysis',
            'llm_model_version',
            'latency_ms',
            'input_tokens',
            'output_tokens',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_audio_url(self, obj):
        try:
            if hasattr(obj, 'recording') and obj.recording and obj.recording.audio_file:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.recording.audio_file.url)
                return obj.recording.audio_file.url
        except Exception:
            pass
        return None

    def get_analysis(self, obj):
        try:
            if hasattr(obj, 'recording') and obj.recording:
                current_res = obj.recording.analysis_results.filter(is_current=True).first()
                if current_res:
                    return AnalysisResultSerializer(current_res).data
        except Exception:
            pass
        return None

class ConversationSessionSerializer(serializers.ModelSerializer):
    turns = ConversationTurnSerializer(many=True, read_only=True)
    exercise_title = serializers.CharField(source='exercise.title', read_only=True, default=None)

    class Meta:
        model = ConversationSession
        fields = [
            'id',
            'user_language',
            'exercise',
            'exercise_title',
            'session_title',
            'is_active',
            'conversation_summary',
            'turn_counter',
            'snapshot_prompt_text',
            'turns',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'turn_counter', 'created_at', 'updated_at']

class ConversationSessionDetailSerializer(serializers.ModelSerializer):
    turns = ConversationTurnDetailSerializer(many=True, read_only=True)
    exercise_title = serializers.CharField(source='exercise.title', read_only=True, default=None)
    language_code = serializers.CharField(source='user_language.language.code', read_only=True, default='en-US')

    class Meta:
        model = ConversationSession
        fields = [
            'id',
            'user_language',
            'language_code',
            'exercise',
            'exercise_title',
            'session_title',
            'is_active',
            'conversation_summary',
            'turn_counter',
            'snapshot_prompt_text',
            'turns',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'turn_counter', 'created_at', 'updated_at']

class StartConversationSessionSerializer(serializers.Serializer):
    scenario_id = serializers.CharField(required=True)
    custom_title = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_scenario_id(self, value):
        from .conversations import SCENARIOS
        if value not in SCENARIOS:
            raise serializers.ValidationError(f"Invalid scenario '{value}'. Choices are: {', '.join(SCENARIOS.keys())}")
        return value

class ConversationTurnReplySerializer(serializers.Serializer):
    audio_file = serializers.FileField(required=True)
    duration_seconds = serializers.FloatField(required=False, default=0.0)
    mime_type = serializers.CharField(required=False, default='audio/webm')

    def validate_audio_file(self, file):
        max_size = 25 * 1024 * 1024
        if file.size > max_size:
            raise serializers.ValidationError("Audio file exceeds maximum allowed size of 25MB.")
        return file


class AnalysisResultSerializer(serializers.ModelSerializer):
    weakness_tags = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=WeaknessTag.objects.all(),
        required=False
    )

    class Meta:
        model = AnalysisResult
        fields = [
            'id',
            'recording_id',
            'is_current',
            'estimated_cefr',
            'grammar_feedback',
            'vocabulary_feedback',
            'fluency_metrics',
            'word_timestamps',
            'asr_model_version',
            'llm_model_version',
            'prompt_version',
            'latency_asr_ms',
            'latency_llm_ms',
            'input_tokens',
            'output_tokens',
            'raw_llm_response',
            'weakness_tags',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class RecordingSerializer(serializers.ModelSerializer):
    analysis = serializers.SerializerMethodField()
    exercise_title = serializers.CharField(source='exercise.title', read_only=True, default=None)
    exercise_id = serializers.IntegerField(source='exercise.id', read_only=True, default=None)
    session_id = serializers.UUIDField(source='turn.session_id', read_only=True, default=None)
    turn_sequence = serializers.IntegerField(source='turn.turn_sequence', read_only=True, default=None)

    class Meta:
        model = Recording
        fields = [
            'id',
            'turn',
            'session_id',
            'turn_sequence',
            'exercise_id',
            'exercise_title',
            'audio_file',
            'mime_type',
            'duration_seconds',
            'file_size_bytes',
            'status',
            'error_message',
            'analysis',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'error_message', 'created_at', 'updated_at']

    def get_analysis(self, obj):
        current_res = obj.analysis_results.filter(is_current=True).first()
        if current_res:
            return AnalysisResultSerializer(current_res).data
        return None

class RecordingUploadSerializer(serializers.ModelSerializer):
    exercise_id = serializers.IntegerField(required=False, allow_null=True)
    turn_id = serializers.IntegerField(required=False, allow_null=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    audio_file = serializers.FileField(required=True)

    class Meta:
        model = Recording
        fields = [
            'exercise_id',
            'session_id',
            'turn_id',
            'audio_file',
            'mime_type',
            'duration_seconds',
        ]

    def validate_audio_file(self, file):
        # Enforce max audio size: 25 MB
        max_size = 25 * 1024 * 1024
        if file.size > max_size:
            raise serializers.ValidationError("Audio file exceeds maximum allowed size of 25MB.")
        return file

    def validate_exercise_id(self, value):
        if value is not None and not Exercise.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Exercise with id {value} does not exist.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        turn_id = validated_data.pop('turn_id', None)
        session_id = validated_data.pop('session_id', None)
        exercise_id = validated_data.pop('exercise_id', None)
        audio_file = validated_data['audio_file']
        file_size = audio_file.size

        turn = None
        if turn_id:
            turn = ConversationTurn.objects.get(id=turn_id)
        else:
            exercise = None
            if exercise_id:
                exercise = Exercise.objects.get(id=exercise_id)

            # Match learner's UserLanguage to exercise target language, or fallback to primary
            user_language = None
            if exercise and exercise.language:
                user_language = user.user_languages.filter(language=exercise.language).first()
                if not user_language:
                    # Auto-enroll in exercise target language
                    user_language = UserLanguage.objects.create(
                        user=user,
                        language=exercise.language,
                        current_cefr_level=exercise.cefr_level,
                        target_goal='General Fluency',
                        is_learning=True,
                        is_primary=False
                    )

            if not user_language:
                user_language = user.primary_user_language

            if not user_language:
                english, _ = Language.objects.get_or_create(
                    code='en-US',
                    defaults={'name': 'English (US)', 'is_active': True}
                )
                user_language, _ = UserLanguage.objects.get_or_create(
                    user=user,
                    language=english,
                    defaults={'is_primary': True, 'is_learning': True}
                )

            # Retrieve or create session
            session = None
            if session_id:
                session = ConversationSession.objects.filter(id=session_id, user_language=user_language).first()

            if not session:
                snapshot_text = exercise.prompt_text if exercise else ''
                title = exercise.title if exercise else 'Speaking Practice'
                session = ConversationSession.objects.create(
                    user_language=user_language,
                    exercise=exercise,
                    session_title=title,
                    snapshot_prompt_text=snapshot_text
                )

            # Increment turn counter under row lock
            _, next_seq = ConversationSession.get_next_turn_sequence(session.id)

            turn = ConversationTurn.objects.create(
                session=session,
                role=ConversationTurn.Role.USER,
                turn_sequence=next_seq,
                text_content=''
            )

        recording = Recording.objects.create(
            turn=turn,
            audio_file=audio_file,
            mime_type=validated_data.get('mime_type', 'audio/webm'),
            duration_seconds=validated_data.get('duration_seconds'),
            file_size_bytes=file_size,
            status=Recording.Status.UPLOADED
        )
        return recording
