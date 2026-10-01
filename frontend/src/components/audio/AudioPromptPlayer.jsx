import React, { useState } from 'react';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import './AudioPromptPlayer.css';

export function AudioPromptPlayer({
  text,
  label = 'Listen',
  size = 'md',
  showRateToggle = true,
  autoPlay = false,
  className = '',
}) {
  const { isSupported, isSpeaking, currentText, speak, stop, rate, setRate } = useSpeechSynthesis();
  const [localRate, setLocalRate] = useState(1.0);

  const isCurrentSpeaking = isSpeaking && currentText === text;

  const handlePlayToggle = (e) => {
    e.stopPropagation();
    if (!text) return;

    if (isCurrentSpeaking) {
      stop();
    } else {
      speak(text, { rate: localRate });
    }
  };

  const handleSpeedToggle = (e) => {
    e.stopPropagation();
    const nextRate = localRate === 1.0 ? 0.85 : localRate === 0.85 ? 1.15 : 1.0;
    setLocalRate(nextRate);
    setRate(nextRate);

    // If currently speaking, re-speak at new speed
    if (isCurrentSpeaking) {
      speak(text, { rate: nextRate });
    }
  };

  if (!isSupported) {
    return null;
  }

  return (
    <div className={`audio-prompt-player-container size-${size} ${className}`}>
      <button
        type="button"
        className={`audio-prompt-btn ${isCurrentSpeaking ? 'is-playing' : ''}`}
        onClick={handlePlayToggle}
        title={isCurrentSpeaking ? 'Stop speaking' : 'Listen aloud'}
        aria-label={isCurrentSpeaking ? 'Stop speaking' : 'Listen aloud'}
      >
        <span className="audio-prompt-icon-wrap">
          {isCurrentSpeaking ? (
            <span className="soundwave-bars">
              <span className="bar bar-1"></span>
              <span className="bar bar-2"></span>
              <span className="bar bar-3"></span>
              <span className="bar bar-4"></span>
            </span>
          ) : (
            <svg
              className="speaker-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor" fillOpacity="0.15"></polygon>
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
            </svg>
          )}
        </span>
        {label && (
          <span className="audio-prompt-label">
            {isCurrentSpeaking ? 'Speaking...' : label}
          </span>
        )}
      </button>

      {showRateToggle && (
        <button
          type="button"
          className="speed-toggle-chip"
          onClick={handleSpeedToggle}
          title="Toggle speech pace"
        >
          {localRate}x
        </button>
      )}
    </div>
  );
}
