"""
Linguistic assessment and feedback schemas matching frontend UI contracts.
"""

from typing import Literal
from pydantic import BaseModel, Field

class GrammarCorrection(BaseModel):
    """Specific grammatical correction with pedagogical rule explanation."""
    original: str = Field(..., description="Learner's exact spoken phrase with grammar issue")
    corrected: str = Field(..., description="Natural, grammatically accurate replacement phrase")
    explanation: str = Field(..., description="Concise rule explanation for the learner")
    rule_tag: str = Field(default="", description="Pedagogical category e.g. 'Past Tense', 'Subject-Verb Agreement', 'Prepositions'")

class GrammarFeedback(BaseModel):
    """Grammar proficiency evaluation and actionable feedback."""
    overall_score: int = Field(..., ge=0, le=100, description="Overall grammar accuracy score 0-100")
    strengths: list[str] = Field(default_factory=list, description="Observed strengths in grammar and syntax")
    corrections: list[GrammarCorrection] = Field(default_factory=list, description="List of specific corrections")

class VocabSuggestion(BaseModel):
    """Lexical enhancement suggestion for overused or generic vocabulary."""
    word: str = Field(..., description="Word or phrase used by learner that can be elevated")
    alternatives: list[str] = Field(default_factory=list, description="Sophisticated alternatives")
    context: str = Field(..., description="Brief pedagogical guidance on how/when to use the alternatives")

class VocabularyFeedback(BaseModel):
    """Vocabulary richness and lexical range evaluation."""
    overall_score: int = Field(..., ge=0, le=100, description="Overall vocabulary score 0-100")
    advanced_words_used: list[str] = Field(default_factory=list, description="Sophisticated words successfully used")
    suggestions: list[VocabSuggestion] = Field(default_factory=list, description="Lexical improvement suggestions")

class LinguisticAssessment(BaseModel):
    """Holistic linguistic evaluation schema matching backend AnalysisResult and frontend UI."""
    estimated_cefr: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = Field(
        ...,
        description="Assessed CEFR level based on grammar complexity, lexical resource, and coherence"
    )
    grammar_feedback: GrammarFeedback = Field(..., description="Grammar feedback block")
    vocabulary_feedback: VocabularyFeedback = Field(..., description="Vocabulary feedback block")
    fluency_feedback: str = Field(default="", description="Qualitative evaluation of cadence and pacing")
    weaknesses: list[str] = Field(
        default_factory=list,
        description="List of specific weakness tags identified, e.g. ['Past Tense', 'Articles', 'Prepositions']"
    )
    strengths_summary: str = Field(
        default="",
        description="Warm, encouraging summary highlighting key learner accomplishments"
    )
