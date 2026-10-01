import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../../stores/authStore';
import { useUiStore } from '../../../stores/uiStore';
import { authApi } from '../../../lib/api/auth';
import { Spinner } from '../../../components/ui/Spinner';
import { AudioPromptPlayer } from '../../../components/audio/AudioPromptPlayer';
import { 
  Globe, 
  Check, 
  Star, 
  Shield, 
  User, 
  Edit3, 
  Trash2, 
  Plus, 
  AlertCircle, 
  X, 
  Clock, 
  PlayCircle,
  Save,
  Volume2,
  Sliders
} from 'lucide-react';
import './SettingsPage.css';

const AVAILABLE_LANGUAGES = [
  { code: 'en-US', name: 'English (US)', flag: '🇺🇸' },
  { code: 'es-ES', name: 'Spanish (Spain)', flag: '🇪🇸' },
  { code: 'fr-FR', name: 'French (France)', flag: '🇫🇷' },
  { code: 'de-DE', name: 'German (Germany)', flag: '🇩🇪' },
  { code: 'it-IT', name: 'Italian (Italy)', flag: '🇮🇹' },
  { code: 'pt-BR', name: 'Portuguese (Brazil)', flag: '🇧🇷' },
  { code: 'ja-JP', name: 'Japanese (Japan)', flag: '🇯🇵' },
  { code: 'zh-CN', name: 'Chinese (Simplified)', flag: '🇨🇳' },
];

const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

const GOAL_PRESETS = [
  'General Fluency',
  'Business & Professional',
  'Travel & Daily Life',
  'Exam Preparation (IELTS/TOEFL)',
  'Academic Communication',
];

export function SettingsPage() {
  const { user, activeLanguage, switchPrimaryLanguage, refreshUserProfile } = useAuthStore();
  const { addToast } = useUiStore();

  const [activeSettingsTab, setActiveSettingsTab] = useState('tracks'); // 'tracks' | 'profile' | 'audio'

  // Profile update state
  const [profileForm, setProfileForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
  });
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Enroll modal state
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [newLangCode, setNewLangCode] = useState('es-ES');
  const [newCefr, setNewCefr] = useState('A1');
  const [newGoal, setNewGoal] = useState('General Fluency');
  const [isEnrollingSubmit, setIsEnrollingSubmit] = useState(false);

  // Edit track modal state
  const [editingTrack, setEditingTrack] = useState(null);
  const [editCefr, setEditCefr] = useState('B1');
  const [editGoal, setEditGoal] = useState('');
  const [isSavingTrack, setIsSavingTrack] = useState(false);

  // Delete track confirmation state
  const [deletingTrack, setDeletingTrack] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Primary language switching loading state
  const [switchingId, setSwitchingId] = useState(null);

  useEffect(() => {
    if (user) {
      setProfileForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
      });
    }
  }, [user]);

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setIsSavingProfile(true);
    try {
      await authApi.updateProfile({
        first_name: profileForm.first_name.trim(),
        last_name: profileForm.last_name.trim(),
        email: profileForm.email.trim(),
      });
      await refreshUserProfile();
      addToast({
        title: 'Profile Updated',
        message: 'Your personal details have been saved successfully.',
        type: 'success',
      });
    } catch (err) {
      console.error('Failed to update profile:', err);
      addToast({
        title: 'Update Failed',
        message: err.response?.data?.detail || 'Could not update profile.',
        type: 'error',
      });
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleSetPrimary = async (langId) => {
    setSwitchingId(langId);
    try {
      await switchPrimaryLanguage(langId);
      addToast({
        title: 'Primary Language Updated',
        message: 'Your active learning language has been updated across the agent.',
        type: 'success',
      });
    } catch (err) {
      console.error('Failed to set primary language:', err);
      addToast({
        title: 'Update Failed',
        message: err.response?.data?.detail || 'Could not update primary language.',
        type: 'error',
      });
    } finally {
      setSwitchingId(null);
    }
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    setIsEnrollingSubmit(true);
    try {
      await authApi.enrollLanguage({
        language_code: newLangCode,
        current_cefr_level: newCefr,
        target_goal: newGoal,
      });
      await refreshUserProfile();
      addToast({
        title: 'Enrolled Successfully',
        message: `You are now enrolled in ${newLangCode}.`,
        type: 'success',
      });
      setIsEnrolling(false);
    } catch (err) {
      console.error('Enrollment error:', err);
      const msg = err.response?.data?.detail || 
        err.response?.data?.non_field_errors?.join(' ') || 
        'Could not enroll in language.';
      addToast({
        title: 'Enrollment Failed',
        message: msg,
        type: 'error',
      });
    } finally {
      setIsEnrollingSubmit(false);
    }
  };

  const openEditTrack = (track) => {
    setEditingTrack(track);
    setEditCefr(track.current_cefr_level || 'B1');
    setEditGoal(track.target_goal || 'General Fluency');
  };

  const handleSaveTrack = async (e) => {
    e.preventDefault();
    if (!editingTrack) return;

    setIsSavingTrack(true);
    try {
      await authApi.updateUserLanguage(editingTrack.id, {
        current_cefr_level: editCefr,
        target_goal: editGoal.trim(),
      });
      await refreshUserProfile();
      addToast({
        title: 'Track Updated',
        message: `Updated ${editingTrack.language_name || editingTrack.language_code} settings.`,
        type: 'success',
      });
      setEditingTrack(null);
    } catch (err) {
      console.error('Failed to update track:', err);
      addToast({
        title: 'Update Failed',
        message: err.response?.data?.detail || 'Could not update language track.',
        type: 'error',
      });
    } finally {
      setIsSavingTrack(false);
    }
  };

  const handleDeleteTrack = async () => {
    if (!deletingTrack) return;
    setIsDeleting(true);
    try {
      await authApi.deleteUserLanguage(deletingTrack.id);
      await refreshUserProfile();
      addToast({
        title: 'Track Removed',
        message: `Unenrolled from ${deletingTrack.language_name || deletingTrack.language_code}.`,
        type: 'info',
      });
      setDeletingTrack(null);
    } catch (err) {
      console.error('Failed to delete track:', err);
      addToast({
        title: 'Removal Failed',
        message: err.response?.data?.detail || 'Could not remove language track.',
        type: 'error',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const enrolledLanguages = user?.user_languages || [];

  return (
    <div className="settings-clean-page">
      {/* Header */}
      <header className="settings-clean-header">
        <div className="header-eyebrow">
          <Sliders size={14} />
          <span>Configuration</span>
        </div>
        <h1 className="settings-title">Preferences & Languages</h1>
        <p className="settings-sub-desc">
          Manage your enrolled language tracks, adjust CEFR targets, and update your learner account.
        </p>
      </header>

      {/* Clean Sub-Navigation Tabs */}
      <nav className="settings-nav-tabs">
        <button
          type="button"
          className={`settings-tab-btn ${activeSettingsTab === 'tracks' ? 'active' : ''}`}
          onClick={() => setActiveSettingsTab('tracks')}
        >
          <Globe size={16} />
          <span>Language Tracks ({enrolledLanguages.length})</span>
        </button>

        <button
          type="button"
          className={`settings-tab-btn ${activeSettingsTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveSettingsTab('profile')}
        >
          <User size={16} />
          <span>Account Profile</span>
        </button>

        <button
          type="button"
          className={`settings-tab-btn ${activeSettingsTab === 'audio' ? 'active' : ''}`}
          onClick={() => setActiveSettingsTab('audio')}
        >
          <Volume2 size={16} />
          <span>Voice & AI Audio</span>
        </button>
      </nav>

      {/* Main Settings Content */}
      <div className="settings-tab-content">
        {/* TAB 1: LANGUAGE TRACKS */}
        {activeSettingsTab === 'tracks' && (
          <div className="tab-pane-fade">
            <div className="section-head-bar">
              <div>
                <h3 className="section-head-title">Your Enrolled Language Tracks</h3>
                <p className="section-head-desc">
                  Select which language is active as your primary target, or enroll in new language programs.
                </p>
              </div>

              <button
                type="button"
                className="enroll-trigger-btn"
                onClick={() => setIsEnrolling(true)}
              >
                <Plus size={16} />
                <span>Enroll in New Language</span>
              </button>
            </div>

            <div className="tracks-clean-grid">
              {enrolledLanguages.map((ul) => {
                const isPrimary = ul.id === activeLanguage?.id || ul.is_primary;
                const practiceMins = Math.floor((ul.total_practice_seconds || 0) / 60);

                return (
                  <div 
                    key={ul.id} 
                    className={`clean-track-card ${isPrimary ? 'is-primary-card' : ''}`}
                  >
                    <div className="track-card-top">
                      <div className="track-brand">
                        <div className="track-globe-icon">
                          <Globe size={22} />
                        </div>
                        <div>
                          <h4 className="track-name">{ul.language_name || ul.language_code}</h4>
                          <span className="track-goal-sub">{ul.target_goal || 'General Fluency'}</span>
                        </div>
                      </div>

                      <div className="track-badges-group">
                        {isPrimary && (
                          <span className="primary-pill">
                            <Star size={11} fill="currentColor" /> Active Primary
                          </span>
                        )}
                        <span className="cefr-tag-pill">{ul.current_cefr_level}</span>
                      </div>
                    </div>

                    <div className="track-stats-row">
                      <div className="track-stat-item">
                        <span className="stat-label">Practice Time</span>
                        <span className="stat-value">{practiceMins}m</span>
                      </div>
                      <div className="track-stat-item">
                        <span className="stat-label">Sessions</span>
                        <span className="stat-value">{ul.total_sessions_completed || 0}</span>
                      </div>
                      <div className="track-stat-item">
                        <span className="stat-label">Code</span>
                        <span className="stat-value">{ul.language_code}</span>
                      </div>
                    </div>

                    <div className="track-card-footer">
                      {!isPrimary ? (
                        <button
                          type="button"
                          className="set-primary-btn"
                          onClick={() => handleSetPrimary(ul.id)}
                          disabled={switchingId === ul.id}
                        >
                          {switchingId === ul.id ? <Spinner size="sm" /> : 'Set as Primary'}
                        </button>
                      ) : (
                        <span className="active-primary-indicator">
                          <Check size={14} /> Currently Active
                        </span>
                      )}

                      <div className="track-minor-actions">
                        <button
                          type="button"
                          className="icon-action-btn edit"
                          onClick={() => openEditTrack(ul)}
                          title="Edit target level and goal"
                        >
                          <Edit3 size={15} />
                          <span>Edit</span>
                        </button>

                        {!isPrimary && (
                          <button
                            type="button"
                            className="icon-action-btn delete"
                            onClick={() => setDeletingTrack(ul)}
                            title="Unenroll from track"
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: ACCOUNT PROFILE */}
        {activeSettingsTab === 'profile' && (
          <div className="tab-pane-fade profile-pane-wrapper">
            <div className="profile-clean-card">
              <div className="profile-card-header">
                <User size={20} className="section-icon" />
                <div>
                  <h3>Personal Information</h3>
                  <p>Update your display name and contact email address.</p>
                </div>
              </div>

              <form onSubmit={handleProfileSubmit} className="clean-profile-form">
                <div className="form-fields-grid">
                  <div className="field-block">
                    <label>Username</label>
                    <input
                      type="text"
                      value={user?.username || ''}
                      disabled
                      className="clean-input disabled"
                    />
                    <span className="input-hint">Unique username cannot be changed.</span>
                  </div>

                  <div className="field-block">
                    <label>Email Address</label>
                    <input
                      type="email"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                      required
                      className="clean-input"
                    />
                  </div>

                  <div className="field-block">
                    <label>First Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Alex"
                      value={profileForm.first_name}
                      onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                      className="clean-input"
                    />
                  </div>

                  <div className="field-block">
                    <label>Last Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Morgan"
                      value={profileForm.last_name}
                      onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                      className="clean-input"
                    />
                  </div>
                </div>

                <div className="form-submit-row">
                  <button
                    type="submit"
                    className="save-profile-btn"
                    disabled={isSavingProfile}
                  >
                    {isSavingProfile ? (
                      <>
                        <span className="spinner-sm"></span> Saving...
                      </>
                    ) : (
                      <>
                        <Save size={16} />
                        <span>Save Profile Changes</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* TAB 3: AUDIO & COACH PREFERENCES */}
        {activeSettingsTab === 'audio' && (
          <div className="tab-pane-fade audio-preferences-wrapper">
            <div className="audio-pref-card">
              <div className="pref-header">
                <Volume2 size={20} className="section-icon" />
                <div>
                  <h3>AI Coach Speech Synthesis</h3>
                  <p>Configure voice playback cadence and test in-browser speech.</p>
                </div>
              </div>

              <div className="pref-body">
                <div className="pref-row">
                  <div>
                    <h4 className="pref-row-title">Coach Speech Speed</h4>
                    <p className="pref-row-desc">
                      Select how fast the AI Coach speaks during practice exercises and roleplays.
                    </p>
                  </div>
                  <div className="sample-player-wrap">
                    <AudioPromptPlayer
                      text="Hello! Welcome to FluentFlow. This is an audio test of your browser's speech synthesis engine."
                      label="Test Voice"
                      size="md"
                    />
                  </div>
                </div>

                <div className="pref-divider"></div>

                <div className="pref-row">
                  <div>
                    <h4 className="pref-row-title">Microphone & Noise Cancellation</h4>
                    <p className="pref-row-desc">
                      FluentFlow automatically engages browser echo cancellation and background noise suppression during recording.
                    </p>
                  </div>
                  <div className="mic-status-badge">
                    <span className="status-dot"></span>
                    <span>Ready for Recording</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* MODAL 1: ENROLL NEW LANGUAGE */}
      {isEnrolling && (
        <div className="settings-modal-backdrop" onClick={() => setIsEnrolling(false)}>
          <div className="settings-clean-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-title-group">
                <Globe size={20} />
                <h3>Enroll in New Language Track</h3>
              </div>
              <button 
                type="button" 
                className="btn-modal-close" 
                onClick={() => setIsEnrolling(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleEnroll} className="modal-body-form">
              <div className="form-item">
                <label>Target Language</label>
                <select
                  value={newLangCode}
                  onChange={(e) => setNewLangCode(e.target.value)}
                  className="modal-select"
                  required
                >
                  {AVAILABLE_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name} ({lang.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-item">
                <label>Starting CEFR Level</label>
                <div className="cefr-choice-pills">
                  {CEFR_LEVELS.map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setNewCefr(lvl)}
                      className={`cefr-pill-btn ${newCefr === lvl ? 'active' : ''}`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-item">
                <label>Learning Goal / Motivation</label>
                <input
                  type="text"
                  value={newGoal}
                  onChange={(e) => setNewGoal(e.target.value)}
                  placeholder="e.g. Career advancement, Travel"
                  className="modal-text-input"
                  required
                />
                <div className="presets-row">
                  {GOAL_PRESETS.map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      className="preset-chip"
                      onClick={() => setNewGoal(preset)}
                    >
                      {preset}
                    </button>
                  ))}
                </div>
              </div>

              <div className="modal-footer-actions">
                <button 
                  type="button" 
                  className="modal-cancel-btn" 
                  onClick={() => setIsEnrolling(false)}
                  disabled={isEnrollingSubmit}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="modal-confirm-btn" 
                  disabled={isEnrollingSubmit}
                >
                  {isEnrollingSubmit ? 'Enrolling...' : 'Start Learning Track'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: EDIT LANGUAGE TRACK */}
      {editingTrack && (
        <div className="settings-modal-backdrop" onClick={() => setEditingTrack(null)}>
          <div className="settings-clean-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-title-group">
                <Edit3 size={20} />
                <h3>Edit {editingTrack.language_name || editingTrack.language_code} Track</h3>
              </div>
              <button 
                type="button" 
                className="btn-modal-close" 
                onClick={() => setEditingTrack(null)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveTrack} className="modal-body-form">
              <div className="form-item">
                <label>Proficiency Target (CEFR)</label>
                <div className="cefr-choice-pills">
                  {CEFR_LEVELS.map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setEditCefr(lvl)}
                      className={`cefr-pill-btn ${editCefr === lvl ? 'active' : ''}`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-item">
                <label>Learning Goal</label>
                <input
                  type="text"
                  value={editGoal}
                  onChange={(e) => setEditGoal(e.target.value)}
                  className="modal-text-input"
                  required
                />
                <div className="presets-row">
                  {GOAL_PRESETS.map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      className="preset-chip"
                      onClick={() => setEditGoal(preset)}
                    >
                      {preset}
                    </button>
                  ))}
                </div>
              </div>

              <div className="modal-footer-actions">
                <button 
                  type="button" 
                  className="modal-cancel-btn" 
                  onClick={() => setEditingTrack(null)}
                  disabled={isSavingTrack}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="modal-confirm-btn" 
                  disabled={isSavingTrack}
                >
                  {isSavingTrack ? 'Updating...' : 'Save Track Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: DELETE CONFIRMATION */}
      {deletingTrack && (
        <div className="settings-modal-backdrop" onClick={() => setDeletingTrack(null)}>
          <div className="settings-clean-modal danger-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-title-group text-danger">
                <Trash2 size={20} />
                <h3>Remove Language Track</h3>
              </div>
              <button 
                type="button" 
                className="btn-modal-close" 
                onClick={() => setDeletingTrack(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-danger-body">
              <p>
                Are you sure you want to unenroll from <strong>{deletingTrack.language_name || deletingTrack.language_code}</strong>?
              </p>
              <span className="danger-subnote">
                This will detach your practice records for this language track. This action cannot be undone.
              </span>
            </div>

            <div className="modal-footer-actions">
              <button 
                type="button" 
                className="modal-cancel-btn" 
                onClick={() => setDeletingTrack(null)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="modal-danger-confirm-btn" 
                onClick={handleDeleteTrack}
                disabled={isDeleting}
              >
                {isDeleting ? 'Removing...' : 'Confirm Unenroll'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
