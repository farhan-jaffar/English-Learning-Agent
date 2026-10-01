import uuid
from django.db import models, transaction
from core.base_models import BaseTimeModel
from core.choices import CEFRLevel, ConversationRole, RecordingStatus
from apps.authentication.models import User, Language, UserLanguage
from apps.exercises.models import Exercise

class WeaknessTag(BaseTimeModel):
    """
    Normalized weakness tag for pedagogical tracking and analytics (e.g. 'Past Tense', 'Prepositions').
    Tied to a target language.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='weakness_tags'
    )

    class Meta:
        ordering = ['language', 'name']
        verbose_name = 'Weakness Tag'
        verbose_name_plural = 'Weakness Tags'
        constraints = [
            models.UniqueConstraint(
                fields=['language', 'name'],
                name='unique_weakness_tag_per_language'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.language.code})"

class ConversationSession(BaseTimeModel):
    """
    Stateful practice conversation session between learner and AI English Coach.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_language = models.ForeignKey(
        UserLanguage,
        on_delete=models.CASCADE,
        related_name='conversation_sessions'
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_sessions'
    )
    session_title = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)
    conversation_summary = models.TextField(blank=True, default='')
    turn_counter = models.PositiveIntegerField(
        default=0,
        help_text="Incremented under row lock before creating a turn to prevent race conditions"
    )
    snapshot_prompt_text = models.TextField(
        blank=True,
        default='',
        help_text="Snapshots the Exercise prompt so historical sessions remain intact if Exercise is edited"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Conversation Session'
        verbose_name_plural = 'Conversation Sessions'

    def __str__(self) -> str:
        title = self.session_title or (self.exercise.title if self.exercise else 'Free Practice')
        return f"Session {str(self.id)[:8]} - {title} ({self.user_language.user.username})"


    @classmethod
    def get_next_turn_sequence(cls, session_id):
        """
        Acquires an exclusive row lock (select_for_update) on the session,
        atomically increments turn_counter, and returns (session, next_turn_sequence).
        Prevents race conditions in high-concurrency turn creation.
        """
        with transaction.atomic():
            session = cls.objects.select_for_update().get(id=session_id)
            session.turn_counter = models.F('turn_counter') + 1
            session.save(update_fields=['turn_counter', 'updated_at'])
            session.refresh_from_db(fields=['turn_counter'])
            return session, session.turn_counter

class ConversationTurn(BaseTimeModel):
    """
    Individual conversational turn representing either user speech or coach agent response.
    Includes comprehensive LLM telemetry and model tracking fields.
    """
    # Retained as class reference for backwards compatibility; prefer core.choices directly.
    Role = ConversationRole

    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='turns'
    )
    role = models.CharField(max_length=10, choices=ConversationRole.choices)

    turn_sequence = models.PositiveIntegerField(help_text="1-indexed sequence order within the session")
    text_content = models.TextField(blank=True, default='')

    # Model tracking & telemetry fields (null for user turns)
    llm_model_version = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Exact upstream version hash or model ID, e.g. 'gpt-4o-2024-05-13' or 'gemini-1.5-flash-002'"
    )
    latency_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Inference response latency in milliseconds"
    )
    input_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Prompt token count"
    )
    output_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Completion token count"
    )

    class Meta:
        ordering = ['session', 'turn_sequence']
        verbose_name = 'Conversation Turn'
        verbose_name_plural = 'Conversation Turns'
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'turn_sequence'],
                name='unique_session_turn_sequence'
            )
        ]

    def __str__(self) -> str:
        return f"Turn #{self.turn_sequence} [{self.get_role_display()}] in Session {str(self.session_id)[:8]}"


class Recording(BaseTimeModel):
    """
    Audio recording file associated 1-to-1 with a ConversationTurn.
    Stores cloud storage pointer (S3 / GCS URL or relative path) instead of raw bytes.
    """
    # Retained as class reference for backwards compatibility; prefer core.choices directly.
    Status = RecordingStatus

    id = models.BigAutoField(primary_key=True)
    turn = models.OneToOneField(
        ConversationTurn,
        on_delete=models.CASCADE,
        related_name='recording',
        null=True,
        blank=True,
        help_text="Associated user conversation turn"
    )
    audio_file = models.FileField(
        upload_to='recordings/%Y/%m/%d/',
        max_length=1024,
        help_text="Cloud storage pointer/URL to S3 or file storage"
    )
    mime_type = models.CharField(
        max_length=50,
        default='audio/webm',
        help_text="Audio MIME type, e.g. audio/webm or audio/mp4"
    )
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Calculated duration in seconds"
    )
    file_size_bytes = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Audio file size in bytes"
    )
    status = models.CharField(
        max_length=20,
        choices=RecordingStatus.choices,
        default=RecordingStatus.UPLOADED,
        db_index=True,
        help_text="Indexed for queue polling"
    )
    error_message = models.TextField(
        blank=True,
        default='',
        help_text="Error diagnostics if analysis fails"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recording'
        verbose_name_plural = 'Recordings'

    def __str__(self) -> str:
        turn_str = f"Turn #{self.turn.turn_sequence}" if self.turn else "Unlinked"
        return f"Recording #{self.id} [{turn_str}] - {self.status}"


    @property
    def user(self):
        """Convenience accessor to the owning user through turn -> session -> user_language."""
        if self.turn and self.turn.session and self.turn.session.user_language:
            return self.turn.session.user_language.user
        return None

    @property
    def exercise(self):
        """Convenience accessor to exercise through turn -> session."""
        if self.turn and self.turn.session:
            return self.turn.session.exercise
        return None

class AnalysisResult(BaseTimeModel):
    """
    Linguistic feedback and metrics generated for a Recording.
    Many-to-One with Recording allows re-running analysis when prompts or models improve.
    Enforces a partial unique constraint so only one result is marked active (is_current=True) per recording.
    """
    id = models.BigAutoField(primary_key=True)
    recording = models.ForeignKey(
        Recording,
        on_delete=models.CASCADE,
        related_name='analysis_results',
        help_text="Foreign Key allows re-running analysis on the same recording"
    )
    is_current = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flags the active result among multiple runs"
    )
    estimated_cefr = models.CharField(
        max_length=2,
        choices=CEFRLevel.choices,
        default=CEFRLevel.B1,
        help_text="Estimated CEFR level for this response"
    )
    grammar_feedback = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured grammar evaluation, errors, and suggested corrections"
    )
    vocabulary_feedback = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured vocabulary sophistication and recommendations"
    )
    fluency_metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Calculated metrics: wpm, pause_count, avg_pause_ms, filler_count"
    )
    word_timestamps = models.JSONField(
        default=list,
        blank=True,
        help_text="List of word objects with start_offset and end_offset in seconds"
    )

    # Telemetry and upstream version tracking
    asr_model_version = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Exact speech-to-text model version, e.g. 'whisper-large-v3' or 'gemini-1.5-flash'"
    )
    llm_model_version = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Exact analysis LLM version, e.g. 'gpt-4o-2024-05-13'"
    )
    prompt_version = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Version identifier of prompt template used"
    )
    latency_asr_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Transcription latency in ms")
    latency_llm_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Analysis LLM latency in ms")
    input_tokens = models.PositiveIntegerField(null=True, blank=True, help_text="Prompt tokens consumed")
    output_tokens = models.PositiveIntegerField(null=True, blank=True, help_text="Output tokens generated")
    raw_llm_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw verbatim upstream response payload for debugging and verification"
    )

    weakness_tags = models.ManyToManyField(
        WeaknessTag,
        related_name='analysis_results',
        blank=True,
        help_text="Normalized weakness tags identified during analysis"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'
        constraints = [
            models.UniqueConstraint(
                fields=['recording'],
                condition=models.Q(is_current=True),
                name='unique_current_analysis_per_recording'
            )
        ]

    def __str__(self) -> str:
        curr_label = " [CURRENT]" if self.is_current else ""
        return f"Analysis #{self.id} for Recording #{self.recording_id} (CEFR {self.estimated_cefr}){curr_label}"


    def set_as_current(self):
        """Atomically marks this analysis as the current one for its recording, deactivating others."""
        with transaction.atomic():
            AnalysisResult.objects.filter(recording=self.recording, is_current=True).exclude(pk=self.pk).update(is_current=False)
            self.is_current = True
            self.save(update_fields=['is_current', 'updated_at'])


class AgentDecisionLog(BaseTimeModel):
    """
    Persisted log of adaptive agent policy decisions and reasons for cross-session continuity.
    """
    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='agent_decisions',
        null=True,
        blank=True
    )
    turn = models.ForeignKey(
        ConversationTurn,
        on_delete=models.SET_NULL,
        related_name='agent_decisions',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agent_decisions'
    )
    action = models.CharField(
        max_length=50,
        help_text="CONTINUE, REMEDIATE, ASK_FOLLOW_UP, INCREASE_DIFFICULTY, GIVE_FEEDBACK"
    )
    target_skill = models.CharField(max_length=50, blank=True, default='')
    target_weakness = models.CharField(max_length=100, blank=True, default='')
    difficulty = models.CharField(max_length=10, blank=True, default='')
    reason = models.TextField(blank=True, default='')
    was_executed = models.BooleanField(
        default=False,
        help_text="Whether this decision (e.g. REMEDIATE) was executed into a concrete exercise"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Decision Log'
        verbose_name_plural = 'Agent Decision Logs'

    def __str__(self) -> str:
        return f"AgentDecision #{self.id} [{self.action}] user={self.user_id} ({self.created_at})"

