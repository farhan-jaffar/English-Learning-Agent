"""
Adaptive Agent Orchestrator.
Main entry point coordinating learner state, policy evaluation, and generative actions.
"""

import logging
from typing import Optional
from apps.authentication.models import User
from apps.exercises.models import Exercise
from ai_engine.learner.state import LearnerStateBuilder
from ai_engine.schemas.assessment import LinguisticAssessment
from ai_engine.schemas.agent import AgentActionType, AgentDecision
from ai_engine.generation.exercise_generator import AdaptiveExerciseGenerator
from .policy import HybridAgentPolicy

logger = logging.getLogger(__name__)

class AdaptiveAgentOrchestrator:
    """Orchestrates learner intelligence, hybrid policy decisions, and remediation actions."""

    def __init__(self, exercise_generator: Optional[AdaptiveExerciseGenerator] = None):
        self.exercise_generator = exercise_generator or AdaptiveExerciseGenerator()

    def decide_next_step(
        self,
        user: User,
        assessment: Optional[LinguisticAssessment] = None,
        language_code: Optional[str] = None,
        interaction_type: str = "conversation",
        current_turn: int = 1,
        max_turns: int = 4
    ) -> AgentDecision:
        """
        Synthesizes learner state, evaluates policy constraints, and returns next action.
        """
        learner_state = LearnerStateBuilder.build(user, language_code)

        decision = HybridAgentPolicy.evaluate(
            learner_state=learner_state,
            assessment=assessment,
            interaction_type=interaction_type,
            current_turn=current_turn,
            max_turns=max_turns
        )

        return decision

    def generate_remediation_exercise(
        self,
        user: User,
        decision: AgentDecision,
        language_code: Optional[str] = None
    ) -> Exercise:
        """
        Executes a REMEDIATE decision by generating and saving a tailored practice exercise.
        """
        learner_state = LearnerStateBuilder.build(user, language_code)
        user_lang = user.user_languages.filter(language__code=learner_state.target_language).first()
        target_lang = user_lang.language if user_lang else None

        exercise = self.exercise_generator.generate_and_save(
            language=target_lang,
            cefr_level=decision.difficulty or learner_state.current_cefr,
            skill_focus=decision.target_skill or "grammar",
            target_weakness=decision.target_weakness,
            preferred_topic="Targeted Practice",
            avoid_recent_titles=[]
        )
        return exercise
