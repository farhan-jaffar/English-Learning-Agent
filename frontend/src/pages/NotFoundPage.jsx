import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Home } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        gap: 'var(--space-4)',
      }}
    >
      <div
        style={{
          fontSize: '72px',
          fontWeight: 800,
          fontFamily: 'var(--font-display)',
          color: 'var(--color-olive)',
          lineHeight: 1,
        }}
      >
        404
      </div>
      <h2>Page Not Found</h2>
      <p style={{ color: 'var(--color-text-secondary)', maxWidth: '400px' }}>
        The page or learning session you are looking for does not exist or has been moved.
      </p>
      <div style={{ marginTop: 'var(--space-2)' }}>
        <Button variant="olive" size="md" icon={Home} onClick={() => navigate('/')}>
          Back to Dashboard
        </Button>
      </div>
    </div>
  );
}
