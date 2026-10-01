import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { recordingsApi } from '../../../lib/api/recordings';
import { useAudioRecorder } from '../../../hooks/useAudioRecorder';
import { useSpeechSynthesis } from '../../../hooks/useSpeechSynthesis';
import { AudioPromptPlayer } from '../../../components/audio/AudioPromptPlayer';
import AudioVisualizer from '../../../components/audio/AudioVisualizer';
import './ConversationRoomPage.css';

export function ConversationRoomPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmittingTurn, setIsSubmittingTurn] = useState(false);
  const [expandedFeedbackId, setExpandedFeedbackId] = useState(null);
  const [error, setError] = useState(null);
  const [autoSpeakNewTurns, setAutoSpeakNewTurns] = useState(true);

  const dialogueEndRef = useRef(null);
  const prevTurnsCountRef = useRef(0);

  const recorder = useAudioRecorder();
  const { speak, stop: stopSpeech, isSpeaking } = useSpeechSynthesis();

  // Load session detail
  useEffect(() => {
    loadSessionDetail();
  }, [sessionId]);

  const loadSessionDetail = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await recordingsApi.getConversationSessionDetail(sessionId);
      setSession(data);

      // Expand feedback of latest user turn by default
      const userTurns = (data.turns || []).filter((t) => t.role === 'user');
      if (userTurns.length > 0) {
        setExpandedFeedbackId(userTurns[userTurns.length - 1].id);
      }

      // If initial load and only turn 1 (Coach opening) exists, auto-speak it if enabled
      if (data.turns?.length === 1 && data.turns[0].role === 'agent' && autoSpeakNewTurns) {
        setTimeout(() => {
          speak(data.turns[0].text_content);
        }, 500);
      }
    } catch (err) {
      console.error('Failed to load session details:', err);
      setError('Could not load this conversation session.');
    } finally {
      setIsLoading(false);
    }
  };

  // Scroll to bottom when turns update
  useEffect(() => {
    if (session?.turns) {
      const currentCount = session.turns.length;
      if (currentCount > prevTurnsCountRef.current) {
        dialogueEndRef.current?.scrollIntoView({ behavior: 'smooth' });

        // If a new agent turn arrived, speak it if autoSpeak is on
        if (prevTurnsCountRef.current > 0 && autoSpeakNewTurns) {
          const latestTurn = session.turns[currentCount - 1];
          if (latestTurn && latestTurn.role === 'agent') {
            speak(latestTurn.text_content);
          }
        }
      }
      prevTurnsCountRef.current = currentCount;
    }
  }, [session?.turns, autoSpeakNewTurns, speak]);

  // Clean up speech on unmount
  useEffect(() => {
    return () => {
      stopSpeech();
    };
  }, [stopSpeech]);

  const handleSendTurnReply = async () => {
    if (!recorder.audioBlob || isSubmittingTurn) return;

    setIsSubmittingTurn(true);
    setError(null);
    stopSpeech();

    try {
      const updatedSession = await recordingsApi.sendConversationTurnReply(
        sessionId,
        recorder.audioBlob,
        recorder.recordingTime
      );

      setSession(updatedSession);
      recorder.resetRecording();

      // Automatically expand newest user turn analysis
      const userTurns = (updatedSession.turns || []).filter((t) => t.role === 'user');
      if (userTurns.length > 0) {
        setExpandedFeedbackId(userTurns[userTurns.length - 1].id);
      }
    } catch (err) {
      console.error('Failed to submit turn reply:', err);
      setError(err?.response?.data?.detail || 'Failed to submit speech reply. Please try again.');
    } finally {
      setIsSubmittingTurn(false);
    }
  };

  const handleConcludeSession = async () => {
    if (!window.confirm('Are you ready to conclude this conversation session?')) return;
    try {
      const updatedSession = await recordingsApi.concludeConversationSession(sessionId);
      setSession(updatedSession);
      stopSpeech();
    } catch (err) {
      console.error('Failed to conclude session:', err);
      setError('Failed to conclude session.');
    }
  };

  const toggleFeedback = (turnId) => {
    setExpandedFeedbackId((prev) => (prev === turnId ? null : turnId));
  };

  if (isLoading) {
    return (
      <div className="conversation-room-loading">
        <div className="pulse-loader"></div>
        <h2>Setting up your roleplay room...</h2>
        <p>Connecting with AI Coach partner</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="conversation-room-error">
        <h2>Session Not Found</h2>
        <p>{error || 'The requested conversation session could not be loaded.'}</p>
        <button type="button" className="room-back-btn" onClick={() => navigate('/conversations')}>
          ← Return to Scenarios
        </button>
      </div>
    );
  }

  const turns = session.turns || [];
  const userTurnCount = turns.filter((t) => t.role === 'user').length;
  const isFreeChatSession = Boolean(session?.session_title?.toLowerCase().includes('free'));

  return (
    <div className="conversation-room-container">
      {/* Room Header */}
      <header className="room-header">
        <div className="room-header-left">
          <button
            type="button"
            className="room-back-icon-btn"
            onClick={() => navigate('/conversations')}
            title="Back to Scenarios"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
          </button>
          <div>
            <div className="room-title-row">
              <h1 className="room-session-title">{session.session_title}</h1>
              <span className={`room-live-pill ${session.is_active ? 'active' : 'concluded'}`}>
                {session.is_active ? (
                  <>
                    <span className="live-dot"></span>
                    Live Dialogue
                  </>
                ) : (
                  '✓ Concluded'
                )}
              </span>
            </div>
            <p className="room-meta-sub">
              <span>{userTurnCount} spoken replies completed</span>
              <span className="meta-sep">•</span>
              <span>Language: {session.language_code || 'en-US'}</span>
            </p>
          </div>
        </div>

        <div className="room-header-right">
          <label className="auto-speech-toggle" title="Automatically speak coach responses out loud">
            <input
              type="checkbox"
              checked={autoSpeakNewTurns}
              onChange={(e) => setAutoSpeakNewTurns(e.target.checked)}
            />
            <span>Auto-Voice Coach</span>
          </label>

          {session.is_active && (
            <button
              type="button"
              className="conclude-session-btn"
              onClick={handleConcludeSession}
              title="End conversation and save summary"
            >
              Conclude Dialogue
            </button>
          )}
        </div>
      </header>

      {error && <div className="room-alert-banner">{error}</div>}

      {/* Main Dialogue Timeline Feed */}
      <main className="room-dialogue-feed">
        {turns.map((turn, index) => {
          const isAgent = turn.role === 'agent';
          const isUser = turn.role === 'user';
          const analysis = turn.analysis;

          if (isAgent) {
            return (
              <div key={turn.id || index} className="dialogue-turn agent-turn">
                <div className="turn-avatar agent-avatar">🤖</div>
                <div className="turn-bubble-wrapper">
                  <div className="turn-bubble-header">
                    <span className="turn-speaker-name">AI English Coach</span>
                    <span className="turn-seq-badge">Turn #{turn.turn_sequence}</span>
                  </div>
                  <div className="agent-bubble-card">
                    <p className="turn-message-text">{turn.text_content}</p>
                    <div className="agent-bubble-footer">
                      <AudioPromptPlayer
                        text={turn.text_content}
                        label="Listen to Coach"
                        size="sm"
                        showRateToggle={true}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          }

          if (isUser) {
            const hasAnalysis = Boolean(analysis);
            const isFeedbackOpen = isFreeChatSession ? hasAnalysis : expandedFeedbackId === turn.id;

            return (
              <div key={turn.id || index} className="dialogue-turn user-turn">
                <div className="turn-bubble-wrapper">
                  <div className="turn-bubble-header user-header">
                    <span className="turn-seq-badge user-seq">Your Turn #{turn.turn_sequence}</span>
                    <span className="turn-speaker-name">You (Learner)</span>
                  </div>

                  <div className="user-bubble-card">
                    {/* User Voice Audio Player */}
                    {turn.audio_url && (
                      <div className="user-audio-wrap">
                        <audio controls src={turn.audio_url} className="custom-audio-elem" preload="metadata" />
                      </div>
                    )}

                    <p className="turn-message-text user-transcript">
                      "{turn.text_content || 'Voice reply submitted'}"
                    </p>

                    {/* Quick Metrics Bar */}
                    {hasAnalysis && (
                      <div className="user-turn-metrics-row">
                        <span className="metric-chip cefr-chip">
                          CEFR: <strong>{analysis.estimated_cefr || 'B1'}</strong>
                        </span>
                        {analysis.fluency_metrics?.wpm && (
                          <span className="metric-chip wpm-chip">
                            ⚡ {analysis.fluency_metrics.wpm} WPM
                          </span>
                        )}
                        <button
                          type="button"
                          className="toggle-feedback-btn"
                          onClick={() => toggleFeedback(turn.id)}
                        >
                          {isFeedbackOpen ? 'Hide Linguistic Feedback ▲' : 'View Linguistic Feedback ▼'}
                        </button>
                      </div>
                    )}

                    {/* Collapsible Analysis Feedback Panel */}
                    {hasAnalysis && isFeedbackOpen && (
                      <div className="inline-feedback-drawer">
                        {/* Grammar Feedback */}
                        {analysis.grammar_feedback && (
                          <div className="feedback-sub-section">
                            <h5 className="sub-section-title">
                              <span>✍️ Grammar Evaluation</span>
                              <span className="score-pill">
                                {analysis.grammar_feedback.overall_score || 85}%
                              </span>
                            </h5>
                            {analysis.grammar_feedback.strengths?.length > 0 && (
                              <div className="feedback-block strengths">
                                <h6>Strengths:</h6>
                                <ul>
                                  {analysis.grammar_feedback.strengths.map((st, i) => (
                                    <li key={i}>{st}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {analysis.grammar_feedback.corrections?.length > 0 && (
                              <div className="feedback-block corrections">
                                <h6>Suggested Refinements:</h6>
                                {analysis.grammar_feedback.corrections.map((corr, i) => (
                                  <div key={i} className="correction-item">
                                    <div className="corr-orig">
                                      <span className="corr-tag">Original:</span> {corr.original}
                                    </div>
                                    <div className="corr-better">
                                      <span className="corr-tag">Recommended:</span> {corr.corrected}
                                    </div>
                                    {corr.explanation && (
                                      <p className="corr-expl">{corr.explanation}</p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Vocabulary Feedback */}
                        {analysis.vocabulary_feedback && (
                          <div className="feedback-sub-section">
                            <h5 className="sub-section-title">
                              <span>📚 Vocabulary & Diction</span>
                              <span className="score-pill">
                                {analysis.vocabulary_feedback.overall_score || 82}%
                              </span>
                            </h5>
                            {analysis.vocabulary_feedback.advanced_words_used?.length > 0 && (
                              <div className="vocab-tags-row">
                                <span className="vocab-row-label">Advanced Words:</span>
                                {analysis.vocabulary_feedback.advanced_words_used.map((w, i) => (
                                  <span key={i} className="vocab-tag">
                                    {w}
                                  </span>
                                ))}
                              </div>
                            )}
                            {analysis.vocabulary_feedback.suggestions?.length > 0 && (
                              <div className="vocab-upgrade-list">
                                {analysis.vocabulary_feedback.suggestions.map((sug, i) => (
                                  <div key={i} className="upgrade-item">
                                    Replace "<strong>{sug.word}</strong>" with{' '}
                                    <span className="alternatives-chips">
                                      {sug.alternatives?.join(', ')}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <div className="turn-avatar user-avatar">👤</div>
              </div>
            );
          }

          return null;
        })}

        {/* Submitting Speech Spinner Indicator */}
        {isSubmittingTurn && (
          <div className="dialogue-turn agent-turn agent-thinking">
            <div className="turn-avatar agent-avatar pulse-avatar">🤖</div>
            <div className="thinking-bubble">
              <span className="dot dot-1"></span>
              <span className="dot dot-2"></span>
              <span className="dot dot-3"></span>
              <span className="thinking-label">AI Coach is analyzing speech and formulating reply...</span>
            </div>
          </div>
        )}

        {/* Anchor to scroll */}
        <div ref={dialogueEndRef} />
      </main>

      {/* Bottom Action / Recording Dock */}
      <footer className="room-action-dock">
        {session.is_active ? (
          <div className="recorder-interactive-dock">
            {recorder.state === 'inactive' && (
              <div className="dock-prompt-bar">
                <div className="dock-hint">
                  <strong>Your Turn to Speak:</strong> Click the microphone to record your conversational response.
                </div>
                <button
                  type="button"
                  className="start-mic-btn"
                  onClick={recorder.startRecording}
                  disabled={isSubmittingTurn}
                >
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                  </svg>
                  <span>Start Speaking</span>
                </button>
              </div>
            )}

            {recorder.state === 'recording' && (
              <div className="dock-recording-active">
                <div className="recording-status-pill">
                  <span className="rec-red-pulse"></span>
                  Recording: {recorder.recordingTime}s
                </div>
                <div className="dock-visualizer-wrap">
                  <AudioVisualizer audioLevels={recorder.audioLevels} isRecording={true} />
                </div>
                <div className="dock-rec-buttons">
                  <button type="button" className="btn-rec-control pause" onClick={recorder.pauseRecording}>
                    Pause
                  </button>
                  <button type="button" className="btn-rec-control stop" onClick={recorder.stopRecording}>
                    Finish & Review
                  </button>
                </div>
              </div>
            )}

            {recorder.state === 'paused' && (
              <div className="dock-recording-active">
                <div className="recording-status-pill paused">Paused at {recorder.recordingTime}s</div>
                <div className="dock-rec-buttons">
                  <button type="button" className="btn-rec-control resume" onClick={recorder.resumeRecording}>
                    Resume Speaking
                  </button>
                  <button type="button" className="btn-rec-control stop" onClick={recorder.stopRecording}>
                    Finish & Review
                  </button>
                </div>
              </div>
            )}

            {recorder.state === 'recorded' && (
              <div className="dock-review-bar">
                <div className="dock-audio-preview">
                  <audio controls src={recorder.audioUrl} className="preview-player" />
                  <span className="duration-tag">{recorder.recordingTime}s recorded</span>
                </div>
                <div className="dock-reply-actions">
                  <button
                    type="button"
                    className="btn-retry-record"
                    onClick={recorder.resetRecording}
                    disabled={isSubmittingTurn}
                  >
                    Re-record
                  </button>
                  <button
                    type="button"
                    className="btn-submit-turn"
                    onClick={handleSendTurnReply}
                    disabled={isSubmittingTurn}
                  >
                    {isSubmittingTurn ? (
                      <>
                        <span className="spinner-sm"></span> Sending...
                      </>
                    ) : (
                      <>
                        <span>Send Response to Coach</span>
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <line x1="22" y1="2" x2="11" y2="13"></line>
                          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="dock-concluded-summary">
            <div className="concluded-check">🎉</div>
            <div className="concluded-info">
              <h4>Conversation Concluded</h4>
              <p>
                {session.conversation_summary ||
                  `Completed ${userTurnCount} conversational turns with your AI partner.`}
              </p>
            </div>
            <button
              type="button"
              className="return-scenarios-btn"
              onClick={() => navigate('/conversations')}
            >
              Back to All Scenarios
            </button>
          </div>
        )}
      </footer>
    </div>
  );
}
