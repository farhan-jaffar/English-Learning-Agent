"""
Adaptive Agent action and decision contracts.
"""

from enum import Enum
from pydantic import BaseModel, Field

class AgentActionType(str, Enum):
    """Possible pedagogical actions decided by the hybrid policy."""
    CONTINUE = "CONTINUE"
    GIVE_FEEDBACK = "GIVE_FEEDBACK"
    ASK_FOLLOW_UP = "ASK_FOLLOW_UP"
    REMEDIATE = "REMEDIATE"
    GENERATE_EXERCISE = "GENERATE_EXERCISE"
    INCREASE_DIFFICULTY = "INCREASE_DIFFICULTY"

class AgentDecision(BaseModel):
    """Structured decision output from the Adaptive Agent."""
    action: AgentActionType = Field(..., description="Action decided by agent policy")
    target_skill: str = Field(default="mixed", description="Pedagogical skill targeted (grammar, vocabulary, fluency, pronunciation)")
    target_weakness: str = Field(default="", description="Target weakness name if remediating or probing")
    difficulty: str = Field(default="B1", description="Suggested CEFR level for next step")
    reason: str = Field(..., description="Linguistic and pedagogical justification for this action")
    suggested_coach_reply: str = Field(
        default="",
        description="Optional conversational reply or follow-up prompt for the learner"
    )
