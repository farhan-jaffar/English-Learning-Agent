"""
Generated Exercise schema for adaptive practice.
"""

from pydantic import BaseModel, Field

class GeneratedExercise(BaseModel):
    """Schema for dynamically generated remediation or stretch exercises."""
    title: str = Field(..., description="Short engaging exercise title")
    prompt_text: str = Field(..., description="Spoken prompt instructions for the learner")
    skill_focus: str = Field(default="grammar", description="Target skill: grammar, vocabulary, fluency, pronunciation")
    cefr_level: str = Field(default="B1", description="Target CEFR level A1-C2")
    vocabulary_hints: list[str] = Field(default_factory=list, description="Target vocabulary to encourage usage")
    topic: str = Field(default="Daily Life", description="Topic category e.g. Travel, Business, Social")
    min_duration_seconds: int = Field(default=20, description="Minimum recommended speaking duration")
    max_duration_seconds: int = Field(default=90, description="Maximum recommended speaking duration")
