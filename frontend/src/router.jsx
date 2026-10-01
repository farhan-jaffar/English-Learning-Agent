import React from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { AuthLayout } from './features/auth/components/AuthLayout';
import { LoginPage } from './features/auth/pages/LoginPage';
import { RegisterPage } from './features/auth/pages/RegisterPage';
import { ProtectedRoute } from './features/auth/components/ProtectedRoute';
import { PublicOnlyRoute } from './features/auth/components/PublicOnlyRoute';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './features/dashboard/pages/DashboardPage';
import { PracticePage } from './features/exercises/pages/PracticePage';
import { RecordingsPage } from './features/recordings/pages/RecordingsPage';
import { ProgressPage } from './features/dashboard/pages/ProgressPage';
import { SettingsPage } from './features/settings/pages/SettingsPage';
import { ConversationsPage } from './features/conversations/pages/ConversationsPage';
import { ConversationRoomPage } from './features/conversations/pages/ConversationRoomPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const router = createBrowserRouter([
  // Public-only authentication routes (redirect to '/' if already logged in)
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/register', element: <RegisterPage /> },
        ],
      },
    ],
  },

  // Protected application routes
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <DashboardPage /> },
          { path: '/practice', element: <PracticePage /> },
          { path: '/conversations', element: <ConversationsPage /> },
          { path: '/conversations/:sessionId', element: <ConversationRoomPage /> },
          { path: '/recordings', element: <RecordingsPage /> },
          { path: '/progress', element: <ProgressPage /> },
          { path: '/settings', element: <SettingsPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);

