"""
Prompts for multi-turn roleplay conversation and follow-up generation.
"""

from typing import Optional, Any, List, Dict

CONVERSATION_COACH_SYSTEM_PROMPT = """You are an interactive AI English Coach roleplaying in a focused simulation.
Your role is to stay in-character, listen attentively to the learner's spoken input, and provide an engaging, natural response that advances the dialogue while eliciting spoken English practice.

Rules:
1. Stay strictly in your assigned persona (e.g. Hiring Manager, Barista, Customs Agent, Debate Partner).
2. Keep responses concise (2-4 sentences max) so the learner does most of the speaking.
3. If the learner made a confusing or incomplete statement, gently ask for clarification in-character.
4. If this is a concluding turn (e.g. final turn in the scenario), bring the conversation to a natural, positive close and compliment their communication.
5. Do NOT break character into an academic grading lecture during the roleplay; stay authentic to the scenario while seamlessly implementing pedagogical coaching directives.
"""

def build_coach_turn_prompt(
    scenario_title: str,
    persona: str,
    objective: str,
    history_turns: List[Dict[str, str]],
    user_transcript: str,
    is_final_turn: bool = False,
    agent_decision: Optional[Any] = None,
    assessment_context: Optional[Any] = None
) -> str:
    history_text = "\n".join([
        f"{turn.get('role', 'speaker').capitalize()}: {turn.get('text', '')}"
        for turn in history_turns[-6:]  # Keep last 6 turns for context
    ])

    pedagogical_guidance = ""
    if agent_decision or assessment_context:
        guidance_lines = [
            "\n## Pedagogical Context (Internal Coaching Directive — Do NOT quote or lecture on these rules directly)"
        ]

        if agent_decision:
            action = getattr(agent_decision, 'action', None)
            if hasattr(action, 'value'):
                action_str = str(action.value)
            elif action:
                action_str = str(action)
            elif isinstance(agent_decision, dict):
                action_str = str(agent_decision.get('action', 'CONTINUE'))
            else:
                action_str = "CONTINUE"

            reason = getattr(agent_decision, 'reason', '') or (agent_decision.get('reason', '') if isinstance(agent_decision, dict) else '')
            target_weakness = getattr(agent_decision, 'target_weakness', '') or (agent_decision.get('target_weakness', '') if isinstance(agent_decision, dict) else '')

            guidance_lines.append(f"Strategic Action Directive: {action_str}")
            if reason:
                guidance_lines.append(f"Action Justification: {reason}")
            if target_weakness:
                guidance_lines.append(f"Target Linguistic Weakness: {target_weakness}")

            if action_str == "ASK_FOLLOW_UP":
                guidance_lines.append(
                    "- Coaching Instruction: Formulate an in-character question that naturally encourages the learner to use or practice the target structure."
                )
            elif action_str == "REMEDIATE":
                guidance_lines.append(
                    "- Coaching Instruction: The learner encountered difficulties. Subtly model the proper phrasing in your natural reply, then ask a clarifying question to help them express their thought."
                )
            elif action_str == "INCREASE_DIFFICULTY":
                guidance_lines.append(
                    "- Coaching Instruction: The learner performed with high accuracy. Elevate your vocabulary and ask a more complex, open-ended question to challenge them."
                )
            elif action_str == "GIVE_FEEDBACK":
                guidance_lines.append(
                    "- Coaching Instruction: Wrap up the conversation with warm, encouraging in-character praise highlighting their communication ability."
                )
            elif action_str == "CONTINUE":
                guidance_lines.append(
                    "- Coaching Instruction: Advance the conversation smoothly and authentically."
                )

        if assessment_context:
            grammar_score = getattr(getattr(assessment_context, 'grammar_feedback', None), 'overall_score', None)
            if grammar_score is None and isinstance(assessment_context, dict):
                grammar_score = assessment_context.get('grammar_feedback', {}).get('overall_score')

            corrections = getattr(getattr(assessment_context, 'grammar_feedback', None), 'corrections', [])
            if not corrections and isinstance(assessment_context, dict):
                corrections = assessment_context.get('grammar_feedback', {}).get('corrections', [])

            weaknesses = getattr(assessment_context, 'weaknesses', []) or (assessment_context.get('weaknesses', []) if isinstance(assessment_context, dict) else [])

            if grammar_score is not None:
                guidance_lines.append(f"Current Turn Grammar Score: {grammar_score}/100")
            if corrections:
                corr_examples = []
                for c in corrections[:2]:
                    orig = getattr(c, 'original', '') or (c.get('original', '') if isinstance(c, dict) else '')
                    corr = getattr(c, 'corrected', '') or (c.get('corrected', '') if isinstance(c, dict) else '')
                    if orig and corr:
                        corr_examples.append(f"'{orig}' -> '{corr}'")
                if corr_examples:
                    guidance_lines.append(f"Recent Spoken Errors: {'; '.join(corr_examples)}")
            if weaknesses:
                guidance_lines.append(f"Identified Weakness Focus Areas: {', '.join(str(w) for w in weaknesses)}")

        pedagogical_guidance = "\n".join(guidance_lines) + "\n"

    return f"""Scenario: {scenario_title}
Persona: {persona}
Objective: {objective}

Recent Conversation History:
{history_text}

Latest Spoken User Reply:
User: "{user_transcript}"
{pedagogical_guidance}
Is Concluding Turn: {"Yes, please wrap up the conversation warmly" if is_final_turn else "No, keep the conversation going"}

Generate the next in-character coach reply. Output only the spoken dialogue text.
"""
