from django.contrib import admin
from .models import WeaknessTag, ConversationSession, ConversationTurn, Recording, AnalysisResult

@admin.register(WeaknessTag)
class WeaknessTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'language', 'created_at')
    list_filter = ('language',)
    search_fields = ('name',)

class ConversationTurnInline(admin.TabularInline):
    model = ConversationTurn
    extra = 0
    fields = ('turn_sequence', 'role', 'text_content', 'llm_model_version', 'latency_ms', 'input_tokens', 'output_tokens')
    readonly_fields = ('created_at',)

@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_language', 'exercise', 'turn_counter', 'is_active', 'created_at')
    list_filter = ('is_active', 'user_language__language', 'created_at')
    search_fields = ('id', 'session_title', 'user_language__user__username')
    inlines = [ConversationTurnInline]

@admin.register(ConversationTurn)
class ConversationTurnAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'turn_sequence', 'llm_model_version', 'latency_ms', 'created_at')
    list_filter = ('role', 'llm_model_version', 'created_at')
    search_fields = ('session__id', 'text_content')

@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ('id', 'turn', 'status', 'duration_seconds', 'file_size_bytes', 'created_at')
    list_filter = ('status', 'mime_type', 'created_at')
    search_fields = ('turn__session__user_language__user__username', 'turn__session__id')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'recording', 'is_current', 'estimated_cefr', 'llm_model_version', 'asr_model_version', 'created_at')
    list_filter = ('is_current', 'estimated_cefr', 'llm_model_version', 'created_at')
    search_fields = ('recording__id', 'recording__turn__session__user_language__user__username')
    filter_horizontal = ('weakness_tags',)
