import React, { useEffect, useState, useMemo } from 'react';
import { recordingsApi } from '../../../lib/api/recordings';
import { Spinner } from '../../../components/ui/Spinner';
import Button from '../../../components/ui/Button';
import { 
  Mic, 
  Search, 
  FileAudio, 
  ChevronDown, 
  ChevronUp,
  Volume2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Filter,
  Layers,
  Award,
  BookOpen,
  HelpCircle
} from 'lucide-react';
import './RecordingsPage.css';

const STATUS_CONFIG = {
  uploaded: { label: 'Uploaded', className: 'status-uploaded' },
  processing: { label: 'Analyzing...', className: 'status-processing' },
  analyzed: { label: 'Evaluated', className: 'status-analyzed' },
  failed: { label: 'Failed', className: 'status-failed' },
};

const CEFR_FILTERS = ['ALL', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export function RecordingsPage() {
  const [recordings, setRecordings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [activeTabMap, setActiveTabMap] = useState({}); // { [recordingId]: 'audio' | 'feedback' }
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCefr, setSelectedCefr] = useState('ALL');

  const fetchRecordings = async () => {
    setIsLoading(true);
    try {
      const data = await recordingsApi.getRecordings();
      setRecordings(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Failed to fetch recordings:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordings();
  }, []);

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
    if (!activeTabMap[id]) {
      setActiveTabMap((prev) => ({ ...prev, [id]: 'audio' }));
    }
  };

  const setCardTab = (recordingId, tab) => {
    setActiveTabMap((prev) => ({ ...prev, [recordingId]: tab }));
  };

  // Filtered recordings
  const filteredRecordings = useMemo(() => {
    return recordings.filter((rec) => {
      const title = (rec.exercise_title || `Turn #${rec.turn_sequence || rec.id}`).toLowerCase();
      const matchesSearch = !searchQuery || title.includes(searchQuery.toLowerCase());
      
      const cefr = rec.analysis?.estimated_cefr || '';
      const matchesCefr = selectedCefr === 'ALL' || cefr.toUpperCase() === selectedCefr;

      return matchesSearch && matchesCefr;
    });
  }, [recordings, searchQuery, selectedCefr]);

  return (
    <div className="recordings-clean-page">
      {/* Header Bar */}
      <header className="recordings-clean-header">
        <div className="header-text-group">
          <div className="header-eyebrow">
            <Mic size={14} />
            <span>Voice Library</span>
          </div>
          <h1 className="header-main-title">Speech Recordings & Evaluation</h1>
          <p className="header-sub-desc">
            Listen back to your speech submissions, review AI pronunciation cadence, and inspect grammar corrections.
          </p>
        </div>
        <button 
          type="button" 
          className="refresh-pill-btn" 
          onClick={fetchRecordings} 
          disabled={isLoading}
        >
          {isLoading ? <Spinner size="sm" /> : '↻ Refresh List'}
        </button>
      </header>

      {/* Filter & Search Bar */}
      <div className="recordings-filter-dock">
        <div className="search-box-wrap">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search exercises or sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="clean-search-input"
          />
          {searchQuery && (
            <button 
              type="button" 
              className="clear-search-btn"
              onClick={() => setSearchQuery('')}
            >
              ✕
            </button>
          )}
        </div>

        <div className="cefr-filter-chips">
          <span className="filter-label">Level:</span>
          {CEFR_FILTERS.map((lvl) => (
            <button
              key={lvl}
              type="button"
              className={`cefr-filter-chip ${selectedCefr === lvl ? 'active' : ''}`}
              onClick={() => setSelectedCefr(lvl)}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <div className="recordings-loading-clean">
          <div className="clean-spinner-ring"></div>
          <p>Loading your speech recordings...</p>
        </div>
      ) : filteredRecordings.length === 0 ? (
        <div className="recordings-empty-clean">
          <div className="empty-icon-circle">
            <FileAudio size={32} />
          </div>
          <h3>No recordings found</h3>
          <p>
            {searchQuery || selectedCefr !== 'ALL'
              ? 'Try clearing your filters or search terms to see more recordings.'
              : 'Complete a practice exercise or AI roleplay session to populate your voice library.'}
          </p>
        </div>
      ) : (
        <div className="recordings-cards-flow">
          {filteredRecordings.map((rec) => {
            const isExpanded = expandedId === rec.id;
            const currentTab = activeTabMap[rec.id] || 'audio';
            const statusKey = (rec.status || 'uploaded').toLowerCase();
            const statusInfo = STATUS_CONFIG[statusKey] || { label: rec.status, className: 'status-uploaded' };
            const analysis = rec.analysis;
            const wpm = analysis?.fluency_metrics?.wpm;
            const cefr = analysis?.estimated_cefr;
            const accuracy = analysis?.grammar_feedback?.overall_score;
            const dateFormatted = new Date(rec.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });
            const timeFormatted = new Date(rec.created_at).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            });

            return (
              <div 
                key={rec.id} 
                className={`clean-recording-card ${isExpanded ? 'card-expanded' : ''}`}
              >
                {/* Header Summary Row */}
                <div 
                  className="card-summary-header"
                  onClick={() => toggleExpand(rec.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && toggleExpand(rec.id)}
                >
                  <div className="summary-left-block">
                    <div className="clean-mic-icon">
                      <Mic size={18} />
                    </div>
                    <div>
                      <h3 className="exercise-name">
                        {rec.exercise_title || `Practice Turn #${rec.turn_sequence || rec.id}`}
                      </h3>
                      <div className="exercise-date-row">
                        <span>{dateFormatted} at {timeFormatted}</span>
                        <span className="dot-sep">•</span>
                        <span>{rec.duration_seconds ? `${Math.round(rec.duration_seconds)}s` : 'Voice note'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="summary-right-block">
                    {cefr && (
                      <span className="clean-cefr-badge">{cefr}</span>
                    )}
                    {wpm && (
                      <span className="clean-metric-badge">
                        <strong>{wpm}</strong> WPM
                      </span>
                    )}
                    {accuracy && (
                      <span className="clean-metric-badge accuracy">
                        <strong>{accuracy}%</strong>
                      </span>
                    )}
                    <span className={`clean-status-pill ${statusInfo.className}`}>
                      {statusInfo.label}
                    </span>
                    <button 
                      type="button" 
                      className="expand-indicator-btn"
                      aria-label={isExpanded ? 'Collapse' : 'Expand'}
                    >
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </button>
                  </div>
                </div>

                {/* Expanded Modular Inspection Panel */}
                {isExpanded && (
                  <div className="card-expanded-body">
                    {/* Sub-Tabs Bar */}
                    <div className="expanded-subtabs-nav">
                      <button
                        type="button"
                        className={`subtab-btn ${currentTab === 'audio' ? 'active' : ''}`}
                        onClick={() => setCardTab(rec.id, 'audio')}
                      >
                        <Volume2 size={15} />
                        <span>Spoken Audio & Pace</span>
                      </button>

                      <button
                        type="button"
                        className={`subtab-btn ${currentTab === 'feedback' ? 'active' : ''}`}
                        onClick={() => setCardTab(rec.id, 'feedback')}
                      >
                        <Sparkles size={15} />
                        <span>Linguistic Feedback & Corrections</span>
                      </button>
                    </div>

                    {/* Tab 1: Audio & Transcript */}
                    {currentTab === 'audio' && (
                      <div className="subtab-content audio-tab-pane">
                        {rec.audio_file ? (
                          <div className="audio-player-deck">
                            <div className="audio-player-meta">
                              <span className="deck-label">Audio Recording</span>
                              <span className="audio-duration-tag">
                                {rec.duration_seconds ? `${Math.round(rec.duration_seconds)} seconds` : 'Speech snippet'}
                              </span>
                            </div>
                            <audio 
                              controls 
                              src={
                                rec.audio_file.startsWith('http') 
                                  ? rec.audio_file 
                                  : `${(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/api\/?$/, '')}${rec.audio_file}`
                              } 
                              className="clean-audio-player" 
                            />
                          </div>
                        ) : (
                          <div className="no-audio-state">No audio file stored for this turn.</div>
                        )}

                        {/* Speech Transcript */}
                        <div className="clean-transcript-card">
                          <span className="deck-label">Speech Transcript</span>
                          <p className="clean-transcript-text">
                            "{rec.turn?.text_content || 'Voice recording processed by the linguistic evaluation pipeline.'}"
                          </p>
                        </div>

                        {/* Fluency Metrics Row */}
                        {analysis?.fluency_metrics && (
                          <div className="fluency-metrics-clean-grid">
                            <div className="mini-stat-card">
                              <span className="stat-label">Speech Rate</span>
                              <span className="stat-value">{analysis.fluency_metrics.wpm || '—'} <small>WPM</small></span>
                            </div>
                            <div className="mini-stat-card">
                              <span className="stat-label">Pause Pauses</span>
                              <span className="stat-value">{analysis.fluency_metrics.pause_count ?? '0'} <small>pauses</small></span>
                            </div>
                            <div className="mini-stat-card">
                              <span className="stat-label">Avg Pause Time</span>
                              <span className="stat-value">{analysis.fluency_metrics.avg_pause_ms ?? '420'} <small>ms</small></span>
                            </div>
                            <div className="mini-stat-card">
                              <span className="stat-label">Filler Words</span>
                              <span className="stat-value">{analysis.fluency_metrics.filler_count ?? '0'} <small>fillers</small></span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Tab 2: Linguistic Feedback */}
                    {currentTab === 'feedback' && (
                      <div className="subtab-content feedback-tab-pane">
                        {analysis ? (
                          <div className="feedback-two-columns">
                            {/* Column 1: Grammar */}
                            <div className="feedback-column">
                              <div className="column-header">
                                <h4>Grammar & Sentence Structure</h4>
                                {analysis.grammar_feedback?.overall_score && (
                                  <span className="score-tag">{analysis.grammar_feedback.overall_score}% Score</span>
                                )}
                              </div>

                              {analysis.grammar_feedback?.strengths?.length > 0 && (
                                <div className="feedback-group strengths-group">
                                  <span className="group-title">Key Strengths</span>
                                  <ul>
                                    {analysis.grammar_feedback.strengths.map((s, idx) => (
                                      <li key={idx}>{s}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {analysis.grammar_feedback?.corrections?.length > 0 ? (
                                <div className="feedback-group corrections-group">
                                  <span className="group-title">Recommended Refinements</span>
                                  {analysis.grammar_feedback.corrections.map((corr, idx) => (
                                    <div key={idx} className="correction-clean-item">
                                      <div className="corr-line orig">
                                        <span className="type-badge">Original:</span> {corr.original}
                                      </div>
                                      <div className="corr-line fix">
                                        <span className="type-badge">Suggested:</span> {corr.corrected}
                                      </div>
                                      {corr.explanation && (
                                        <p className="corr-why">{corr.explanation}</p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="no-errors-clean">
                                  <CheckCircle2 size={16} />
                                  <span>No grammar errors identified in this speech segment.</span>
                                </div>
                              )}
                            </div>

                            {/* Column 2: Vocabulary & Weaknesses */}
                            <div className="feedback-column">
                              <div className="column-header">
                                <h4>Vocabulary & Weakness Tags</h4>
                                {analysis.vocabulary_feedback?.overall_score && (
                                  <span className="score-tag">{analysis.vocabulary_feedback.overall_score}% Score</span>
                                )}
                              </div>

                              {analysis.vocabulary_feedback?.advanced_words_used?.length > 0 && (
                                <div className="feedback-group">
                                  <span className="group-title">Advanced Vocabulary Used</span>
                                  <div className="vocab-pills-wrap">
                                    {analysis.vocabulary_feedback.advanced_words_used.map((word, idx) => (
                                      <span key={idx} className="vocab-clean-pill">{word}</span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {analysis.vocabulary_feedback?.suggestions?.length > 0 && (
                                <div className="feedback-group">
                                  <span className="group-title">Word Upgrades</span>
                                  <div className="upgrades-stack">
                                    {analysis.vocabulary_feedback.suggestions.map((sug, idx) => (
                                      <div key={idx} className="upgrade-clean-box">
                                        <span>Replace "<strong>{sug.word}</strong>" with </span>
                                        <span className="upgrade-options">{sug.alternatives?.join(', ')}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {analysis.weakness_tags?.length > 0 && (
                                <div className="feedback-group">
                                  <span className="group-title">Flagged Grammar Weaknesses</span>
                                  <div className="weakness-pills-wrap">
                                    {analysis.weakness_tags.map((tag, idx) => (
                                      <span key={idx} className="weakness-clean-pill">
                                        {typeof tag === 'string' ? tag : tag.name}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="no-feedback-state">
                            {statusKey === 'processing' ? (
                              <div className="processing-indicator">
                                <Spinner size="md" />
                                <span>Evaluating speech audio...</span>
                              </div>
                            ) : (
                              <p>No linguistic feedback generated yet for this recording.</p>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
