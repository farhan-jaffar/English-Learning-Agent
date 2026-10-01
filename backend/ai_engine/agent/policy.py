"""
Hybrid Agent Policy balancing deterministic pedagogical rules with LLM reasoning.
"""

from typing import Optional
from ai_engine.config import AIEngineConfig
from ai_engine.schemas.assessment import LinguisticAssessment
from ai_engine.schemas.learner import LearnerState
from ai_engine.schemas.agent import AgentActionType, AgentDecision

class HybridAgentPolicy:
    """Enforces deterministic constraints, CEFR boundaries, and weakness persistence rules."""

    @staticmethod
    def evaluate(
        learner_state: LearnerState,
        assessment: Optional[LinguisticAssessment] = None,
        interaction_type: str = "conversation",
        current_turn: int = 1,
        max_turns: int = 4
    ) -> AgentDecision:
        """
        Evaluates the learner's state and recent assessment to determine the next pedagogical action.
        """
        # Rule 1: Conversation completion boundary
        if interaction_type == "conversation" and current_turn >= max_turns:
            return AgentDecision(
                action=AgentActionType.GIVE_FEEDBACK,
                target_skill="mixed",
                difficulty=learner_state.current_cefr,
                reason="Conversation roleplay scenario reached maximum turn limit."
            )

        # Rule 2: Persistence-based Remediation Trigger
        # If any weakness in current assessment matches a verified recurring weakness
        recurring_active_weaknesses = []
        if assessment and assessment.weaknesses:
            for w in assessment.weaknesses:
                for lw in learner_state.weaknesses:
                    if lw.tag.lower() == w.lower() and lw.is_recurring:
                        recurring_active_weaknesses.append(lw.tag)

        if recurring_active_weaknesses:
            target_tag = recurring_active_weaknesses[0]
            return AgentDecision(
                action=AgentActionType.REMEDIATE,
                target_skill="grammar",
                target_weakness=target_tag,
                difficulty=learner_state.current_cefr,
                reason=f"Persistent recurring weakness '{target_tag}' re-occurred in this session."
            )

        # Rule 3: Single-instance error in conversation -> Probe with Follow-up
        if interaction_type == "conversation" and assessment and assessment.weaknesses:
            new_weakness = assessment.weaknesses[0]
            return AgentDecision(
                action=AgentActionType.ASK_FOLLOW_UP,
                target_skill="grammar",
                target_weakness=new_weakness,
                difficulty=learner_state.current_cefr,
                reason=f"Observed '{new_weakness}' for the first time; probing to confirm if it is a persistent pattern."
            )

        # Rule 4: High performance -> Increase difficulty
        if assessment and assessment.grammar_feedback.overall_score >= 92 and assessment.vocabulary_feedback.overall_score >= 90:
            next_level = HybridAgentPolicy._get_next_cefr(learner_state.current_cefr)
            return AgentDecision(
                action=AgentActionType.INCREASE_DIFFICULTY,
                target_skill="mixed",
                difficulty=next_level,
                reason=f"Outstanding mastery at {learner_state.current_cefr}; recommending stretch to {next_level}."
            )

        # Default action
        return AgentDecision(
            action=AgentActionType.CONTINUE,
            target_skill="mixed",
            difficulty=learner_state.current_cefr,
            reason="Dialogue within normal parameters; continuing progression."
        )

    @staticmethod
    def _get_next_cefr(current: str) -> str:
        levels = AIEngineConfig.CEFR_LEVELS
        try:
            idx = levels.index(current)
            if idx + 1 < len(levels):
                return levels[idx + 1]
        except ValueError:
            pass
        return current
