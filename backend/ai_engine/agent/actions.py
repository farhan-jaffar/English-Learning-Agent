"""
Adaptive Agent Action handlers.
"""

from ai_engine.schemas.agent import AgentActionType, AgentDecision

class ActionHandler:
    """Dispatches and validates agent actions."""

    @staticmethod
    def is_terminal_action(action: AgentActionType) -> bool:
        """Determines if an action concludes the current interaction."""
        return action in (AgentActionType.GIVE_FEEDBACK, AgentActionType.REMEDIATE)
