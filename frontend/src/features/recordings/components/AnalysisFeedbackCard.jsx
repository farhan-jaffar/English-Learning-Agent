import React from 'react';
import { 
  Award, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  BookOpen, 
  Sparkles, 
  ArrowRight, 
  Clock, 
  Mic2,
  Tag
} from 'lucide-react';
import Badge from '../../../components/ui/Badge';
import Button from '../../../components/ui/Button';
import './AnalysisFeedbackCard.css';

/**
 * AI Linguistic Feedback Card displaying CEFR score, fluency metrics,
 * grammar corrections, vocabulary depth, and pedagogical weakness tags.
 * 
 * @param {Object} analysis - The AnalysisResult object from backend
 * @param {string} transcript - Speech-to-text transcript if available
 * @param {function} onNext - Optional callback to move to next exercise
 * @param {function} onRetry - Optional callback to retry current exercise
 */
export default function AnalysisFeedbackCard({ 
  analysis, 
  transcript = '', 
  onNext, 
  onRetry 
}) {
  if (!analysis) {
    return (
      <div className="analysis-empty-state">
        <Sparkles size={32} className="empty-icon" />
        <p>No analysis details available for this recording.</p>
      </div>
    );
  }

  const {
    estimated_cefr = 'B1',
    fluency_metrics = {},
    grammar_feedback = {},
    vocabulary_feedback = {},
    weakness_tags = [],
  } = analysis;

  const wpm = fluency_metrics.wpm || 0;
  const pauseCount = fluency_metrics.pause_count || 0;
  const avgPauseMs = fluency_metrics.avg_pause_ms || 0;
  const fillerCount = fluency_metrics.filler_count || 0;
  const adjustment = fluency_metrics.adjustment || fluency_metrics.promotion;
  const promotion = adjustment;

  const grammarScore = grammar_feedback.overall_score || 80;
  const grammarStrengths = grammar_feedback.strengths || [];
  const grammarCorrections = grammar_feedback.corrections || [];

  const vocabScore = vocabulary_feedback.overall_score || 80;
  const advancedWords = vocabulary_feedback.advanced_words_used || [];
  const vocabSuggestions = vocabulary_feedback.suggestions || [];

  const getPaceStatus = (speed) => {
    if (speed < 90) return { label: 'Deliberate', variant: 'warning' };
    if (speed <= 150) return { label: 'Optimal Flow', variant: 'success' };
    return { label: 'Fast Pace', variant: 'warning' };
  };

  const pace = getPaceStatus(wpm);

  return (
    <div className="analysis-feedback-card">
      {/* CEFR Level Up Banner */}
      {adjustment?.promoted && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.5)',
          borderRadius: '12px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 14px rgba(16, 185, 129, 0.15)'
        }}>
          <div style={{ fontSize: '32px', lineHeight: 1 }}>🎉</div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{
                background: '#10B981',
                color: '#fff',
                fontSize: '11px',
                fontWeight: '700',
                padding: '2px 8px',
                borderRadius: '4px',
                letterSpacing: '0.5px'
              }}>
                CEFR LEVEL UP
              </span>
              <span style={{ fontWeight: '700', color: '#10B981', fontSize: '15px' }}>
                Promoted to {adjustment.new_level_name || adjustment.new_level}!
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '13px', color: '#E5E7EB', lineHeight: '1.4' }}>
              {adjustment.reason}
            </p>
          </div>
        </div>
      )}

      {/* CEFR Level Recalibration Banner */}
      {adjustment?.demoted && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%)',
          border: '1px solid rgba(245, 158, 11, 0.4)',
          borderRadius: '12px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 14px rgba(245, 158, 11, 0.1)'
        }}>
          <div style={{ fontSize: '32px', lineHeight: 1 }}>🎯</div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{
                background: '#F59E0B',
                color: '#111827',
                fontSize: '11px',
                fontWeight: '700',
                padding: '2px 8px',
                borderRadius: '4px',
                letterSpacing: '0.5px'
              }}>
                LEVEL CALIBRATED
              </span>
              <span style={{ fontWeight: '700', color: '#F59E0B', fontSize: '15px' }}>
                Pacing adjusted to {adjustment.new_level_name || adjustment.new_level}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '13px', color: '#E5E7EB', lineHeight: '1.4' }}>
              {adjustment.reason}
            </p>
          </div>
        </div>
      )}

      {/* Top Banner: CEFR & Overall Evaluation */}
      <div className="analysis-hero-banner">
        <div className="cefr-badge-large">
          <span className="cefr-title">Assessed Level</span>
          <span className="cefr-val">{estimated_cefr}</span>
          {adjustment?.level_confidence && (
            <span style={{ fontSize: '11px', color: '#9CA3AF', marginTop: '4px', fontWeight: '500' }}>
              {adjustment.level_confidence}% confidence
            </span>
          )}
        </div>

        <div className="analysis-hero-text">
          <div className="hero-title-row">
            <h3>AI Speech Evaluation</h3>
            <Badge variant="lemon">Active Result</Badge>
          </div>
          <p className="hero-description">
            Your spoken response demonstrated good sentence coherence and steady flow. Review the specific metrics and recommendations below to continue refining your natural speaking rhythm.
          </p>
        </div>
      </div>

      {/* Transcript callout if available */}
      {transcript && (
        <div className="transcript-box">
          <div className="transcript-header">
            <Mic2 size={16} />
            <span>Transcribed Speech</span>
          </div>
          <p className="transcript-text">"{transcript}"</p>
        </div>
      )}

      {/* Fluency Metrics Grid */}
      <div className="section-title">
        <Activity size={18} />
        <h4>Fluency & Cadence Metrics</h4>
      </div>

      <div className="fluency-metrics-grid">
        <div className="fluency-metric-card">
          <span className="metric-label">Speaking Pace</span>
          <div className="metric-val-row">
            <span className="metric-value">{wpm}</span>
            <span className="metric-unit">WPM</span>
          </div>
          <Badge variant={pace.variant} className="metric-status-badge">
            {pace.label}
          </Badge>
          <span className="metric-subtext">Target: 110–150 words/min</span>
        </div>

        <div className="fluency-metric-card">
          <span className="metric-label">Natural Pauses</span>
          <div className="metric-val-row">
            <span className="metric-value">{pauseCount}</span>
            <span className="metric-unit">pauses</span>
          </div>
          <span className="metric-detail">Avg {avgPauseMs} ms</span>
          <span className="metric-subtext">Controlled pause cadence</span>
        </div>

        <div className="fluency-metric-card">
          <span className="metric-label">Filler Words</span>
          <div className="metric-val-row">
            <span className="metric-value">{fillerCount}</span>
            <span className="metric-unit">detected</span>
          </div>
          <Badge variant={fillerCount <= 2 ? 'success' : 'warning'} className="metric-status-badge">
            {fillerCount <= 2 ? 'Low Hesitation' : 'Moderate Hesitation'}
          </Badge>
          <span className="metric-subtext">um, uh, like</span>
        </div>

        <div className="fluency-metric-card">
          <span className="metric-label">Grammar Accuracy</span>
          <div className="metric-val-row">
            <span className="metric-value">{grammarScore}%</span>
          </div>
          <Badge variant={grammarScore >= 80 ? 'success' : 'muted'} className="metric-status-badge">
            {grammarScore >= 80 ? 'High Accuracy' : 'In Progress'}
          </Badge>
          <span className="metric-subtext">Structural score</span>
        </div>
      </div>

      {/* Grammar Breakdown */}
      <div className="feedback-section">
        <div className="section-title">
          <CheckCircle2 size={18} />
          <h4>Grammar Analysis & Refinements ({grammarScore}%)</h4>
        </div>

        {/* Strengths */}
        {grammarStrengths.length > 0 && (
          <div className="feedback-strengths-box">
            <span className="strengths-title">What went well:</span>
            <ul className="strengths-list">
              {grammarStrengths.map((str, idx) => (
                <li key={idx}>
                  <CheckCircle2 size={15} className="strength-icon" />
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Corrections */}
        {grammarCorrections.length > 0 ? (
          <div className="corrections-container">
            <span className="corrections-heading">Suggested Corrections:</span>
            {grammarCorrections.map((corr, idx) => (
              <div key={idx} className="correction-card">
                <div className="correction-diff">
                  <div className="diff-row original">
                    <span className="diff-tag">Spoken:</span>
                    <span className="diff-text original-text">{corr.original}</span>
                  </div>
                  <div className="diff-row corrected">
                    <span className="diff-tag">Recommended:</span>
                    <span className="diff-text corrected-text">{corr.corrected}</span>
                  </div>
                </div>
                {corr.explanation && (
                  <p className="correction-explanation">{corr.explanation}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="no-errors-note">No grammatical errors detected. Excellent syntactic command!</p>
        )}
      </div>

      {/* Vocabulary Breakdown */}
      <div className="feedback-section">
        <div className="section-title">
          <BookOpen size={18} />
          <h4>Vocabulary Sophistication ({vocabScore}%)</h4>
        </div>

        {/* Advanced Words Detected */}
        {advancedWords.length > 0 && (
          <div className="advanced-words-box">
            <span className="vocab-subheading">Advanced Words Employed:</span>
            <div className="chips-row">
              {advancedWords.map((word, idx) => (
                <span key={idx} className="advanced-word-chip">
                  ✨ {word}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {vocabSuggestions.length > 0 && (
          <div className="vocab-suggestions-list">
            <span className="vocab-subheading">Word Enhancements:</span>
            {vocabSuggestions.map((sug, idx) => (
              <div key={idx} className="vocab-suggestion-item">
                <div className="vocab-swap">
                  <span className="base-word">"{sug.word}"</span>
                  <ArrowRight size={14} className="swap-arrow" />
                  <div className="alt-chips">
                    {sug.alternatives?.map((alt, aIdx) => (
                      <Badge key={aIdx} variant="lemon" size="sm">
                        {alt}
                      </Badge>
                    ))}
                  </div>
                </div>
                {sug.context && (
                  <p className="vocab-context">{sug.context}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pedagogical Weakness Tags */}
      {weakness_tags.length > 0 && (
        <div className="feedback-section weakness-section">
          <div className="section-title">
            <Tag size={18} />
            <h4>Target Areas For Next Session</h4>
          </div>
          <div className="chips-row">
            {weakness_tags.map((tag, idx) => (
              <Badge key={idx} variant="muted" className="weakness-tag-chip">
                {typeof tag === 'string' ? tag : tag.name}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Modal Actions */}
      <div className="analysis-card-actions">
        {onRetry && (
          <Button variant="secondary" size="md" onClick={onRetry}>
            Try This Exercise Again
          </Button>
        )}
        {onNext && (
          <Button variant="olive" size="md" onClick={onNext}>
            <span>Continue to Next Exercise</span>
            <ArrowRight size={16} />
          </Button>
        )}
      </div>
    </div>
  );
}
