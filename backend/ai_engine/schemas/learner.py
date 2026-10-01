"""
Learner state schema for pedagogical memory and adaptive planning.
"""

from typing import Optional
from pydantic import BaseModel, Field

class LearnerWeakness(BaseModel):
    """Tracks a specific weakness with frequency and recency weighting."""
    tag: str = Field(..., description="Weakness category name e.g. 'Past Tense'")
    frequency: int = Field(default=1, description="Count of occurrences across practice sessions")
    is_recurring: bool = Field(default=False, description="True if frequency >= threshold")
    last_observed_session_id: Optional[str] = Field(default=None, description="UUID of most recent session")

class LearnerState(BaseModel):
    """
    Compact learner profile synthesized from database records for the Adaptive Agent.
    Avoids passing the full historical database into LLM context.
    """
    user_id: int
    username: str
    target_language: str = "en-US"
    current_cefr: str = "B1"
    target_goal: str = "Conversational Fluency"
    total_sessions_completed: int = 0
    recent_average_wpm: float = 0.0
    weaknesses: list[LearnerWeakness] = Field(default_factory=list)
    recurring_weakness_tags: list[str] = Field(default_factory=list)
    recent_topics: list[str] = Field(default_factory=list)
    recent_exercise_ids: list[int] = Field(default_factory=list)
