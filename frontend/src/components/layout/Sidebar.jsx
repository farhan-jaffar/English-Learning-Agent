import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PlayCircle,
  Mic,
  TrendingUp,
  Settings,
  Sparkles,
  MessageSquare,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useUiStore } from '../../stores/uiStore';
import { Badge } from '../ui/Badge';
import './Sidebar.css';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/practice', label: 'Practice', icon: PlayCircle },
  { to: '/conversations', label: 'AI Partner', icon: MessageSquare },
  { to: '/recordings', label: 'Recordings', icon: Mic },
  { to: '/progress', label: 'Progress & Stats', icon: TrendingUp },
  { to: '/settings', label: 'Settings', icon: Settings },
];


export function Sidebar() {
  const { user, activeLanguage } = useAuthStore();
  const { sidebarCollapsed } = useUiStore();

  const sessions = activeLanguage?.total_sessions_completed ?? 0;
  const level = activeLanguage?.current_cefr_level || user?.cefr_level || 'B1';

  return (
    <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-brand-badge">F</div>
        <div className="sidebar-brand-info">
          <span className="sidebar-brand-title">FluentFlow</span>
          <span className="sidebar-brand-tag">AI Language Agent</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              title={sidebarCollapsed ? item.label : undefined}
            >
              <span className="sidebar-link-icon">
                <Icon size={20} />
              </span>
              <span className="sidebar-link-text">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-summary-card">
          <div className="sidebar-summary-title">
            <span>Current Level</span>
            <Badge variant="lemon" style={{ fontSize: '11px', padding: '1px 6px' }}>
              {level}
            </Badge>
          </div>
          <p className="sidebar-summary-desc">
            {sessions} session{sessions === 1 ? '' : 's'} recorded in {activeLanguage?.language_name || 'English'}.
          </p>
        </div>
      </div>
    </aside>
  );
}
