import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom React hook wrapping the Web Speech Synthesis API.
 * Provides speech playback for the AI Coach with rate/pitch control and event tracking.
 */
export function useSpeechSynthesis() {
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [rate, setRate] = useState(1.0);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [currentText, setCurrentText] = useState('');
  
  const activeUtteranceRef = useRef(null);

  // Initialize and discover available voices
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);

      const updateVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices() || [];
        setVoices(availableVoices);

        if (availableVoices.length > 0) {
          // Look for preferred English voices (Google, Natural, en-US, en-GB)
          const preferred =
            availableVoices.find((v) => v.lang === 'en-US' && (v.name.includes('Natural') || v.name.includes('Google'))) ||
            availableVoices.find((v) => v.lang === 'en-US') ||
            availableVoices.find((v) => v.lang.startsWith('en')) ||
            availableVoices[0];
          setSelectedVoice(preferred || null);
        }
      };

      updateVoices();
      window.speechSynthesis.onvoiceschanged = updateVoices;

      return () => {
        if (window.speechSynthesis) {
          window.speechSynthesis.cancel();
          window.speechSynthesis.onvoiceschanged = null;
        }
      };
    }
  }, []);

  const stop = useCallback(() => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setIsPaused(false);
      setCurrentText('');
      activeUtteranceRef.current = null;
    }
  }, []);

  const speak = useCallback(
    (text, options = {}) => {
      if (!isSupported || !text) return;

      // Stop any existing playback
      stop();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = options.rate ?? rate;
      utterance.pitch = options.pitch ?? 1.0;

      const voice = options.voice || selectedVoice;
      if (voice) {
        utterance.voice = voice;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
        setIsPaused(false);
        setCurrentText(text);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
        setCurrentText('');
        activeUtteranceRef.current = null;
      };

      utterance.onerror = (e) => {
        if (e.error !== 'canceled' && e.error !== 'interrupted') {
          console.warn('SpeechSynthesis error:', e);
        }
        setIsSpeaking(false);
        setIsPaused(false);
        setCurrentText('');
        activeUtteranceRef.current = null;
      };

      activeUtteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    [isSupported, rate, selectedVoice, stop]
  );

  const pause = useCallback(() => {
    if (isSupported && window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    }
  }, [isSupported]);

  const resume = useCallback(() => {
    if (isSupported && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    }
  }, [isSupported]);

  const toggleSpeech = useCallback(
    (text, options = {}) => {
      if (isSpeaking && currentText === text) {
        stop();
      } else {
        speak(text, options);
      }
    },
    [isSpeaking, currentText, stop, speak]
  );

  return {
    isSupported,
    isSpeaking,
    isPaused,
    rate,
    setRate,
    voices,
    selectedVoice,
    setSelectedVoice,
    currentText,
    speak,
    stop,
    pause,
    resume,
    toggleSpeech,
  };
}
