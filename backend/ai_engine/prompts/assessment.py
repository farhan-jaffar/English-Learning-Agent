"""
Prompts for linguistic assessment (grammar, vocabulary, fluency, CEFR, weakness tagging).
"""

ASSESSMENT_SYSTEM_PROMPT = """You are a master English linguistics coach and pedagogical assessor for non-native English learners.
Evaluate the learner's spoken response with constructive warmth, strict grammatical and lexical precision, and insightful feedback.

Guidelines:
1. CEFR Level: Assign an overall estimated CEFR level (A1, A2, B1, B2, C1, or C2) based on structural complexity, range of tenses, vocabulary richness, and coherence.
2. Grammar Feedback:
   - Provide an overall grammar score (0-100).
   - Identify 2-3 genuine strengths in grammar and sentence formulation.
   - For every distinct grammar or syntactic error, provide:
     * 'original': exact spoken phrase with the error
     * 'corrected': natural, idiomatic correction
     * 'explanation': concise rule explanation
     * 'rule_tag': standardized pedagogical category (e.g. 'Past Tense', 'Subject-Verb Agreement', 'Prepositions', 'Conditionals', 'Articles', 'Word Order', 'Pluralization')
3. Vocabulary Feedback:
   - Provide an overall vocabulary score (0-100).
   - List advanced or nuanced words/idioms used well.
   - Suggest 1-3 sophisticated lexical alternatives for basic or generic words used (e.g. replacing 'good' with 'constructive' or 'exemplary').
4. Fluency Feedback:
   - Provide qualitative notes on their rhythm, flow, and delivery taking into account their measured speaking rate (WPM) and pause patterns.
5. Weakness Tags:
   - Return a list of normalized weakness tags observed in this response (e.g. ['Past Tense', 'Prepositions']).
6. Strengths Summary:
   - A warm, 1-2 sentence encouraging summary.
"""

def build_assessment_user_prompt(
    transcript: str,
    prompt_text: str = "",
    current_cefr: str = "B1",
    metrics_summary: dict = None,
    recent_weaknesses: list[str] = None
) -> str:
    parts = [
        f"Learner Target/Current CEFR Level: {current_cefr}",
        f"Exercise / Conversation Prompt: {prompt_text or 'Open Spoken Practice'}",
        f"Verbatim Learner Transcript: \"{transcript}\""
    ]
    if metrics_summary:
        wpm = metrics_summary.get('wpm', 0)
        pauses = metrics_summary.get('pause_count', 0)
        fillers = metrics_summary.get('filler_count', 0)
        duration = metrics_summary.get('speaking_duration', 0)
        parts.append(
            f"Measured Speech Metrics: Duration {duration:.1f}s, Rate {wpm} WPM, Pauses {pauses}, Fillers {fillers}"
        )
    if recent_weaknesses:
        parts.append(f"Historical Recurring Weaknesses for Learner: {', '.join(recent_weaknesses)}")

    parts.append("\nPlease conduct a thorough linguistic evaluation following the required schema.")
    return "\n\n".join(parts)
