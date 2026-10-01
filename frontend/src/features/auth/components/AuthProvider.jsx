import React, { useEffect } from 'react';
import { useAuthStore } from '../../../stores/authStore';
import { Spinner } from '../../../components/ui/Spinner';

export function AuthProvider({ children }) {
  const { initializeAuth, isLoading } = useAuthStore();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: 'var(--color-bg)',
          gap: 'var(--space-4)',
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            backgroundColor: 'var(--color-primary)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--font-display)',
            fontWeight: 'var(--font-weight-extrabold)',
            fontSize: 'var(--font-size-2xl)',
            boxShadow: 'var(--shadow-lemon-glow)',
            color: 'var(--color-text)',
          }}
        >
          F
        </div>
        <Spinner size="md" color="var(--color-olive)" />
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          Loading FluentFlow...
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
