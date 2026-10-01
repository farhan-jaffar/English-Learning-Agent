import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { User, Lock, Eye, EyeOff, AlertCircle, ArrowRight } from 'lucide-react';
import { Input } from '../../../components/ui/Input';
import { Button } from '../../../components/ui/Button';
import { authApi } from '../../../lib/api/auth';
import { useAuthStore } from '../../../stores/authStore';
import { useUiStore } from '../../../stores/uiStore';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth } = useAuthStore();
  const { addToast } = useUiStore();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
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
      newErrors.username = 'Username or email is required';
    }
    if (!formData.password) {
      newErrors.password = 'Password is required';
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
      const response = await authApi.login({
        username: formData.username.trim(),
        password: formData.password,
      });

      setAuth(response);

      addToast({
        title: `Welcome back, ${response.user.username}!`,
        message: 'Successfully authenticated.',
        type: 'success',
      });

      let destination = location.state?.from?.pathname || '/';
      if (destination === '/login' || destination === '/register') {
        destination = '/';
      }
      navigate(destination, { replace: true });
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
          setErrors(responseData);
        }
      } else {
        setGeneralError('Could not connect to the server. Please check your network.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="auth-form-header">
        <h2>Sign In</h2>
        <p>Enter your credentials to continue your language journey.</p>
      </div>

      {generalError && (
        <div className="auth-error-banner" role="alert">
          <AlertCircle size={16} />
          <span>{generalError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <Input
          label="Username or Email"
          name="username"
          type="text"
          placeholder="e.g. learner or user@example.com"
          value={formData.username}
          onChange={handleChange}
          error={errors.username}
          icon={User}
          required
          autoFocus
        />

        <Input
          label="Password"
          name="password"
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          value={formData.password}
          onChange={handleChange}
          error={errors.password}
          icon={Lock}
          endIcon={showPassword ? EyeOff : Eye}
          onEndIconClick={() => setShowPassword((prev) => !prev)}
          required
        />

        <div style={{ marginTop: 'var(--space-2)' }}>
          <Button
            type="submit"
            variant="olive"
            size="lg"
            isBlock
            isLoading={isLoading}
            iconRight={ArrowRight}
          >
            Sign In
          </Button>
        </div>
      </form>

      <div style={{ marginTop: 'var(--space-6)', textAlign: 'center', fontSize: 'var(--font-size-sm)' }}>
        <span style={{ color: 'var(--color-text-secondary)' }}>Don't have an account? </span>
        <Link
          to="/register"
          style={{ color: 'var(--color-olive-dark)', fontWeight: 'var(--font-weight-bold)' }}
        >
          Create one now
        </Link>
      </div>
    </div>
  );
}
