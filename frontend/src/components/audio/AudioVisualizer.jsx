import React from 'react';
import './AudioVisualizer.css';

/**
 * Animated real-time frequency bar visualizer for microphone input.
 * @param {Array<number>} audioLevels - Array of normalized volume levels (0.0 to 1.0)
 * @param {boolean} isRecording - True when recording is active
 * @param {boolean} isPaused - True when recording is paused
 */
export default function AudioVisualizer({ audioLevels = [], isRecording = false, isPaused = false }) {
  // Fallback idle levels if none provided
  const bars = audioLevels.length > 0 ? audioLevels : new Array(24).fill(0.08);

  return (
    <div className={`audio-visualizer-container ${isRecording ? 'is-recording' : ''} ${isPaused ? 'is-paused' : ''}`}>
      <div className="audio-visualizer-bars">
        {bars.map((level, idx) => {
          // Height between 10% and 100%
          const heightPercent = Math.max(10, Math.min(100, Math.round(level * 100)));
          return (
            <div
              key={idx}
              className="audio-bar"
              style={{
                height: isRecording ? `${heightPercent}%` : '12%',
                animationDelay: `${(idx % 6) * 0.1}s`,
              }}
            />
          );
        })}
      </div>
      <div className="audio-visualizer-reflection" aria-hidden="true">
        {bars.map((level, idx) => {
          const heightPercent = Math.max(8, Math.min(60, Math.round(level * 40)));
          return (
            <div
              key={idx}
              className="audio-bar-reflect"
              style={{
                height: isRecording ? `${heightPercent}%` : '8%',
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
