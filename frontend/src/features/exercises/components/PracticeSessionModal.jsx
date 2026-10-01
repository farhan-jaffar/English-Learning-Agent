import React, { useState, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  Lightbulb, 
  BookOpen, 
  CheckCircle2, 
  Mic, 
  Volume2, 
  RotateCcw, 
  ArrowRight,
  ShieldCheck,
  Headphones,
  Compass
} from 'lucide-react';
import { recordingsApi } from '../../../lib/api/recordings';
import { exercisesApi } from '../../../lib/api/exercises';
import { useUIStore } from '../../../stores/uiStore';
import { useAuthStore } from '../../../stores/authStore';
import Badge from '../../../components/ui/Badge';
import AudioRecorderCard from '../../../components/audio/AudioRecorderCard';
import { AudioPromptPlayer } from '../../../components/audio/AudioPromptPlayer';
import AnalysisFeedbackCard from '../../recordings/components/AnalysisFeedbackCard';
import './PracticeSessionModal.css';

/**
 * Focused, high-aesthetic practice modal where learner records speech
 * response to an exercise and receives instant AI linguistic feedback.
 */
export default function PracticeSessionModal({
  exercise: initialExercise,
  isOpen,
  onClose,
  onComplete,
}) {
  const [currentExercise, setCurrentExercise] = useState(initialExercise);
  const [step, setStep] = useState('recording'); // 'recording' | 'analyzing' | 'feedback'
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [completedRecording, setCompletedRecording] = useState(null);
  const [error, setError] = useState(null);

  const addToast = useUIStore((state) => state.addToast);
  const activeLanguage = useAuthStore((state) => state.activeLanguage);

  useEffect(() => {
    if (initialExercise) {
      setCurrentExercise(initialExercise);
      setStep('recording');
      setCompletedRecording(null);
      setError(null);
    }
  }, [initialExercise, isOpen]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !isSubmitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  const handleSubmitAudio = async (audioBlob, durationSeconds) => {
    if (!currentExercise || !audioBlob) return;

    setIsSubmitting(true);
    setStep('analyzing');
    setError(null);

    try {
      // 1. Upload audio file
      const uploadRes = await recordingsApi.uploadRecording(
        currentExercise.id,
        audioBlob,
        durationSeconds
      );

      const recordingId = uploadRes.id;

      // 2. Fetch recording detail with analysis
      let detail = null;
      for (let attempt = 0; attempt < 6; attempt++) {
        detail = await recordingsApi.getRecordingDetail(recordingId);
        if (detail.status === 'analyzed' && detail.analysis) {
          break;
        }
        if (detail.status === 'failed') {
          throw new Error(detail.error_message || 'Speech analysis failed.');
        }
        // Wait 1.5s before next poll
        await new Promise((res) => setTimeout(res, 1500));
      }

      setCompletedRecording(detail);
      setStep('feedback');
      addToast({
        title: 'Analysis Complete!',
        message: `Your speech has been evaluated at CEFR ${detail.analysis?.estimated_cefr || 'level'}.`,
        type: 'success',
      });

      if (onComplete) {
        onComplete(detail);
      }
    } catch (err) {
      console.error('Error submitting recording:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to analyze recording.';
      setError(msg);
      setStep('recording');
      addToast({
        title: 'Submission Error',
        message: msg,
        type: 'error',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextExercise = async () => {
    setIsSubmitting(true);
    try {
      const nextEx = await exercisesApi.getNextExercise(activeLanguage?.code, currentExercise?.id);
      if (nextEx && nextEx.id) {
        setCurrentExercise(nextEx);
        setCompletedRecording(null);
        setStep('recording');
        setError(null);
      } else {
        addToast({
          title: 'All caught up!',
          message: 'You have reviewed all available exercises for now.',
          type: 'info',
        });
        onClose();
      }
    } catch (err) {
      console.error('Error fetching next exercise:', err);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    setCompletedRecording(null);
    setStep('recording');
    setError(null);
  };

  if (!isOpen || !currentExercise) return null;

  const {
    title,
    prompt_text,
    skill_focus,
    cefr_level,
    vocabulary_hints = [],
    topic_tags = [],
  } = currentExercise;

  return (
    <div className="practice-modal-backdrop" onClick={onClose}>
      <div 
        className="practice-modal-container"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Studio Top Header */}
        <div className="practice-modal-header">
          <div className="header-left">
            <div className="studio-breadcrumb">
              <span className="studio-tag">
                <Sparkles size={13} className="studio-tag-icon" />
                Speaking Studio
              </span>
              <span className="breadcrumb-dot">•</span>
              <span className="step-counter">
                {step === 'recording' && 'Step 1 of 2: Record Speech'}
                {step === 'analyzing' && 'AI Speech Evaluation'}
                {step === 'feedback' && 'Step 2 of 2: Linguistic Report'}
              </span>
            </div>
            <h2 className="practice-title">{title}</h2>
          </div>

          <div className="header-right">
            <div className="header-badges">
              <Badge variant="lemon" size="sm">{cefr_level}</Badge>
              <Badge variant="olive" size="sm">{skill_focus || 'Fluency'}</Badge>
            </div>
            <div className="header-actions">
              <span className="kbd-shortcut-hint" title="Press Escape to close">ESC</span>
              <button
                type="button"
                className="btn-modal-close"
                onClick={onClose}
                disabled={isSubmitting}
                aria-label="Close practice modal"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Studio Stage Stepper */}
        <div className="practice-stage-tracker">
          <div className={`tracker-segment ${step === 'recording' ? 'active' : 'completed'}`}>
            <span className="tracker-dot" />
            <span className="tracker-label">1. Practice & Record</span>
          </div>
          <div className="tracker-connector" />
          <div className={`tracker-segment ${step === 'analyzing' ? 'active pulse' : step === 'feedback' ? 'completed' : ''}`}>
            <span className="tracker-dot" />
            <span className="tracker-label">2. AI Evaluation</span>
          </div>
          <div className="tracker-connector" />
          <div className={`tracker-segment ${step === 'feedback' ? 'active' : ''}`}>
            <span className="tracker-dot" />
            <span className="tracker-label">3. Feedback & Scores</span>
          </div>
        </div>

        {/* Modal Body Content */}
        <div className="practice-modal-body">
          {/* STEP 1: RECORDING WORKSPACE */}
          {step === 'recording' && (
            <div className="practice-step-recording">
              {/* Exercise Challenge / Prompt Card */}
              <div className="prompt-stage-card">
                <div className="prompt-card-top">
                  <div className="prompt-label-group">
                    <div className="prompt-icon-badge">
                      <Lightbulb size={18} />
                    </div>
                    <div>
                      <div className="prompt-kicker">Speaking Prompt</div>
                      <div className="prompt-subkicker">Respond out loud with natural flow and clarity</div>
                    </div>
                  </div>
                  <div className="prompt-audio-action">
                    <AudioPromptPlayer text={prompt_text} label="Listen to Prompt" size="sm" />
                  </div>
                </div>

                <div className="prompt-body-quote">
                  <span className="quote-glyph quote-start">“</span>
                  <p className="prompt-statement">{prompt_text}</p>
                  <span className="quote-glyph quote-end">”</span>
                </div>

                {/* Vocabulary Inspiration Hints */}
                {vocabulary_hints && vocabulary_hints.length > 0 && (
                  <div className="prompt-hints-dock">
                    <div className="hints-dock-title">
                      <BookOpen size={13} />
                      <span>Recommended Target Vocabulary:</span>
                    </div>
                    <div className="hints-tags-row">
                      {vocabulary_hints.map((hint, idx) => (
                        <span key={idx} className="modern-hint-tag" title="Incorporate in your response">
                          <span className="hint-bullet" />
                          {hint}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Topic tags row if present */}
                {topic_tags && topic_tags.length > 0 && (
                  <div className="prompt-topics-dock">
                    {topic_tags.map((t, idx) => (
                      <span key={idx} className="topic-subtle-tag">
                        #{typeof t === 'string' ? t : t.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Audio Recorder Engine */}
              <div className="recorder-stage-dock">
                <AudioRecorderCard
                  onSubmit={handleSubmitAudio}
                  isSubmitting={isSubmitting}
                />
              </div>
            </div>
          )}

          {/* STEP 2: ANALYZING STATE */}
          {step === 'analyzing' && (
            <div className="practice-step-analyzing">
              <div className="analyzing-radar-stage">
                {/* Multi-ring acoustic pulse animation */}
                <div className="acoustic-radar-wrapper">
                  <div className="radar-ring ring-1" />
                  <div className="radar-ring ring-2" />
                  <div className="radar-ring ring-3" />
                  <div className="radar-core">
                    <Sparkles size={30} className="radar-sparkle-icon" />
                  </div>
                </div>

                <div className="analyzing-headline">
                  <h3>Evaluating Your Speech Response</h3>
                  <p className="analyzing-description">
                    Our AI speech model is transcribing your recording and benchmarking cadence, grammatical accuracy, and vocabulary against CEFR {cefr_level}.
                  </p>
                </div>

                {/* Dynamic Analysis Milestones */}
                <div className="analysis-milestones-card">
                  <div className="milestone-item completed">
                    <div className="milestone-icon-wrap">
                      <CheckCircle2 size={16} />
                    </div>
                    <div className="milestone-content">
                      <span className="milestone-title">Whisper Speech-to-Text Transcription</span>
                      <span className="milestone-status">Audio processed successfully</span>
                    </div>
                  </div>

                  <div className="milestone-item in-progress">
                    <div className="milestone-icon-wrap">
                      <div className="milestone-spinner" />
                    </div>
                    <div className="milestone-content">
                      <span className="milestone-title">Fluency & Cadence Calculation</span>
                      <span className="milestone-status">Measuring WPM, speech pauses, and rhythm</span>
                    </div>
                  </div>

                  <div className="milestone-item pending">
                    <div className="milestone-icon-wrap">
                      <div className="milestone-dot" />
                    </div>
                    <div className="milestone-content">
                      <span className="milestone-title">Grammar & Lexical Scoring</span>
                      <span className="milestone-status">Evaluating syntactic precision & CEFR level</span>
                    </div>
                  </div>
                </div>

                {/* Fluid indeterminate progress bar */}
                <div className="analyzing-bar-track">
                  <div className="analyzing-bar-glow" />
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: FEEDBACK DISPLAY */}
          {step === 'feedback' && completedRecording && (
            <div className="practice-step-feedback">
              <AnalysisFeedbackCard
                analysis={completedRecording.analysis}
                transcript={completedRecording.turn?.text_content || ''}
                onNext={handleNextExercise}
                onRetry={handleRetry}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
