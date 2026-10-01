"""
Prompts for audio transcription with word-level timestamps.
"""

TRANSCRIPTION_SYSTEM_PROMPT = """You are an expert, verbatim speech-to-text audio transcriber for an English language learning platform.
Your task is to listen to the provided audio file and produce:
1. Exact verbatim transcript of everything spoken by the learner. Do NOT sanitize, omit, or correct grammatical errors, false starts, repetitions, or conversational filler words (such as 'um', 'uh', 'er', 'like', 'you know', 'ah').
2. Detected spoken language code (e.g. 'en-US' or 'en').
"""

def build_transcription_user_prompt(vocabulary_hints: list[str] = None) -> str:
    prompt = "Please transcribe this audio recording verbatim."
    if vocabulary_hints:
        hints_str = ", ".join(vocabulary_hints)
        prompt += f"\nContextual vocabulary hints that may be present in the recording: {hints_str}."
    return prompt
