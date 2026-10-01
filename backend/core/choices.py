from django.db import models

class CEFRLevel(models.TextChoices):
    """
    Common European Framework of Reference for Languages (CEFR) standard levels.
    Shared across authentication, exercises, recordings, and analytics.
    """
    A1 = 'A1', 'A1 - Beginner'
    A2 = 'A2', 'A2 - Elementary'
    B1 = 'B1', 'B1 - Intermediate'
    B2 = 'B2', 'B2 - Upper Intermediate'
    C1 = 'C1', 'C1 - Advanced'
    C2 = 'C2', 'C2 - Mastery'


class SkillFocus(models.TextChoices):
    """
    Primary pedagogical skill targeted by an exercise prompt or analysis weakness tag.
    """
    GRAMMAR = 'grammar', 'Grammar'
    VOCABULARY = 'vocabulary', 'Vocabulary'
    FLUENCY = 'fluency', 'Fluency'
    PRONUNCIATION = 'pronunciation', 'Pronunciation'
    MIXED = 'mixed', 'Mixed'


class ExerciseSourceType(models.TextChoices):
    """
    Origin and generation method of practice exercise content.
    """
    STATIC = 'static', 'Pre-curated'
    GENERATED = 'generated', 'AI Adaptive'


class ConversationRole(models.TextChoices):
    """
    Speaker participant in a conversational dialogue turn.
    """
    USER = 'user', 'User'
    AGENT = 'agent', 'Agent'


class RecordingStatus(models.TextChoices):
    """
    Lifecycle state of an audio recording through the analysis pipeline.
    """
    UPLOADED = 'uploaded', 'Uploaded'
    PROCESSING = 'processing', 'Processing'
    ANALYZED = 'analyzed', 'Analyzed'
    FAILED = 'failed', 'Failed'
