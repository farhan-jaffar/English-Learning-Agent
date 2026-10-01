"""
Deterministic speech metrics calculation in pure Python.
Calculates WPM, pauses, filler words, and speaking duration without LLM arithmetic.
"""

import re
from typing import List, Dict, Any, Optional
from ai_engine.config import AIEngineConfig
from ai_engine.schemas.transcription import WordTimestamp, TranscriptResult

class SpeechMetricsCalculator:
    """Computes exact, reproducible speech metrics from transcript and word timestamps."""

    def __init__(
        self,
        pause_threshold_sec: float = AIEngineConfig.PAUSE_THRESHOLD_SECONDS,
        filler_words: frozenset = AIEngineConfig.COMMON_FILLERS
    ):
        self.pause_threshold_sec = pause_threshold_sec
        self.filler_words = filler_words

    def calculate(
        self,
        transcript_result: TranscriptResult,
        audio_duration_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates all fluency metrics.
        Returns a dict matching backend AnalysisResult.fluency_metrics and frontend UI contracts:
        {
            "wpm": int,
            "pause_count": int,
            "avg_pause_ms": int,
            "longest_pause_ms": int,
            "filler_count": int,
            "word_count": int,
            "speaking_duration": float
        }
        """
        words: List[WordTimestamp] = transcript_result.words or []
        transcript_text: str = transcript_result.transcript or ""

        # Calculate speaking duration
        if audio_duration_seconds and audio_duration_seconds > 0:
            duration = float(audio_duration_seconds)
        elif words:
            duration = max(words[-1].end - words[0].start, 1.0)
        else:
            duration = 15.0  # default fallback

        word_count = len(words) if words else len(transcript_text.split())

        # WPM calculation: (word_count / duration_seconds) * 60
        if duration > 0 and word_count > 0:
            raw_wpm = (word_count / duration) * 60.0
            wpm = int(max(30, min(250, round(raw_wpm))))
        else:
            wpm = 0

        # Pause analysis: gaps between adjacent words exceeding threshold
        pauses_ms: List[int] = []
        for i in range(len(words) - 1):
            curr_end = words[i].end
            next_start = words[i + 1].start
            gap_sec = next_start - curr_end
            if gap_sec >= self.pause_threshold_sec:
                pauses_ms.append(int(gap_sec * 1000))

        pause_count = len(pauses_ms)
        avg_pause_ms = int(sum(pauses_ms) / pause_count) if pause_count > 0 else 0
        longest_pause_ms = max(pauses_ms) if pause_count > 0 else 0

        # Filler word analysis
        filler_count = self._count_fillers(words, transcript_text)

        return {
            "wpm": wpm,
            "pause_count": pause_count,
            "avg_pause_ms": avg_pause_ms,
            "longest_pause_ms": longest_pause_ms,
            "filler_count": filler_count,
            "word_count": word_count,
            "speaking_duration": round(duration, 2)
        }

    def _count_fillers(self, words: List[WordTimestamp], text: str) -> int:
        """Counts occurrences of known filler expressions."""
        count = 0
        clean_text = text.lower()

        # Check multi-word fillers (e.g. "you know", "i mean", "sort of", "kind of")
        multi_word_fillers = ["you know", "i mean", "sort of", "kind of"]
        for mw in multi_word_fillers:
            count += len(re.findall(r'\b' + re.escape(mw) + r'\b', clean_text))

        # Check single word tokens
        if words:
            for w in words:
                token = re.sub(r'[^\w]', '', w.word.lower())
                if token in self.filler_words and token not in {"you", "know", "i", "mean", "sort", "kind"}:
                    count += 1
        else:
            single_tokens = re.findall(r'\b[a-z]+\b', clean_text)
            for token in single_tokens:
                if token in self.filler_words and token not in {"you", "know", "i", "mean", "sort", "kind"}:
                    count += 1

        return count
