import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock, Eye, EyeOff, Globe, Target, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import { Input } from '../../../components/ui/Input';
import { Button } from '../../../components/ui/Button';
import { authApi } from '../../../lib/api/auth';
import { useAuthStore } from '../../../stores/authStore';
import { useUiStore } from '../../../stores/uiStore';

const CEFR_LEVELS = [
  { code: 'A1', label: 'A1 - Beginner', desc: 'Basic phrases & everyday expressions' },
  { code: 'A2', label: 'A2 - Elementary', desc: 'Routine tasks & direct information' },
  { code: 'B1', label: 'B1 - Intermediate', desc: 'Work, school, leisure & connected text' },
  { code: 'B2', label: 'B2 - Upper Intermediate', desc: 'Complex ideas & technical discussions' },
  { code: 'C1', label: 'C1 - Advanced', desc: 'Fluent, flexible & effective communication' },
  { code: 'C2', label: 'C2 - Mastery', desc: 'Effortless spontaneous native-like nuance' },
];

const TARGET_GOALS = [
  'General Fluency',
  'IELTS / TOEFL Prep',
  'Career & Job Interviews',
  'Academic English',
  'Travel & Conversational Confidence',
];

export function RegisterPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const { addToast } = useUiStore();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    cefr_level: 'B1',
    native_language: '',
    target_goal: 'General Fluency',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (generalError) {
      setGeneralError('');
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    setGeneralError('');

    try {
      const response = await authApi.register({
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password,
        password_confirm: formData.password_confirm,
        cefr_level: formData.cefr_level,
        native_language: formData.native_language.trim(),
        target_goal: formData.target_goal,
      });

      setAuth(response);

      addToast({
        title: 'Account created!',
        message: `Welcome to FluentFlow, ${response.user.username}. Enrolled in English (${formData.cefr_level}).`,
        type: 'success',
      });

      navigate('/', { replace: true });
    } catch (err) {
      const responseData = err.response?.data;
      if (responseData) {
        if (typeof responseData === 'string') {
          setGeneralError(responseData);
        } else if (responseData.detail) {
          setGeneralError(responseData.detail);
        } else if (responseData.non_field_errors) {
          setGeneralError(responseData.non_field_errors.join(' '));
        } else {
          // Field-specific validation errors from Django serializer
          const mappedErrors = {};
          Object.entries(responseData).forEach(([k, v]) => {
            mappedErrors[k] = Array.isArray(v) ? v.join(' ') : String(v);
          });
          setErrors(mappedErrors);
        }
      } else {
        setGeneralError('Could not register account. Please check your network connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="register-page">
      <div className="auth-form-header">
        <h2>Create Account</h2>
        <p>Start your AI-powered English journey in seconds.</p>
      </div>

      {generalError && (
        <div className="auth-error-banner" role="alert">
          <AlertCircle size={16} />
          <span>{generalError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <Input
          label="Username"
          name="username"
          type="text"
          placeholder="learner2026"
          value={formData.username}
          onChange={handleChange}
          error={errors.username}
          icon={User}
          required
        />

        <Input
          label="Email Address"
          name="email"
          type="email"
          placeholder="learner@example.com"
          value={formData.email}
          onChange={handleChange}
          error={errors.email}
          icon={Mail}
          required
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
          <Input
            label="Password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Min 8 chars"
            value={formData.password}
            onChange={handleChange}
            error={errors.password}
            icon={Lock}
            endIcon={showPassword ? EyeOff : Eye}
            onEndIconClick={() => setShowPassword((p) => !p)}
            required
          />

          <Input
            label="Confirm Password"
            name="password_confirm"
            type={showPasswordConfirm ? 'text' : 'password'}
            placeholder="Repeat password"
            value={formData.password_confirm}
            onChange={handleChange}
            error={errors.password_confirm}
            icon={Lock}
            endIcon={showPasswordConfirm ? EyeOff : Eye}
            onEndIconClick={() => setShowPasswordConfirm((p) => !p)}
            required
          />
        </div>

        {/* CEFR Level Selection */}
        <div className="input-wrapper">
          <label className="input-label" htmlFor="cefr_level">
            Current English Level (CEFR)
          </label>
          <div className="input-container">
            <select
              id="cefr_level"
              name="cefr_level"
              value={formData.cefr_level}
              onChange={handleChange}
              className="input-field"
              style={{ cursor: 'pointer' }}
            >
              {CEFR_LEVELS.map((lvl) => (
                <option key={lvl.code} value={lvl.code}>
                  {lvl.label} — {lvl.desc}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Native Language and Goal */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
          <Input
            label="Native Language"
            name="native_language"
            type="text"
            placeholder="e.g. Spanish, Urdu"
            value={formData.native_language}
            onChange={handleChange}
            error={errors.native_language}
            icon={Globe}
          />

          <div className="input-wrapper">
            <label className="input-label" htmlFor="target_goal">
              Learning Goal
            </label>
            <div className="input-container">
              <select
                id="target_goal"
                name="target_goal"
                value={formData.target_goal}
                onChange={handleChange}
                className="input-field"
                style={{ cursor: 'pointer' }}
              >
                {TARGET_GOALS.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 'var(--space-3)' }}>
          <Button
            type="submit"
            variant="olive"
            size="lg"
            isBlock
            isLoading={isLoading}
            iconRight={ArrowRight}
          >
            Create My Account
          </Button>
        </div>
      </form>

      <div style={{ marginTop: 'var(--space-5)', textAlign: 'center', fontSize: 'var(--font-size-sm)' }}>
        <span style={{ color: 'var(--color-text-secondary)' }}>Already have an account? </span>
        <Link
          to="/login"
          style={{ color: 'var(--color-olive-dark)', fontWeight: 'var(--font-weight-bold)' }}
        >
          Sign In
        </Link>
      </div>
    </div>
  );
}
