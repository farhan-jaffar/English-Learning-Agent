from rest_framework import serializers
from .models import Exercise, TopicTag
from apps.authentication.models import Language

class TopicTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicTag
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ExerciseSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)
    topic_tags = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=TopicTag.objects.all(),
        required=False
    )

    class Meta:
        model = Exercise
        fields = [
            'id',
            'language',
            'language_code',
            'title',
            'prompt_text',
            'skill_focus',
            'topic_tags',
            'cefr_level',
            'source',
            'vocabulary_hints',
            'min_duration_seconds',
            'max_duration_seconds',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'language_code', 'created_at', 'updated_at']
