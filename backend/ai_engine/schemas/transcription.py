"""
Transcription and word timestamp schemas.
"""

from pydantic import BaseModel, Field

class WordTimestamp(BaseModel):
    """Timestamped word offset in spoken response."""
    word: str = Field(..., description="Spoken word or token")
    start: float = Field(..., description="Start offset in seconds from audio onset")
    end: float = Field(..., description="End offset in seconds")

class TranscriptResult(BaseModel):
    """Complete verbatim transcription with word-level chronological timestamps."""
    transcript: str = Field(..., description="Verbatim raw text of speech including filler words")
    words: list[WordTimestamp] = Field(default_factory=list, description="Chronological sequence of spoken words with timestamps")
    detected_language: str = Field(default="en", description="Detected language code (e.g. en, en-US)")
