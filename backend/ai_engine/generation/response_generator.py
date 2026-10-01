"""
Dynamic conversational response generator for AI Coach roleplays.
Uses Gemini to generate persona-faithful, context-aware dialogue replies.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from ai_engine.config import AIEngineConfig
from ai_engine.providers.gemini import GeminiProvider
from ai_engine.prompts.conversation import (
    CONVERSATION_COACH_SYSTEM_PROMPT,
    build_coach_turn_prompt
)
from ai_engine.exceptions import GenerationError, ProviderError
from apps.recordings.conversations import get_scenario

logger = logging.getLogger(__name__)

class ConversationalResponseGenerator:
    """Generates dynamic AI Coach replies based on roleplay persona, learner speech, and agent directives."""

    def __init__(self, provider: Optional[GeminiProvider] = None):
        self.provider = provider or GeminiProvider()

    def generate_reply(
        self,
        scenario_id: str,
        turn_number: int,
        user_transcript: str,
        history_turns: Optional[List[Dict[str, str]]] = None,
        is_final_turn: bool = False,
        agent_decision: Optional[Any] = None,
        assessment: Optional[Any] = None,
        analysis_result: Optional[Any] = None
    ) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Generates the next Coach conversational turn with pedagogical awareness.
        Returns: (coach_reply_text, is_concluding_turn, telemetry_dict)
        Raises GenerationError if LLM generation fails. Never returns fake static text.
        """
        scenario = get_scenario(scenario_id)
        scenario_title = scenario.get('title', 'Spoken English Conversation')
        persona = scenario.get('persona', 'English Language Coach')
        objective = scenario.get('objective', 'Practice natural conversation')

        # Check concluding turn state based on turn limits or agent decision
        follow_ups = scenario.get('follow_ups', [])
        action_name = ""
        if agent_decision:
            act = getattr(agent_decision, 'action', '')
            action_name = act.value if hasattr(act, 'value') else str(act)

        is_concluding = (
            is_final_turn or 
            (turn_number >= len(follow_ups)) or 
            (action_name == "GIVE_FEEDBACK")
        )

        if not self.provider.is_configured():
            raise GenerationError(
                "Gemini API key is not configured. Real AI Coach dialogue generation requires a valid GEMINI_API_KEY."
            )

        prompt = build_coach_turn_prompt(
            scenario_title=scenario_title,
            persona=persona,
            objective=objective,
            history_turns=history_turns or [],
            user_transcript=user_transcript,
            is_final_turn=is_concluding,
            agent_decision=agent_decision,
            assessment_context=assessment
        )

        try:
            resp = self.provider.generate_text(
                prompt=prompt,
                system_instruction=CONVERSATION_COACH_SYSTEM_PROMPT,
                model=AIEngineConfig.DIALOGUE_MODEL,
                temperature=0.7
            )
            coach_reply = resp.raw_text.strip()
            # Remove any accidental enclosing quotes or prefix labels
            if coach_reply.startswith('"') and coach_reply.endswith('"'):
                coach_reply = coach_reply[1:-1].strip()
            for prefix in ["Coach:", "Agent:", f"{persona}:"]:
                if coach_reply.lower().startswith(prefix.lower()):
                    coach_reply = coach_reply[len(prefix):].strip()

            telemetry = {
                "llm_model_version": resp.model_name,
                "latency_ms": resp.latency_ms,
                "input_tokens": resp.input_tokens,
                "output_tokens": resp.output_tokens
            }
            return coach_reply, is_concluding, telemetry

        except (ProviderError, Exception) as e:
            logger.error(f"[ConversationalResponseGenerator] Dynamic coach generation failed: {e}", exc_info=True)
            raise GenerationError(f"AI Coach reply generation failed: {e}") from e
