"""
Prompts for adaptive exercise generation.
"""

EXERCISE_GENERATOR_SYSTEM_PROMPT = """You are an expert English curriculum designer creating high-yield spoken practice exercises.
Your goal is to generate engaging, contextual speaking prompts tailored to the learner's target CEFR level, target skill, and specific pedagogical weakness.

Requirements:
1. 'title': Engaging 3-6 word title.
2. 'prompt_text': Clear, conversational instructions telling the learner what scenario to imagine, what to discuss, and what specific grammatical structures or vocabulary to use.
3. 'skill_focus': One of 'grammar', 'vocabulary', 'fluency', or 'pronunciation'.
4. 'cefr_level': The target CEFR level (A1 to C2).
5. 'vocabulary_hints': 3-5 high-value words/phrases to encourage the learner to use.
6. 'topic': General thematic category (e.g. Travel, Career, Daily Life, Science & Tech).
7. 'min_duration_seconds': 20-30 seconds.
8. 'max_duration_seconds': 60-120 seconds.
"""

def build_exercise_generation_prompt(
    cefr_level: str,
    skill_focus: str,
    target_weakness: str = "",
    preferred_topic: str = "",
    avoid_recent_titles: list[str] = None
) -> str:
    parts = [
        f"Target CEFR Level: {cefr_level}",
        f"Primary Skill Focus: {skill_focus}",
    ]
    if target_weakness:
        parts.append(f"Specific Weakness to Remediate: {target_weakness}")
    if preferred_topic:
        parts.append(f"Preferred Context/Topic: {preferred_topic}")
    if avoid_recent_titles:
        parts.append(f"Do not duplicate or closely mimic these recent exercises: {', '.join(avoid_recent_titles)}")
    
    parts.append("Generate a brand new spoken exercise following the JSON schema.")
    return "\n".join(parts)
