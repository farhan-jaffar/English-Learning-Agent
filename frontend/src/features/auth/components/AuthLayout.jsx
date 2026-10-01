import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sparkles, Mic, BarChart3 } from 'lucide-react';
import './AuthLayout.css';

export function AuthLayout() {
  return (
    <div className="auth-wrapper">
      {/* Brand Hero Panel */}
      <section className="auth-brand-side">
        <div className="auth-logo-row">
          <div className="auth-logo-badge">F</div>
          <span className="auth-logo-text">FluentFlow</span>
        </div>

        <div className="auth-hero-copy">
          <h1 className="auth-hero-title">
            Speak English with <span>confidence</span> & adaptive intelligence.
          </h1>
          <p className="auth-hero-subtitle">
            Experience an intelligent feedback loop that analyzes your pronunciation, expands your vocabulary, and coaches you to fluency.
          </p>

          <div className="auth-features-list">
            <div className="auth-feature-pill">
              <div className="auth-feature-icon">
                <Sparkles size={18} />
              </div>
              <div className="auth-feature-text">
                <h4>Adaptive Next Exercise</h4>
                <p>Personalized learning tailored to your CEFR gaps</p>
              </div>
            </div>

            <div className="auth-feature-pill">
              <div className="auth-feature-icon">
                <Mic size={18} />
              </div>
              <div className="auth-feature-text">
                <h4>Audio Analysis & Coaching</h4>
                <p>Speech turn tracking and phoneme-level tips</p>
              </div>
            </div>

            <div className="auth-feature-pill">
              <div className="auth-feature-icon">
                <BarChart3 size={18} />
              </div>
              <div className="auth-feature-text">
                <h4>CEFR Progression Engine</h4>
                <p>Real-time analytics across your enrolled languages</p>
              </div>
            </div>
          </div>
        </div>

        <footer className="auth-brand-footer">
          &copy; {new Date().getFullYear()} FluentFlow AI. Powered by Django REST & React.
        </footer>
      </section>

      {/* Form Content Side */}
      <main className="auth-form-side">
        <div className="auth-form-card">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
