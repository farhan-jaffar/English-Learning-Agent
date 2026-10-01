import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../../stores/authStore';

export function PublicOnlyRoute() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return null; // Will be handled by AuthProvider initial loading state
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
