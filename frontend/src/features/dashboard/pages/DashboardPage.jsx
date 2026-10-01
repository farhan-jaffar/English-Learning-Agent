import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  PlayCircle,
  Clock,
  Award,
  Globe,
  Mic,
  TrendingUp,
  ArrowRight,
  BookOpen,
} from 'lucide-react';
import { useAuthStore } from '../../../stores/authStore';
import { exercisesApi } from '../../../lib/api/exercises';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { Spinner } from '../../../components/ui/Spinner';
import PracticeSessionModal from '../../exercises/components/PracticeSessionModal';
import { authApi } from '../../../lib/api/auth';
import './DashboardPage.css';

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, activeLanguage, setUser } = useAuthStore();

  const [recommendedExercise, setRecommendedExercise] = useState(null);
  const [isLoadingExercise, setIsLoadingExercise] = useState(true);
  const [isPracticeModalOpen, setIsPracticeModalOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchRecommendation = async () => {
      setIsLoadingExercise(true);
      try {
        const langCode = activeLanguage?.language_code || 'en-US';
        const data = await exercisesApi.getNextExercise(langCode);
        if (isMounted) {
          setRecommendedExercise(data);
        }
      } catch (err) {
        console.warn('Could not load next exercise recommendation:', err);
      } finally {
        if (isMounted) {
          setIsLoadingExercise(false);
        }
      }
    };

    fetchRecommendation();

    return () => {
      isMounted = false;
    };
  }, [activeLanguage?.language_code]);

  const level = activeLanguage?.current_cefr_level || user?.cefr_level || 'B1';
  const totalSessions = activeLanguage?.total_sessions_completed ?? 0;
  const practiceSeconds = activeLanguage?.total_practice_seconds ?? 0;
  const practiceMinutes = Math.floor(practiceSeconds / 60);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="dashboard-container">
      {/* Hero Welcome Banner */}
      <section className="dashboard-hero">
        <div className="dashboard-hero-content">
          <h1 className="dashboard-hero-greeting">
            {getGreeting()}, <span>{user?.username || 'Learner'}</span>!
          </h1>
          <p className="dashboard-hero-sub">
            Your personalized learning agent is ready. Practicing {activeLanguage?.language_name || 'English (US)'} with focus on {activeLanguage?.target_goal || 'General Fluency'}.
          </p>
          <div className="dashboard-hero-tags">
            <Badge variant="lemon">Active Level: {level}</Badge>
            <Badge variant="olive">Goal: {activeLanguage?.target_goal || 'General Fluency'}</Badge>
            {user?.native_language && (
              <Badge variant="muted">Native: {user.native_language}</Badge>
            )}
          </div>
        </div>
      </section>

      {/* Stats Cards Row */}
      <section className="dashboard-stats-grid" aria-label="Learning Statistics">
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-lemon">
            <Award size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">CEFR Mastery</span>
            <span className="stat-value">{level}</span>
            <span className="stat-hint">Active target standard</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-olive">
            <PlayCircle size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Sessions Done</span>
            <span className="stat-value">{totalSessions}</span>
            <span className="stat-hint">Completed turn exercises</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-success">
            <Clock size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Practice Time</span>
            <span className="stat-value">{practiceMinutes}m</span>
            <span className="stat-hint">{practiceSeconds} total audio seconds</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-muted">
            <Globe size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Languages</span>
            <span className="stat-value">{user?.user_languages?.length || 1}</span>
            <span className="stat-hint">Active language profile</span>
          </div>
        </div>
      </section>

      {/* Recommended Next Exercise Card */}
      <section aria-label="Recommended Practice">
        <div className="dashboard-recommended-card">
          <div className="recommended-badge-row">
            <Badge variant="olive" icon={Sparkles}>
              AI Adaptive Recommendation
            </Badge>
            {recommendedExercise?.skill_focus && (
              <Badge variant="muted">{recommendedExercise.skill_focus}</Badge>
            )}
            {recommendedExercise?.cefr_level && (
              <Badge variant="lemon">{recommendedExercise.cefr_level}</Badge>
            )}
          </div>

          {isLoadingExercise ? (
            <div style={{ padding: 'var(--space-8) 0', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <Spinner size="md" color="var(--color-olive)" />
              <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                Analyzing speech weaknesses to select your next exercise...
              </span>
            </div>
          ) : recommendedExercise ? (
            <>
              <h2 className="recommended-title">{recommendedExercise.title}</h2>
              <div className="recommended-prompt">
                <strong>Prompt: </strong>"{recommendedExercise.prompt_text}"
              </div>

              <div className="recommended-footer">
                <div className="recommended-meta">
                  <span>Language: {recommendedExercise.language_code || 'en-US'}</span>
                  <span>
                    Duration: {recommendedExercise.min_duration_seconds}–{recommendedExercise.max_duration_seconds}s
                  </span>
                  {recommendedExercise.topic_tags?.length > 0 && (
                    <span>Topics: {recommendedExercise.topic_tags.join(', ')}</span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                  <Button
                    variant="lemon"
                    size="md"
                    icon={PlayCircle}
                    onClick={() => setIsPracticeModalOpen(true)}
                  >
                    Start This Exercise
                  </Button>
                  <Button
                    variant="secondary"
                    size="md"
                    icon={BookOpen}
                    onClick={() => navigate('/practice')}
                  >
                    Browse All
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ padding: 'var(--space-4) 0' }}>
              <h3 className="recommended-title">Ready for Your Next Practice Session?</h3>
              <p style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                No active session in queue. Choose an exercise from the catalog or start an adaptive speech check.
              </p>
              <Button
                variant="olive"
                size="md"
                iconRight={ArrowRight}
                onClick={() => navigate('/practice')}
              >
                Explore Practice Exercises
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* Quick Action Shortcuts */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-4)' }}>
        <div
          className="card card-interactive"
          onClick={() => navigate('/practice')}
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}
        >
          <div className="stat-icon-wrapper stat-icon-lemon">
            <PlayCircle size={22} />
          </div>
          <div>
            <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: '2px' }}>Interactive Practice</h4>
            <p style={{ fontSize: 'var(--font-size-xs)' }}>Browse speaking exercises, pronunciation drills, and dialogues.</p>
          </div>
        </div>

        <div
          className="card card-interactive"
          onClick={() => navigate('/recordings')}
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}
        >
          <div className="stat-icon-wrapper stat-icon-olive">
            <Mic size={22} />
          </div>
          <div>
            <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: '2px' }}>Audio History</h4>
            <p style={{ fontSize: 'var(--font-size-xs)' }}>Review past recordings, acoustic feedback, and session turns.</p>
          </div>
        </div>

        <div
          className="card card-interactive"
          onClick={() => navigate('/progress')}
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}
        >
          <div className="stat-icon-wrapper stat-icon-success">
            <TrendingUp size={22} />
          </div>
          <div>
            <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: '2px' }}>Progress & Analytics</h4>
            <p style={{ fontSize: 'var(--font-size-xs)' }}>Track your CEFR journey across 7d, 30d, and 90d periods.</p>
          </div>
        </div>
      </section>

      {/* Practice Recording & Analysis Modal */}
      {isPracticeModalOpen && recommendedExercise && (
        <PracticeSessionModal
          exercise={recommendedExercise}
          isOpen={isPracticeModalOpen}
          onClose={() => setIsPracticeModalOpen(false)}
          onComplete={async () => {
            try {
              const updatedProfile = await authApi.getProfile();
              if (updatedProfile) {
                setUser(updatedProfile);
              }
            } catch (err) {
              console.warn('Failed to refresh user stats:', err);
            }
          }}
        />
      )}
    </div>
  );
}
