from django.contrib import admin
from .models import Exercise, TopicTag

@admin.register(TopicTag)
class TopicTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'cefr_level', 'skill_focus', 'source', 'created_at')
    list_filter = ('language', 'cefr_level', 'skill_focus', 'source')
    search_fields = ('title', 'prompt_text')
    filter_horizontal = ('topic_tags',)
