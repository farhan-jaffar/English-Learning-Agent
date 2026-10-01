import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recordingsApi } from '../../../lib/api/recordings';
import { AudioPromptPlayer } from '../../../components/audio/AudioPromptPlayer';
import './ConversationsPage.css';

const DEFAULT_SCENARIOS = [
  {
    id: 'job_interview',
    title: 'Software Developer Job Interview',
    persona: 'Sarah Jensen — VP of Engineering',
    difficulty: 'B2',
    category: 'Career & Professional',
    objective: 'Practice behavioral questions using the STAR method with clear technical vocabulary.',
    opening_message:
      'Hello and welcome! Thank you for taking the time to speak with me today. To begin our conversation, could you briefly introduce yourself and tell me about a recent technical project you worked on?',
    icon: '💼',
    themeColor: '#ffe566',
  },
  {
    id: 'coffee_shop',
    title: 'Ordering at a Bustling Urban Café',
    persona: 'Leo — Friendly Barista',
    difficulty: 'A2',
    category: 'Daily Life & Service',
    objective: 'Practice ordering drinks, requesting customized snacks, and handling payment interactions.',
    opening_message:
      'Good morning! Welcome to Roasters & Co. The espresso grinder is warmed up and ready. What can I get started for you today?',
    icon: '☕',
    themeColor: '#d6d58b',
  },
  {
    id: 'airport_travel',
    title: 'Airport Check-In & Border Customs',
    persona: 'Officer Williams — Border Control Agent',
    difficulty: 'B1',
    category: 'Travel & Hospitality',
    objective: 'Practice explaining your itinerary, accommodation, and customs declarations clearly and politely.',
    opening_message:
      'Next in line, please! Good afternoon. May I please see your passport, boarding pass, and customs declaration form?',
    icon: '✈️',
    themeColor: '#ffff66',
  },
  {
    id: 'tech_debate',
    title: 'Ethics of Artificial Intelligence Debate',
    persona: 'Dr. Finch — Oxford Philosophy Fellow',
    difficulty: 'C1',
    category: 'Academic & Debate',
    objective: 'Formulate and defend nuanced arguments regarding algorithmic accountability and intellectual property.',
    opening_message:
      'Welcome to our colloquium. Today we are critically examining autonomous generative systems. Who should bear accountability when an AI agent outputs harmful misinformation?',
    icon: '⚖️',
    themeColor: '#b3b347',
  },
];

export function ConversationsPage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState(DEFAULT_SCENARIOS);
  const [sessions, setSessions] = useState([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [startingScenarioId, setStartingScenarioId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoadingSessions(true);
    setError(null);
    try {
      const [backendScenarios, pastSessions] = await Promise.all([
        recordingsApi.getScenarios().catch(() => DEFAULT_SCENARIOS),
        recordingsApi.getConversationSessions().catch(() => []),
      ]);

      if (backendScenarios && backendScenarios.length > 0) {
        // Merge backend scenarios with rich icons and themes
        const merged = backendScenarios.map((sc) => {
          const fallback = DEFAULT_SCENARIOS.find((d) => d.id === sc.id) || {};
          return { ...fallback, ...sc };
        });
        setScenarios(merged);
      }
      setSessions(pastSessions || []);
    } catch (err) {
      console.error('Failed to load conversation scenarios:', err);
      setError('Unable to load conversational sessions. Please refresh or try again.');
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const handleStartSession = async (scenarioId) => {
    if (isStartingSession) return;
    setIsStartingSession(true);
    setStartingScenarioId(scenarioId);
    setError(null);

    try {
      const newSession = await recordingsApi.startConversationSession(scenarioId);
      navigate(`/conversations/${newSession.id}`);
    } catch (err) {
      console.error('Failed to start session:', err);
      setError(err?.response?.data?.detail || 'Could not start conversation session.');
      setIsStartingSession(false);
      setStartingScenarioId(null);
    }
  };

  return (
    <div className="conversations-page-container">
      {/* Hero Header */}
      <header className="conversations-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-pulse"></span>
            AI Interactive Partner Mode
          </div>
          <h1 className="hero-title">Practice Fluent Dialogue with AI Personas</h1>
          <p className="hero-subtitle">
            Engage in multi-turn spoken roleplays. Your AI partner speaks out loud, listens to your
            accent and grammar, and responds dynamically in real time.
          </p>
        </div>
      </header>

      {error && <div className="conversations-error-banner">{error}</div>}

      {/* Scenario Catalog Grid */}
      <section className="scenarios-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Select a Conversation Scenario</h2>
            <p className="section-desc">Choose a real-world setting to test your spontaneous speaking skills.</p>
          </div>
        </div>

        <div className="scenarios-grid">
          {scenarios.map((sc) => {
            const isStarting = isStartingSession && startingScenarioId === sc.id;
            return (
              <div key={sc.id} className="scenario-card" style={{ '--accent-tint': sc.themeColor || '#ffe566' }}>
                <div className="scenario-card-top">
                  <div className="scenario-icon-box">{sc.icon || '💬'}</div>
                  <div className="scenario-meta">
                    <span className={`difficulty-tag cefr-${sc.difficulty.toLowerCase()}`}>{sc.difficulty}</span>
                    <span className="category-label">{sc.category}</span>

                  </div>
                </div>

                <h3 className="scenario-title">{sc.title}</h3>
                <p className="scenario-persona">
                  <strong>Partner:</strong> {sc.persona}
                </p>
                <p className="scenario-objective">{sc.objective}</p>

                <div className="scenario-preview-box">
                  <span className="preview-label">Opening Prompt:</span>
                  <p className="preview-text">"{sc.opening_message}"</p>
                  <div className="preview-listen-wrap">
                    <AudioPromptPlayer text={sc.opening_message} label="Listen to Opening" size="sm" />
                  </div>
                </div>

                <div className="scenario-card-actions">
                  <button
                    type="button"
                    className="start-scenario-btn"
                    onClick={() => handleStartSession(sc.id)}
                    disabled={isStartingSession}
                  >
                    {isStarting ? (
                      <>
                        <span className="spinner-sm"></span> Initializing Coach...
                      </>
                    ) : (
                      <>
                        <span>Start Conversation</span>
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <line x1="5" y1="12" x2="19" y2="12"></line>
                          <polyline points="12 5 19 12 12 19"></polyline>
                        </svg>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Past & Active Conversations Section */}
      <section className="past-sessions-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Your Dialogue History</h2>
            <p className="section-desc">Review previous roleplays, turn transcripts, and feedback.</p>
          </div>
        </div>

        {isLoadingSessions ? (
          <div className="sessions-loading-state">
            <div className="pulse-loader"></div>
            <p>Loading your past sessions...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="sessions-empty-state">
            <div className="empty-icon">🎙️</div>
            <h3>No conversations started yet</h3>
            <p>Choose any scenario above to practice your first multi-turn roleplay conversation!</p>
          </div>
        ) : (
          <div className="sessions-list-grid">
            {sessions.map((sess) => {
              const turnCount = sess.turns?.length || sess.turn_counter || 0;
              const dateStr = new Date(sess.created_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              });

              return (
                <div key={sess.id} className="session-history-card">
                  <div className="session-history-main">
                    <div className="session-status-row">
                      <span className={`session-status-badge ${sess.is_active ? 'active' : 'concluded'}`}>
                        {sess.is_active ? '● Active Session' : '✓ Concluded'}
                      </span>
                      <span className="session-date-stamp">{dateStr}</span>
                    </div>
                    <h4 className="session-history-title">{sess.session_title}</h4>
                    <p className="session-history-stats">
                      <span>{turnCount} dialogue turns</span>
                      {sess.conversation_summary && (
                        <span className="summary-snippet">• {sess.conversation_summary}</span>
                      )}
                    </p>
                  </div>
                  <div className="session-history-action">
                    <button
                      type="button"
                      className={`session-cta-btn ${sess.is_active ? 'resume-btn' : 'review-btn'}`}
                      onClick={() => navigate(`/conversations/${sess.id}`)}
                    >
                      {sess.is_active ? 'Resume Practice →' : 'Review Transcript'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
