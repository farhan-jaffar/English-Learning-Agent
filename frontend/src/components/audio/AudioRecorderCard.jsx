import React from 'react';
import { Mic, Square, Pause, Play, RotateCcw, Send, AlertCircle, Sparkles } from 'lucide-react';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import AudioVisualizer from './AudioVisualizer';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Spinner from '../ui/Spinner';
import './AudioRecorderCard.css';

/**
 * Interactive Audio Recorder card component.
 * @param {function} onSubmit - Callback invoked with (audioBlob, durationSeconds)
 * @param {boolean} isSubmitting - Whether the recording upload/analysis is processing
 * @param {boolean} disabled - Whether the card is disabled
 */
export default function AudioRecorderCard({ onSubmit, isSubmitting = false, disabled = false }) {
  const {
    state,
    recordingTime,
    audioLevels,
    audioBlob,
    audioUrl,
    error,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    resetRecording,
  } = useAudioRecorder();

  const formatTimer = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSubmit = () => {
    if (audioBlob && onSubmit) {
      onSubmit(audioBlob, recordingTime);
    }
  };

  return (
    <div className={`recorder-card ${state}`}>
      {/* Header / Status bar */}
      <div className="recorder-header">
        <div className="recorder-status">
          {state === 'inactive' && (
            <Badge variant="muted">Ready to Record</Badge>
          )}
          {state === 'requesting' && (
            <Badge variant="warning">Requesting Mic Access...</Badge>
          )}
          {state === 'recording' && (
            <Badge variant="lemon" className="recording-live-badge">
              <span className="live-dot" /> Live Recording
            </Badge>
          )}
          {state === 'paused' && (
            <Badge variant="warning">Paused</Badge>
          )}
          {state === 'recorded' && (
            <Badge variant="success">Recording Ready</Badge>
          )}
        </div>

        <div className="recorder-timer">
          <span className="timer-label">Time:</span>
          <span className={`timer-digits ${state === 'recording' ? 'active' : ''}`}>
            {formatTimer(recordingTime)}
          </span>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="recorder-error">
          <AlertCircle size={18} className="error-icon" />
          <span>{error}</span>
        </div>
      )}

      {/* Audio Visualizer (Live / Idle) */}
      {state !== 'recorded' && (
        <div className="recorder-visualizer-area">
          <AudioVisualizer
            audioLevels={audioLevels}
            isRecording={state === 'recording'}
            isPaused={state === 'paused'}
          />
        </div>
      )}

      {/* Audio Player Preview (when recorded) */}
      {state === 'recorded' && audioUrl && (
        <div className="recorder-preview-area">
          <div className="preview-player-box">
            <audio controls src={audioUrl} className="native-audio-player" />
          </div>
          <div className="preview-meta">
            <span>Duration: <strong>{formatTimer(recordingTime)}</strong></span>
            <span>File size: <strong>{audioBlob ? `${Math.round(audioBlob.size / 1024)} KB` : ''}</strong></span>
          </div>
        </div>
      )}

      {/* Controls Area */}
      <div className="recorder-controls">
        {state === 'inactive' && (
          <Button
            variant="lemon"
            size="lg"
            className="btn-record-main"
            onClick={startRecording}
            disabled={disabled || isSubmitting}
          >
            <Mic size={22} className="btn-icon-pulse" />
            <span>Start Speaking</span>
          </Button>
        )}

        {state === 'recording' && (
          <div className="active-controls-group">
            <Button
              variant="secondary"
              size="md"
              onClick={pauseRecording}
              disabled={isSubmitting}
            >
              <Pause size={18} />
              <span>Pause</span>
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={stopRecording}
              disabled={isSubmitting}
            >
              <Square size={18} />
              <span>Finish Recording</span>
            </Button>
          </div>
        )}

        {state === 'paused' && (
          <div className="active-controls-group">
            <Button
              variant="lemon"
              size="md"
              onClick={resumeRecording}
              disabled={isSubmitting}
            >
              <Play size={18} />
              <span>Resume</span>
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={stopRecording}
              disabled={isSubmitting}
            >
              <Square size={18} />
              <span>Finish Recording</span>
            </Button>
          </div>
        )}

        {state === 'recorded' && (
          <div className="review-controls-group">
            <Button
              variant="secondary"
              size="md"
              onClick={resetRecording}
              disabled={isSubmitting}
            >
              <RotateCcw size={18} />
              <span>Re-record</span>
            </Button>
            <Button
              variant="olive"
              size="lg"
              className="btn-submit-analysis"
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Spinner size="sm" />
                  <span>Evaluating Speech...</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  <span>Submit & Analyze</span>
                </>
              )}
            </Button>
          </div>
        )}
      </div>

      {/* Guidance footnote */}
      <div className="recorder-footer-hint">
        {state === 'inactive' && (
          <span>Speak clearly for 20–60 seconds. Our AI will analyze your pronunciation, fluency, and grammar.</span>
        )}
        {state === 'recording' && (
          <span>Speak naturally without rushing. You can pause anytime.</span>
        )}
        {state === 'recorded' && !isSubmitting && (
          <span>Listen to your recording above, or re-record before submitting for AI feedback.</span>
        )}
        {isSubmitting && (
          <span className="submitting-hint">Analyzing your cadence, grammar accuracy, and vocabulary depth...</span>
        )}
      </div>
    </div>
  );
}
