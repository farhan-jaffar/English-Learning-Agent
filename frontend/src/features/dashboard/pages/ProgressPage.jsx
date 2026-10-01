import React, { useEffect, useState } from 'react';
import { recordingsApi } from '../../../lib/api/recordings';
import { useAuthStore } from '../../../stores/authStore';
import { Spinner } from '../../../components/ui/Spinner';
import { 
  TrendingUp, 
  Clock, 
  Award, 
  Activity, 
  Globe, 
  Calendar, 
  Sparkles,
  ArrowRight,
  X,
  FileAudio,
  BarChart3,
  Target,
  ListOrdered
} from 'lucide-react';
import ProgressTrendChart from '../components/ProgressTrendChart';
import WeaknessDistributionCard from '../components/WeaknessDistributionCard';
import AnalysisFeedbackCard from '../../recordings/components/AnalysisFeedbackCard';
import './ProgressPage.css';

const WINDOWS = [
  { id: '7d', label: '7 Days' },
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
  { id: 'all', label: 'All Time' },
];

export function ProgressPage() {
  const { user, activeLanguage } = useAuthStore();
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'weaknesses' | 'history'
  const [selectedWindow, setSelectedWindow] = useState('30d');
  const [selectedLanguageCode, setSelectedLanguageCode] = useState(
    activeLanguage?.language_code || 'en-US'
  );
  const [progressData, setProgressData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Selected session for viewing detailed analysis modal
  const [inspectingRecording, setInspectingRecording] = useState(null);
  const [isLoadingInspection, setIsLoadingInspection] = useState(false);

  useEffect(() => {
    if (activeLanguage?.language_code && selectedLanguageCode !== 'all') {
      setSelectedLanguageCode(activeLanguage.language_code);
    }
  }, [activeLanguage?.language_code]);

  useEffect(() => {
    let isMounted = true;
    const fetchProgress = async () => {
      setIsLoading(true);
      try {
        const langParam = selectedLanguageCode === 'all' ? 'all' : selectedLanguageCode;
        const data = await recordingsApi.getProgress(selectedWindow, langParam);
        if (isMounted) {
          setProgressData(data);
        }
      } catch (err) {
        console.error('Failed to fetch progress metrics:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchProgress();
    return () => {
      isMounted = false;
    };
  }, [selectedWindow, selectedLanguageCode]);

  const handleInspectSession = async (recordingId) => {
    setIsLoadingInspection(true);
    try {
      const detail = await recordingsApi.getRecordingDetail(recordingId);
      setInspectingRecording(detail);
    } catch (err) {
      console.error('Failed to load recording detail:', err);
    } finally {
      setIsLoadingInspection(false);
    }
  };

  const getPaceStatus = (speed) => {
    if (speed === 0) return { label: 'No Data', className: 'pace-muted' };
    if (speed < 90) return { label: 'Deliberate', className: 'pace-warning' };
    if (speed <= 150) return { label: 'Optimal Flow', className: 'pace-optimal' };
    return { label: 'Rapid Pace', className: 'pace-warning' };
  };

  const avgWpm = progressData?.average_wpm || 0;
  const pace = getPaceStatus(avgWpm);
  const totalSessions = progressData?.total_sessions || 0;
  const currentCefr = progressData?.current_cefr || activeLanguage?.current_cefr_level || 'B1';
  const sessions = progressData?.time_series || [];

  const avgPauses = sessions.length > 0
    ? (sessions.reduce((acc, s) => acc + (s.pause_count || 0), 0) / sessions.length).toFixed(1)
    : 0;

  const enrolledLanguages = user?.user_languages || [];

  return (
    <div className="progress-clean-page">
      {/* Header & Controls Bar */}
      <header className="progress-clean-header">
        <div className="header-title-block">
          <div className="header-eyebrow">
            <TrendingUp size={14} />
            <span>Learning Analytics</span>
          </div>
          <h1 className="header-title">Speech Fluency & Progress</h1>
          <p className="header-desc">
            Monitor your speaking pace, CEFR language milestones, and targeted grammar patterns over time.
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="progress-filter-toolbar">
          <div className="lang-picker-box">
            <Globe size={15} />
            <select
              value={selectedLanguageCode}
              onChange={(e) => setSelectedLanguageCode(e.target.value)}
              className="lang-select-input"
            >
              <option value="all">All Languages</option>
              {enrolledLanguages.map((l) => (
                <option key={l.id} value={l.language_code}>
                  {l.language_name || l.language_code} ({l.current_cefr_level})
                </option>
              ))}
            </select>
          </div>

          <div className="time-window-pills">
            {WINDOWS.map((win) => (
              <button
                key={win.id}
                type="button"
                onClick={() => setSelectedWindow(win.id)}
                className={`window-pill-btn ${selectedWindow === win.id ? 'active' : ''}`}
              >
                {win.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Modern Sub-Navigation Tabs */}
      <nav className="progress-nav-tabs">
        <button
          type="button"
          className={`progress-tab-link ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <BarChart3 size={17} />
          <span>Fluency & Pace Trajectory</span>
        </button>

        <button
          type="button"
          className={`progress-tab-link ${activeTab === 'weaknesses' ? 'active' : ''}`}
          onClick={() => setActiveTab('weaknesses')}
        >
          <Target size={17} />
          <span>Weakness Breakdown ({Object.keys(progressData?.weakness_frequency || {}).length})</span>
        </button>

        <button
          type="button"
          className={`progress-tab-link ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <ListOrdered size={17} />
          <span>Practice Turn History ({sessions.length})</span>
        </button>
      </nav>

      {/* Main Body */}
      {isLoading ? (
        <div className="progress-loading-clean">
          <div className="clean-spinner-ring"></div>
          <p>Deriving speech metrics for {selectedWindow}...</p>
        </div>
      ) : (
        <div className="progress-body-clean">
          {/* TAB 1: OVERVIEW & FLOW */}
          {activeTab === 'overview' && (
            <div className="tab-pane-fade">
              {/* 4 Minimalist KPI Cards */}
              <div className="kpi-scorecards-row">
                <div className="kpi-card">
                  <div className="kpi-card-head">
                    <span className="kpi-title">Current Level</span>
                    <Award size={18} className="kpi-icon-accent" />
                  </div>
                  <div className="kpi-main-metric">
                    <span className="kpi-number">{currentCefr}</span>
                  </div>
                  <span className="kpi-footnote">Active CEFR standard</span>
                </div>

                <div className="kpi-card">
                  <div className="kpi-card-head">
                    <span className="kpi-title">Average Pace</span>
                    <Activity size={18} className="kpi-icon-accent" />
                  </div>
                  <div className="kpi-main-metric">
                    <span className="kpi-number">{avgWpm}</span>
                    <span className="kpi-unit">WPM</span>
                    <span className={`pace-pill ${pace.className}`}>{pace.label}</span>
                  </div>
                  <span className="kpi-footnote">Ideal conversational flow: 110–150 WPM</span>
                </div>

                <div className="kpi-card">
                  <div className="kpi-card-head">
                    <span className="kpi-title">Cadence Smoothness</span>
                    <Clock size={18} className="kpi-icon-accent" />
                  </div>
                  <div className="kpi-main-metric">
                    <span className="kpi-number">{avgPauses}</span>
                    <span className="kpi-unit">pauses/turn</span>
                  </div>
                  <span className="kpi-footnote">Average pauses per speaking session</span>
                </div>

                <div className="kpi-card">
                  <div className="kpi-card-head">
                    <span className="kpi-title">Sessions Evaluated</span>
                    <FileAudio size={18} className="kpi-icon-accent" />
                  </div>
                  <div className="kpi-main-metric">
                    <span className="kpi-number">{totalSessions}</span>
                    <span className="kpi-unit">turns</span>
                  </div>
                  <span className="kpi-footnote">Recorded across {selectedWindow}</span>
                </div>
              </div>

              {/* Full-width Responsive Trendline Chart */}
              <div className="chart-full-wrapper">
                <ProgressTrendChart data={sessions} />
              </div>
            </div>
          )}

          {/* TAB 2: WEAKNESS INSIGHTS */}
          {activeTab === 'weaknesses' && (
            <div className="tab-pane-fade weaknesses-tab-view">
              <div className="weakness-intro-box">
                <div>
                  <h3 className="intro-title">Pedagogical Weakness Distribution</h3>
                  <p className="intro-desc">
                    These frequency metrics track repetitive grammatical obstacles and phonetic patterns
                    identified during your speech evaluations.
                  </p>
                </div>
              </div>

              <div className="weakness-card-spacious">
                <WeaknessDistributionCard weaknessFrequency={progressData?.weakness_frequency} />
              </div>

              <div className="weakness-recommendations-box">
                <div className="rec-icon">💡</div>
                <div className="rec-text">
                  <h4>Targeted Practice Recommendation</h4>
                  <p>
                    {Object.keys(progressData?.weakness_frequency || {}).length > 0
                      ? `Focus your next speaking session on "${Object.keys(progressData.weakness_frequency)[0]}". Practicing with the AI Coach in conversational roleplays will help you self-correct in real time.`
                      : 'You have no unresolved grammar tags recorded! Try exploring advanced roleplay dialogues in the AI Partner catalog.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: PRACTICE TURN HISTORY */}
          {activeTab === 'history' && (
            <div className="tab-pane-fade history-tab-view">
              {sessions.length === 0 ? (
                <div className="history-empty-state">
                  <Calendar size={36} className="empty-icon" />
                  <h3>No practice sessions in this timeframe</h3>
                  <p>Choose a different time window above or start a practice session to see historical evaluations.</p>
                </div>
              ) : (
                <div className="history-clean-table-card">
                  <table className="clean-sessions-table">
                    <thead>
                      <tr>
                        <th>Date & Time</th>
                        <th>Exercise / Turn</th>
                        <th>Assessed Level</th>
                        <th>Pace (WPM)</th>
                        <th>Pauses & Fillers</th>
                        <th style={{ textAlign: 'right' }}>Evaluation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessions.map((sess) => (
                        <tr key={sess.id}>
                          <td className="cell-timestamp">{sess.date}</td>
                          <td className="cell-exercise-name">
                            <strong>{sess.exercise_title}</strong>
                          </td>
                          <td>
                            <span className="cefr-badge-pill">{sess.cefr_estimate || 'B1'}</span>
                          </td>
                          <td className="cell-wpm">
                            <span className="wpm-val">{sess.wpm || '—'}</span>
                            {sess.wpm && <span className="wpm-lbl"> wpm</span>}
                          </td>
                          <td className="cell-pauses">
                            <span>{sess.pause_count ?? 0} pauses</span>
                            {sess.filler_count > 0 && (
                              <span className="filler-note">({sess.filler_count} fillers)</span>
                            )}
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              type="button"
                              className="inspect-report-btn"
                              onClick={() => handleInspectSession(sess.recording_id)}
                              disabled={isLoadingInspection}
                            >
                              <span>View Report</span>
                              <ArrowRight size={14} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Inspect Session Analysis Modal */}
      {inspectingRecording && (
        <div className="analysis-inspect-backdrop" onClick={() => setInspectingRecording(null)}>
          <div className="analysis-inspect-modal" onClick={(e) => e.stopPropagation()}>
            <div className="inspect-modal-header">
              <div>
                <span className="inspect-sub">Historical Speech Assessment</span>
                <h2 className="inspect-title">{inspectingRecording.exercise_title || 'Speaking Turn'}</h2>
              </div>
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setInspectingRecording(null)}
              >
                <X size={20} />
              </button>
            </div>

            <div className="inspect-modal-body">
              {inspectingRecording.audio_file && (
                <div className="inspect-audio-row">
                  <span className="audio-lbl">Audio Recording:</span>
                  <audio
                    controls
                    src={
                      inspectingRecording.audio_file.startsWith('http')
                        ? inspectingRecording.audio_file
                        : `${(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/api\/?$/, '')}${inspectingRecording.audio_file}`
                    }
                    className="inspect-audio-player"
                  />
                </div>
              )}

              <AnalysisFeedbackCard
                analysis={inspectingRecording.analysis}
                transcript={inspectingRecording.turn?.text_content || ''}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
